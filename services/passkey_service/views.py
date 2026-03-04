"""
2026-03-04: Passkey / WebAuthn API views (BS-AUTH-002).

Purpose:
    Six endpoints for WebAuthn credential management:
        POST register/start/         IsAuthenticated
        POST register/complete/      IsAuthenticated
        POST authenticate/start/     AllowAny
        POST authenticate/complete/  AllowAny
        GET  credentials/            IsAuthenticated
        DELETE credentials/{id}/     IsAuthenticated

After successful passkey authentication, JWT tokens are issued using the
same helpers as the OTP/password flow (get_tokens_for_student / parent).
"""

import logging  # 2026-03-04: Module logger

from rest_framework import status  # 2026-03-04: HTTP codes
from rest_framework.permissions import AllowAny, IsAuthenticated  # 2026-03-04: Perms
from rest_framework.response import Response  # 2026-03-04: JSON responses
from rest_framework.views import APIView  # 2026-03-04: CBVs
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-03-04: JWT tokens

from .models import PasskeyCredential  # 2026-03-04: Credential model
from .serializers import (  # 2026-03-04: Request validators
    PasskeyRegisterStartSerializer, PasskeyRegisterCompleteSerializer,
    PasskeyAuthStartSerializer, PasskeyAuthCompleteSerializer,
)
from .services import PasskeyService  # 2026-03-04: Business logic

logger = logging.getLogger(__name__)  # 2026-03-04: Logger


def _issue_tokens(user, role: str) -> dict:
    """
    2026-03-04: Issue JWT access+refresh tokens for any role.

    Reuses the same pattern as MonitorLoginView for monitors and
    get_tokens_for_* helpers for student/parent.

    Args:
        user: Authenticated Django User.
        role: 'student', 'parent', or 'monitor'.

    Returns:
        Dict with 'access', 'refresh', 'role' keys.
    """
    if role == 'student':
        from services.auth_service.jwt_utils import get_tokens_for_student  # 2026-03-04
        try:
            student = user.student_profile  # 2026-03-04: OneToOne
            return get_tokens_for_student(student)
        except Exception:
            pass  # 2026-03-04: Fall through to generic token

    if role == 'parent':
        from services.auth_service.jwt_utils import get_tokens_for_parent  # 2026-03-04
        try:
            parent = user.parent_profile  # 2026-03-04: OneToOne
            return get_tokens_for_parent(parent)
        except Exception:
            pass  # 2026-03-04: Fall through to generic token

    # 2026-03-04: Monitor or unknown — generic token with role claim
    refresh = RefreshToken.for_user(user)
    refresh['role'] = role
    refresh['username'] = user.username
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'role': role,
    }


