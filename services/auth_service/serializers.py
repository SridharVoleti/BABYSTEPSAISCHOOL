"""
2026-02-12: Authentication service serializers.

Purpose:
    DRF serializers for auth API request/response validation.
"""

from rest_framework import serializers  # 2026-02-12: DRF serializers
from .models import Parent, Student, ConsentRecord  # 2026-02-12: Models


class SendOTPSerializer(serializers.Serializer):
    """2026-02-12: Serializer for OTP send request."""

    phone = serializers.CharField(  # 2026-02-12: Phone number
        max_length=15,
        help_text='Phone number with country code (e.g., +91XXXXXXXXXX)',
    )
    purpose = serializers.ChoiceField(  # 2026-02-12: OTP purpose
        choices=['registration', 'login', 'reset'],
        default='registration',
    )

    def validate_phone(self, value):
        """2026-02-12: Validate phone number format."""
        cleaned = value.strip().replace(' ', '').replace('-', '')  # 2026-02-12: Clean
        if not cleaned.startswith('+'):  # 2026-02-12: Must have country code
            raise serializers.ValidationError(
                'Phone number must include country code (e.g., +91XXXXXXXXXX).'
            )
        if len(cleaned) < 10 or len(cleaned) > 15:  # 2026-02-12: Length check
            raise serializers.ValidationError(
                'Phone number must be between 10 and 15 digits.'
            )
        return cleaned  # 2026-02-12: Return cleaned value


class VerifyOTPSerializer(serializers.Serializer):
    """2026-02-12: Serializer for OTP verification request."""

    phone = serializers.CharField(max_length=15)  # 2026-02-12: Phone number
    otp_code = serializers.CharField(  # 2026-02-12: OTP code
        max_length=6, min_length=6
    )


class CompleteRegistrationSerializer(serializers.Serializer):
    """2026-02-12: Serializer for registration completion."""

    phone = serializers.CharField(max_length=15)  # 2026-02-12: Verified phone
    full_name = serializers.CharField(max_length=150)  # 2026-02-12: Parent name
    password = serializers.CharField(  # 2026-02-17: Parent account password
        min_length=6, max_length=128
    )
    email = serializers.EmailField(required=False, default='')  # 2026-02-12: Optional
    state = serializers.CharField(  # 2026-02-12: Indian state
        max_length=50, required=False, default=''
    )
    preferred_language = serializers.CharField(  # 2026-02-12: UI language
        max_length=20, required=False, default='en'
    )


class StudentCreateSerializer(serializers.Serializer):
    """2026-02-12: Serializer for student profile creation."""

    full_name = serializers.CharField(max_length=150)  # 2026-02-12: Student name
    dob = serializers.DateField()  # 2026-02-12: Date of birth
    grade = serializers.IntegerField(min_value=1, max_value=12)  # 2026-02-12: Class
    avatar_id = serializers.CharField(  # 2026-02-12: Avatar
        max_length=50, required=False, default='avatar_01'
    )
    pin = serializers.CharField(  # 2026-02-12: 4-digit PIN (ages 6-12)
        max_length=4, min_length=4, required=False
    )
    picture_sequence = serializers.ListField(  # 2026-02-12: Picture IDs (ages 3-6)
        child=serializers.CharField(max_length=50),
        min_length=3,
        max_length=3,
        required=False,
    )
    password = serializers.CharField(  # 2026-02-12: Password (ages 12+)
        max_length=128, required=False
    )
    language_1 = serializers.CharField(  # 2026-02-12: Primary language
        max_length=30, required=False, default='English'
    )
    language_2 = serializers.CharField(  # 2026-02-12: Second language
        max_length=30, required=False, default=''
    )
    language_3 = serializers.CharField(  # 2026-02-12: Third language
        max_length=30, required=False, default=''
    )


class ParentSerializer(serializers.ModelSerializer):
    """2026-02-12: Serializer for parent profile response."""

    class Meta:
        """2026-02-12: Meta options."""

        model = Parent  # 2026-02-12: Parent model
        fields = [  # 2026-02-12: Exposed fields
            'id', 'phone', 'full_name', 'email', 'state',
            'preferred_language', 'is_phone_verified', 'is_profile_complete',
            'created_at',
        ]
        read_only_fields = fields  # 2026-02-12: All read-only


class StudentSerializer(serializers.ModelSerializer):
    """2026-02-12: Serializer for student profile response."""

    class Meta:
        """2026-02-12: Meta options."""

        model = Student  # 2026-02-12: Student model
        fields = [  # 2026-02-12: Exposed fields
            'id', 'full_name', 'dob', 'age_group', 'grade',
            'login_method', 'avatar_id', 'language_1', 'language_2',
            'language_3', 'is_active', 'created_at',
        ]
        read_only_fields = fields  # 2026-02-12: All read-only


class PictureLoginSerializer(serializers.Serializer):
    """2026-02-12: Serializer for picture sequence login."""

    student_id = serializers.UUIDField()  # 2026-02-12: Student UUID
    picture_sequence = serializers.ListField(  # 2026-02-12: Ordered picture IDs
        child=serializers.CharField(max_length=50),
        min_length=3,
        max_length=3,
    )


