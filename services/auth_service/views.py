"""
2026-02-12: Authentication service views.

Purpose:
    DRF viewsets for auth endpoints: OTP flow, registration,
    student login, consent, and language selection.
"""

import random  # 2026-02-12: For picture grid randomization

from rest_framework import status, viewsets  # 2026-02-12: DRF
from rest_framework.decorators import action  # 2026-02-12: Custom actions
from rest_framework.permissions import AllowAny  # 2026-02-12: Public access
from rest_framework.response import Response  # 2026-02-12: API responses
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-12: Token refresh
from rest_framework_simplejwt.exceptions import TokenError  # 2026-02-12: Token errors

from .models import Student  # 2026-02-12: Models
from .permissions import IsParent, IsParentOfStudent  # 2026-02-12: Custom perms
from .serializers import (  # 2026-02-12: Serializers
    SendOTPSerializer, VerifyOTPSerializer, CompleteRegistrationSerializer,
    StudentCreateSerializer, StudentSerializer, PictureLoginSerializer,
    PINLoginSerializer, ConsentGrantSerializer, LanguageSelectionSerializer,
)
from .services import AuthService  # 2026-02-12: Business logic
from .language_data import (  # 2026-02-12: Language data
    STATE_LANGUAGE_MAP, DEFAULT_LANGUAGES, AVAILABLE_LANGUAGES,
)


# 2026-02-12: Available picture IDs for picture login grid
PICTURE_IDS = [
    'cat', 'dog', 'fish', 'bird', 'tree', 'sun',
    'moon', 'star', 'flower', 'house', 'car', 'ball',
]