class PasskeyRegisterStartView(APIView):
    """
    2026-03-04: POST /api/v1/passkeys/register/start/

    Generate WebAuthn registration options for the authenticated user.
    If student_id is provided (parent registering for child), the parent
    must own that student; ensure_student_user() creates the child's
    Django User if absent.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Return registration options + challenge_id."""
        serializer = PasskeyRegisterStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data.get('student_id')
        device_name = serializer.validated_data.get('device_name', 'Passkey')

        if student_id:
            # 2026-03-04: Parent registers passkey on behalf of student
            from services.auth_service.models import Student  # 2026-03-04: Avoid circular
            try:
                student = Student.objects.get(id=student_id, is_active=True)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Student not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            # 2026-03-04: Verify ownership
            try:
                parent = request.user.parent_profile
            except Exception:
                return Response(
                    {'error': 'Only parents can register passkeys for students.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if str(student.parent_id) != str(parent.id):
                return Response(
                    {'error': 'You do not own this student.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            target_user = PasskeyService.ensure_student_user(student)
        else:
            target_user = request.user  # 2026-03-04: Register for self (monitor)

        options, challenge_id = PasskeyService.get_registration_options(
            user=target_user, device_name=device_name
        )
        return Response({'options': options, 'challenge_id': challenge_id})


class PasskeyRegisterCompleteView(APIView):
    """
    2026-03-04: POST /api/v1/passkeys/register/complete/

    Verify the signed registration response from the browser and persist
    the credential.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Verify and save credential."""
        serializer = PasskeyRegisterCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        challenge_id = str(serializer.validated_data['challenge_id'])
        credential_json = serializer.validated_data['credential']
        device_name = serializer.validated_data.get('device_name', 'Passkey')
        student_id = serializer.validated_data.get('student_id')

        if student_id:
            from services.auth_service.models import Student  # 2026-03-04
            try:
                student = Student.objects.get(id=student_id, is_active=True)
                target_user = PasskeyService.ensure_student_user(student)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Student not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            target_user = request.user

        try:
            credential = PasskeyService.complete_registration(
                user=target_user,
                challenge_id=challenge_id,
                credential_json=credential_json,
                device_name=device_name,
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'credential_id': str(credential.id),
            'device_name': credential.device_name,
        }, status=status.HTTP_201_CREATED)


class PasskeyAuthStartView(APIView):
    """
    2026-03-04: POST /api/v1/passkeys/authenticate/start/

    Generate authentication options.  Accepts optional student_id to
    limit allowCredentials to that student's registered passkeys.
    """

    permission_classes = [AllowAny]  # 2026-03-04: Public — login endpoint

    def post(self, request):
        """2026-03-04: Return authentication options + challenge_id."""
        serializer = PasskeyAuthStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data.get('student_id')
        user_credential_ids = None

        if student_id:
            # 2026-03-04: Collect student's registered credential IDs
            from services.auth_service.models import Student  # 2026-03-04
            try:
                student = Student.objects.get(id=student_id, is_active=True)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Student not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if student.user_id:
                user_credential_ids = list(
                    PasskeyCredential.objects.filter(user_id=student.user_id)
                    .values_list('credential_id', flat=True)
                )

        options, challenge_id = PasskeyService.get_authentication_options(
            user_credential_ids=user_credential_ids
        )
        return Response({'options': options, 'challenge_id': challenge_id})


class PasskeyAuthCompleteView(APIView):
    """
    2026-03-04: POST /api/v1/passkeys/authenticate/complete/

    Verify the signed assertion, update the sign count, and issue JWT tokens.
    """

    permission_classes = [AllowAny]  # 2026-03-04: Public — login endpoint

    def post(self, request):
        """2026-03-04: Verify assertion and return JWT tokens."""
        serializer = PasskeyAuthCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        challenge_id = str(serializer.validated_data['challenge_id'])
        credential_json = serializer.validated_data['credential']

        try:
            user, role = PasskeyService.complete_authentication(
                challenge_id=challenge_id,
                credential_json=credential_json,
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        tokens = _issue_tokens(user, role)
        return Response(tokens, status=status.HTTP_200_OK)


class PasskeyCredentialListView(APIView):
    """
    2026-03-04: GET /api/v1/passkeys/credentials/

    List all passkey credentials registered by the authenticated user.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def get(self, request):
        """2026-03-04: Return list of user's passkeys."""
        credentials = PasskeyCredential.objects.filter(user=request.user)
        data = [
            {
                'id': str(c.id),
                'device_name': c.device_name,
                'created_at': c.created_at.isoformat(),
                'last_used_at': c.last_used_at.isoformat() if c.last_used_at else None,
                'transports': c.transports,
            }
            for c in credentials
        ]
        return Response(data)


class PasskeyCredentialDeleteView(APIView):
    """
    2026-03-04: DELETE /api/v1/passkeys/credentials/{id}/

    Remove a registered passkey credential for the authenticated user.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def delete(self, request, pk):
        """2026-03-04: Delete a credential by its UUID pk."""
        try:
            credential = PasskeyCredential.objects.get(id=pk, user=request.user)
        except PasskeyCredential.DoesNotExist:
            return Response(
                {'error': 'Credential not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        credential.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
