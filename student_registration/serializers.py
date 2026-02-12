"""
Student Registration Serializers
Author: Cascade AI
Date: 2025-12-13
Description: DRF serializers for StudentRegistration model API
"""

from rest_framework import serializers
from .models import StudentRegistration


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentRegistration model
    Handles conversion between model instances and JSON for API responses
    """
    
    class Meta:
        model = StudentRegistration
        fields = [
            'registration_id',
            'student_name',
            'student_email',
            'date_of_birth',
            'grade',
            'school_name',
            'preferred_language',
            'parent_name',
            'parent_email',
            'phone',
            'address',
            'city',
            'state',
            'pincode',
            'status',
            'created_at',
            'updated_at',
            'approved_by',
            'approved_at',
            'rejection_reason',
        ]
        # Make some fields read-only
        read_only_fields = [
            'registration_id',
            'status',
            'created_at',
            'updated_at',
            'approved_by',
            'approved_at',
            'rejection_reason',
        ]


class RegistrationApprovalSerializer(serializers.Serializer):
    """
    Serializer for registration approval action
    Used when admin approves a pending registration
    """
    # No fields needed, just the action
    pass


class RegistrationRejectionSerializer(serializers.Serializer):
    """
    Serializer for registration rejection action
    Requires a reason for rejection
    """
    # Reason field is required when rejecting
    reason = serializers.CharField(
        max_length=1000,
        required=True,
        help_text="Reason for rejecting the registration"
    )