class PINLoginSerializer(serializers.Serializer):
    """2026-02-12: Serializer for PIN login."""

    student_id = serializers.UUIDField()  # 2026-02-12: Student UUID
    pin = serializers.CharField(max_length=4, min_length=4)  # 2026-02-12: 4-digit PIN


class ParentUpdateSerializer(serializers.Serializer):
    """2026-02-13: Serializer for parent profile update."""

    full_name = serializers.CharField(  # 2026-02-13: Parent name
        max_length=150, required=False
    )
    email = serializers.EmailField(  # 2026-02-13: Optional email
        required=False, allow_blank=True
    )
    state = serializers.CharField(  # 2026-02-13: Indian state
        max_length=50, required=False, allow_blank=True
    )
    preferred_language = serializers.CharField(  # 2026-02-13: UI language
        max_length=20, required=False
    )


class StudentUpdateSerializer(serializers.Serializer):
    """2026-02-13: Serializer for student profile update (by parent)."""

    full_name = serializers.CharField(  # 2026-02-13: Student name
        max_length=150, required=False
    )
    grade = serializers.IntegerField(  # 2026-02-13: Class/grade
        min_value=1, max_value=12, required=False
    )
    avatar_id = serializers.CharField(  # 2026-02-13: Avatar
        max_length=50, required=False
    )
    language_1 = serializers.CharField(  # 2026-02-13: Primary language
        max_length=30, required=False
    )
    language_2 = serializers.CharField(  # 2026-02-13: Second language
        max_length=30, required=False, allow_blank=True
    )
    language_3 = serializers.CharField(  # 2026-02-13: Third language
        max_length=30, required=False, allow_blank=True
    )


class ResetCredentialSerializer(serializers.Serializer):
    """2026-02-13: Serializer for student credential reset by parent."""

    student_id = serializers.UUIDField()  # 2026-02-13: Student UUID
    pin = serializers.CharField(  # 2026-02-13: New 4-digit PIN
        max_length=4, min_length=4, required=False
    )
    picture_sequence = serializers.ListField(  # 2026-02-13: New picture sequence
        child=serializers.CharField(max_length=50),
        min_length=3, max_length=3, required=False,
    )
    password = serializers.CharField(  # 2026-02-13: New password
        max_length=128, min_length=6, required=False
    )

    def validate(self, data):
        """2026-02-13: Ensure exactly one credential is provided."""
        creds = [k for k in ('pin', 'picture_sequence', 'password') if k in data]
        if len(creds) != 1:
            raise serializers.ValidationError(
                'Provide exactly one credential: pin, picture_sequence, or password.'
            )
        return data


class PasswordLoginSerializer(serializers.Serializer):
    """2026-02-13: Serializer for password login (ages 12+)."""

    student_id = serializers.UUIDField()  # 2026-02-13: Student UUID
    password = serializers.CharField(max_length=128)  # 2026-02-13: Password string


class ConsentGrantSerializer(serializers.Serializer):
    """2026-02-12: Serializer for consent grant/withdraw."""

    consent_version = serializers.CharField(max_length=20)  # 2026-02-12: Doc version
    action = serializers.ChoiceField(  # 2026-02-12: Grant or withdraw
        choices=['grant', 'withdraw']
    )
    scroll_percentage = serializers.IntegerField(  # 2026-02-12: Scroll tracking
        min_value=0, max_value=100, required=False, default=0
    )


class ParentPasswordLoginSerializer(serializers.Serializer):
    """2026-02-17: Serializer for parent phone + password login."""

    phone = serializers.CharField(max_length=15)  # 2026-02-17: Phone number
    password = serializers.CharField(max_length=128)  # 2026-02-17: Account password

    def validate_phone(self, value):
        """2026-02-17: Validate phone number format."""
        cleaned = value.strip().replace(' ', '').replace('-', '')  # 2026-02-17: Clean
        if not cleaned.startswith('+'):  # 2026-02-17: Must have country code
            raise serializers.ValidationError(
                'Phone number must include country code (e.g., +91XXXXXXXXXX).'
            )
        return cleaned  # 2026-02-17: Return cleaned value


class ForgotPasswordSerializer(serializers.Serializer):
    """2026-02-17: Serializer for parent forgot-password (set new password after OTP)."""

    phone = serializers.CharField(max_length=15)  # 2026-02-17: Phone number
    new_password = serializers.CharField(  # 2026-02-17: New password
        min_length=6, max_length=128
    )

    def validate_phone(self, value):
        """2026-02-17: Validate phone number format."""
        cleaned = value.strip().replace(' ', '').replace('-', '')  # 2026-02-17: Clean
        if not cleaned.startswith('+'):  # 2026-02-17: Must have country code
            raise serializers.ValidationError(
                'Phone number must include country code (e.g., +91XXXXXXXXXX).'
            )
        return cleaned  # 2026-02-17: Return cleaned value


class LanguageSelectionSerializer(serializers.Serializer):
    """2026-02-12: Serializer for language selection."""

    language_1 = serializers.CharField(max_length=30)  # 2026-02-12: Primary
    language_2 = serializers.CharField(  # 2026-02-12: Second
        max_length=30, required=False, default=''
    )
    language_3 = serializers.CharField(  # 2026-02-12: Third
        max_length=30, required=False, default=''
    )
