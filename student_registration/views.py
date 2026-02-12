"""
Student Registration Views
Author: Cascade AI
Date: 2025-12-13
Description: API views for student registration and admin approval workflow
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import StudentRegistration
from .serializers import (
    StudentRegistrationSerializer,
    RegistrationApprovalSerializer,
    RegistrationRejectionSerializer
)


class StudentRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentRegistration CRUD operations and approval workflow
    
    List/Retrieve: Requires admin authentication
    Create: Public endpoint for student registration
    Approve/Reject: Admin-only actions
    """
    
    queryset = StudentRegistration.objects.all()
    serializer_class = StudentRegistrationSerializer
    lookup_field = 'registration_id'
    pagination_class = None  # Disable pagination for this viewset
    
    def get_permissions(self):
        """
        Set permissions based on action
        - create: Allow any (public registration)
        - list/retrieve/approve/reject: Require authentication (admin only)
        """
        if self.action == 'create':
            # Public endpoint - anyone can register
            return [AllowAny()]
        else:
            # Admin authentication required for all other actions
            return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters
        Supports filtering by status (pending, approved, rejected)
        """
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new student registration
        Public endpoint - no authentication required
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, registration_id=None):
        """
        Approve a pending registration
        Admin-only action
        """
        # Get the registration instance
        registration = self.get_object()
        
        # Check if already approved or rejected
        if registration.status != 'pending':
            return Response(
                {'error': f'Cannot approve registration with status: {registration.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update registration status
        registration.status = 'approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        # Return updated registration data
        serializer = self.get_serializer(registration)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, registration_id=None):
        """
        Reject a pending registration with a reason
        Admin-only action
        """
        # Get the registration instance
        registration = self.get_object()
        
        # Validate rejection data
        rejection_serializer = RegistrationRejectionSerializer(data=request.data)
        rejection_serializer.is_valid(raise_exception=True)
        
        # Check if already approved or rejected
        if registration.status != 'pending':
            return Response(
                {'error': f'Cannot reject registration with status: {registration.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update registration status
        registration.status = 'rejected'
        registration.rejection_reason = rejection_serializer.validated_data['reason']
        registration.save()
        
        # Return updated registration data
        serializer = self.get_serializer(registration)
        return Response(serializer.data, status=status.HTTP_200_OK)