class AuthViewSet(viewsets.ViewSet):
    """
    2026-02-12: Authentication viewset for OTP-based parent auth.

    Endpoints:
        POST /send-otp/ - Send OTP to phone
        POST /verify-otp/ - Verify OTP code
        POST /complete-registration/ - Complete parent registration
        POST /login/ - Parent login via OTP
        POST /refresh/ - Refresh JWT token
    """

    permission_classes = [AllowAny]  # 2026-02-12: Public endpoints

    @action(detail=False, methods=['post'], url_path='send-otp')
    def send_otp(self, request):
        """2026-02-12: Send OTP to phone number."""
        serializer = SendOTPSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        result = AuthService.send_otp(  # 2026-02-12: Business logic
            phone=serializer.validated_data['phone'],
            purpose=serializer.validated_data['purpose'],
        )

        if result['success']:  # 2026-02-12: Success response
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_429_TOO_MANY_REQUESTS)

    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        """2026-02-12: Verify OTP code."""
        serializer = VerifyOTPSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        result = AuthService.verify_otp(  # 2026-02-12: Business logic
            phone=serializer.validated_data['phone'],
            otp_code=serializer.validated_data['otp_code'],
        )

        if result['success']:  # 2026-02-12: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='complete-registration')
    def complete_registration(self, request):
        """2026-02-12: Complete parent registration after OTP verification."""
        serializer = CompleteRegistrationSerializer(  # 2026-02-12: Validate
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        result = AuthService.complete_registration(  # 2026-02-12: Business logic
            **serializer.validated_data
        )

        if result['success']:  # 2026-02-12: Success with tokens
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """2026-02-12: Parent login via OTP."""
        serializer = VerifyOTPSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        # 2026-02-12: Verify OTP first
        verify_result = AuthService.verify_otp(
            phone=serializer.validated_data['phone'],
            otp_code=serializer.validated_data['otp_code'],
        )
        if not verify_result['success']:
            return Response(verify_result, status=status.HTTP_400_BAD_REQUEST)

        # 2026-02-12: Then login
        result = AuthService.parent_login(
            phone=serializer.validated_data['phone'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_token(self, request):
        """2026-02-12: Refresh JWT access token."""
        refresh_token = request.data.get('refresh')  # 2026-02-12: Get refresh token
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)  # 2026-02-12: Validate token
            return Response({  # 2026-02-12: New access token
                'access': str(token.access_token),
                'refresh': str(token),
            })
        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class StudentAuthViewSet(viewsets.ViewSet):
    """
    2026-02-12: Student authentication viewset.

    Endpoints:
        POST /picture-login/ - Login with picture sequence
        POST /pin-login/ - Login with 4-digit PIN
        GET /picture-grid/{student_id}/ - Get randomized picture grid
    """

    permission_classes = [AllowAny]  # 2026-02-12: Public (student login)

    @action(detail=False, methods=['post'], url_path='picture-login')
    def picture_login(self, request):
        """2026-02-12: Login student with picture sequence."""
        serializer = PictureLoginSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        result = AuthService.student_picture_login(  # 2026-02-12: Business logic
            student_id=serializer.validated_data['student_id'],
            picture_sequence=serializer.validated_data['picture_sequence'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='pin-login')
    def pin_login(self, request):
        """2026-02-12: Login student with PIN."""
        serializer = PINLoginSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        result = AuthService.student_pin_login(  # 2026-02-12: Business logic
            student_id=serializer.validated_data['student_id'],
            pin=serializer.validated_data['pin'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'picture-grid/(?P<student_id>[^/.]+)')
    def picture_grid(self, request, student_id=None):
        """2026-02-12: Get randomized picture grid for student login."""
        try:
            student = Student.objects.get(  # 2026-02-12: Find student
                id=student_id, login_method='picture', is_active=True
            )
        except (Student.DoesNotExist, ValueError):
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-02-12: Return shuffled picture grid
        shuffled = list(PICTURE_IDS)
        random.shuffle(shuffled)
        return Response({
            'student_id': str(student.id),
            'student_name': student.full_name,
            'avatar_id': student.avatar_id,
            'pictures': shuffled,
        })


class StudentProfileViewSet(viewsets.ViewSet):
    """
    2026-02-12: Student profile CRUD for parents.

    Endpoints:
        GET / - List parent's students
        POST / - Create student profile
        GET /{id}/ - Get student detail
    """

    permission_classes = [IsParent]  # 2026-02-12: Parent only

    def list(self, request):
        """2026-02-12: List all students under this parent."""
        parent = request.user.parent_profile  # 2026-02-12: Get parent
        students = parent.students.filter(is_active=True)  # 2026-02-12: Active only
        serializer = StudentSerializer(students, many=True)  # 2026-02-12: Serialize
        return Response(serializer.data)

    def create(self, request):
        """2026-02-12: Create a new student profile."""
        serializer = StudentCreateSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        parent = request.user.parent_profile  # 2026-02-12: Get parent
        result = AuthService.create_student(  # 2026-02-12: Business logic
            parent=parent,
            **serializer.validated_data,
        )

        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """2026-02-12: Get a single student profile."""
        try:
            student = Student.objects.get(  # 2026-02-12: Find student
                id=pk, is_active=True
            )
        except (Student.DoesNotExist, ValueError):
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-02-12: Check ownership
        if student.parent_id != request.user.parent_profile.id:
            return Response(
                {'error': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentSerializer(student)
        return Response(serializer.data)


class ConsentViewSet(viewsets.ViewSet):
    """
    2026-02-12: Consent management viewset.

    Endpoints:
        GET /notice/ - Get consent notice text
        POST /grant/ - Record consent grant
        POST /withdraw/ - Record consent withdrawal
    """

    @action(detail=False, methods=['get'], url_path='notice',
            permission_classes=[AllowAny])
    def notice(self, request):
        """2026-02-12: Get DPDP consent notice."""
        return Response({  # 2026-02-12: Consent text
            'version': '1.0',
            'title': 'Data Protection & Privacy Notice',
            'content': (
                'BabySteps Digital School collects and processes the following '
                'personal data of your child for educational purposes:\n\n'
                '1. Name, date of birth, and grade level\n'
                '2. Learning progress, assessment scores, and activity data\n'
                '3. Language preferences\n\n'
                'This data is processed under the Digital Personal Data Protection '
                'Act, 2023 (DPDP Act) with your explicit consent. Data is stored '
                'securely and not shared with third parties.\n\n'
                'You may withdraw consent at any time, which will result in '
                'deletion of your child\'s data within 30 days.'
            ),
            'checkboxes': [
                'I have read and understood the privacy notice',
                'I consent to the collection and processing of my child\'s data',
                'I understand I can withdraw consent at any time',
            ],
        })

    @action(detail=False, methods=['post'], url_path='grant',
            permission_classes=[IsParent])
    def grant(self, request):
        """2026-02-12: Record consent grant."""
        serializer = ConsentGrantSerializer(data={  # 2026-02-12: Force action
            **request.data,
            'action': 'grant',
        })
        serializer.is_valid(raise_exception=True)

        parent = request.user.parent_profile  # 2026-02-12: Get parent
        ip = request.META.get('REMOTE_ADDR')  # 2026-02-12: Client IP

        result = AuthService.record_consent(  # 2026-02-12: Business logic
            parent=parent,
            consent_version=serializer.validated_data['consent_version'],
            action='grant',
            scroll_percentage=serializer.validated_data.get('scroll_percentage', 0),
            ip_address=ip,
        )

        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='withdraw',
            permission_classes=[IsParent])
    def withdraw(self, request):
        """2026-02-12: Record consent withdrawal."""
        serializer = ConsentGrantSerializer(data={  # 2026-02-12: Force action
            **request.data,
            'action': 'withdraw',
        })
        serializer.is_valid(raise_exception=True)

        parent = request.user.parent_profile  # 2026-02-12: Get parent
        ip = request.META.get('REMOTE_ADDR')  # 2026-02-12: Client IP

        result = AuthService.record_consent(  # 2026-02-12: Business logic
            parent=parent,
            consent_version=serializer.validated_data['consent_version'],
            action='withdraw',
            scroll_percentage=serializer.validated_data.get('scroll_percentage', 0),
            ip_address=ip,
        )

        return Response(result, status=status.HTTP_201_CREATED)


class LanguageViewSet(viewsets.ViewSet):
    """
    2026-02-12: Language selection viewset.

    Endpoints:
        GET /suggestions/?state=XYZ - Get language suggestions for state
        GET /available/ - Get all available languages
    """

    permission_classes = [AllowAny]  # 2026-02-12: Public for registration flow

    @action(detail=False, methods=['get'], url_path='suggestions')
    def suggestions(self, request):
        """2026-02-12: Get language suggestions based on state."""
        state = request.query_params.get('state', '')  # 2026-02-12: Get state param
        suggestions = STATE_LANGUAGE_MAP.get(  # 2026-02-12: Lookup
            state, DEFAULT_LANGUAGES
        )
        return Response({
            'state': state,
            'suggestions': suggestions,
        })

    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        """2026-02-12: Get all available languages."""
        return Response({
            'languages': AVAILABLE_LANGUAGES,
        })
