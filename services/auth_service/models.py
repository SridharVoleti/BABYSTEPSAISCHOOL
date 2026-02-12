"""
2026-02-12: Authentication service models.

Purpose:
    Define database models for the authentication module (BS-AUT).
    Covers parent accounts, student profiles, OTP tracking,
    DPDP consent records, and security audit logging.
"""

import uuid  # 2026-02-12: UUID for primary keys
from datetime import date  # 2026-02-12: Date calculations

from django.conf import settings  # 2026-02-12: Access Django settings
from django.db import models  # 2026-02-12: Django ORM


class Parent(models.Model):
    """
    2026-02-12: Parent account linked to a Django User.

    Represents the primary account holder who registers via WhatsApp OTP.
    One parent can have multiple student (child) profiles.
    """

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.OneToOneField(  # 2026-02-12: Link to Django auth user
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile',
    )
    phone = models.CharField(  # 2026-02-12: Phone number (unique identifier)
        max_length=15, unique=True, db_index=True
    )
    full_name = models.CharField(max_length=150)  # 2026-02-12: Parent full name
    email = models.EmailField(blank=True, default='')  # 2026-02-12: Optional email
    state = models.CharField(  # 2026-02-12: Indian state for language suggestions
        max_length=50, blank=True, default=''
    )
    preferred_language = models.CharField(  # 2026-02-12: UI language preference
        max_length=20, default='en'
    )
    is_phone_verified = models.BooleanField(default=False)  # 2026-02-12: OTP verified
    is_profile_complete = models.BooleanField(default=False)  # 2026-02-12: Registration done
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-12: Last update timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-created_at']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"{self.full_name} ({self.phone})"


class Student(models.Model):
    """
    2026-02-12: Student (child) profile under a parent account.

    Age-based login methods per FSD:
    - Ages 3-6: Picture sequence login
    - Ages 6-12: 4-digit PIN login
    - Ages 12+: Password login (uses Django user password)
    """

    AGE_GROUP_CHOICES = [  # 2026-02-12: Age group categories
        ('3-6', 'Early Childhood (3-6)'),
        ('6-12', 'Middle Childhood (6-12)'),
        ('12+', 'Adolescent (12+)'),
    ]

    LOGIN_METHOD_CHOICES = [  # 2026-02-12: Login method per age group
        ('picture', 'Picture Sequence'),
        ('pin', 'PIN Code'),
        ('password', 'Password'),
    ]

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    parent = models.ForeignKey(  # 2026-02-12: Link to parent
        Parent, on_delete=models.CASCADE, related_name='students'
    )
    user = models.OneToOneField(  # 2026-02-12: Django user for JWT compatibility
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=150)  # 2026-02-12: Student name
    dob = models.DateField()  # 2026-02-12: Date of birth
    age_group = models.CharField(  # 2026-02-12: Computed from DOB
        max_length=5, choices=AGE_GROUP_CHOICES
    )
    grade = models.IntegerField()  # 2026-02-12: Class/grade (1-12)
    login_method = models.CharField(  # 2026-02-12: Determined by age group
        max_length=10, choices=LOGIN_METHOD_CHOICES
    )
    avatar_id = models.CharField(  # 2026-02-12: Selected avatar identifier
        max_length=50, default='avatar_01'
    )
    picture_sequence_hash = models.CharField(  # 2026-02-12: bcrypt hash of picture IDs
        max_length=128, blank=True, default=''
    )
    pin_hash = models.CharField(  # 2026-02-12: bcrypt hash of 4-digit PIN
        max_length=128, blank=True, default=''
    )
    language_1 = models.CharField(  # 2026-02-12: Primary language
        max_length=30, default='English'
    )
    language_2 = models.CharField(  # 2026-02-12: Second language
        max_length=30, blank=True, default=''
    )
    language_3 = models.CharField(  # 2026-02-12: Third language
        max_length=30, blank=True, default=''
    )
    is_active = models.BooleanField(default=True)  # 2026-02-12: Active status
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-12: Last update timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-created_at']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"{self.full_name} (Grade {self.grade})"

    @staticmethod
    def compute_age_group(dob):
        """
        2026-02-12: Compute age group from date of birth.

        Args:
            dob: Date of birth.

        Returns:
            str: Age group string ('3-6', '6-12', or '12+').
        """
        today = date.today()  # 2026-02-12: Current date
        age = today.year - dob.year - (  # 2026-02-12: Calculate age
            (today.month, today.day) < (dob.month, dob.day)
        )
        if age < 6:  # 2026-02-12: Early childhood
            return '3-6'
        elif age < 12:  # 2026-02-12: Middle childhood
            return '6-12'
        return '12+'  # 2026-02-12: Adolescent

    @staticmethod
    def get_login_method_for_age_group(age_group):
        """
        2026-02-12: Determine login method based on age group.

        Args:
            age_group: Age group string.

        Returns:
            str: Login method ('picture', 'pin', or 'password').
        """
        method_map = {  # 2026-02-12: FSD-defined mapping
            '3-6': 'picture',
            '6-12': 'pin',
            '12+': 'password',
        }
        return method_map.get(age_group, 'pin')  # 2026-02-12: Default to PIN


class OTPRequest(models.Model):
    """
    2026-02-12: OTP lifecycle tracking model.

    Tracks OTP generation, delivery, and verification for phone-based auth.
    Enforces cooldown, expiry, and max attempt limits.
    """

    PURPOSE_CHOICES = [  # 2026-02-12: OTP purpose types
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('reset', 'Password Reset'),
    ]

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    phone = models.CharField(max_length=15, db_index=True)  # 2026-02-12: Target phone
    otp_hash = models.CharField(max_length=128)  # 2026-02-12: bcrypt hash of OTP
    purpose = models.CharField(  # 2026-02-12: Why OTP was sent
        max_length=20, choices=PURPOSE_CHOICES, default='registration'
    )
    attempts = models.IntegerField(default=0)  # 2026-02-12: Verification attempts
    is_verified = models.BooleanField(default=False)  # 2026-02-12: Successfully verified
    expires_at = models.DateTimeField()  # 2026-02-12: OTP expiry time
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-created_at']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"OTP for {self.phone} ({self.purpose})"


class ConsentRecord(models.Model):
    """
    2026-02-12: DPDP consent log (append-only).

    Records consent grant/withdraw actions for legal compliance.
    Never updated or deleted - append-only audit trail.
    """

    ACTION_CHOICES = [  # 2026-02-12: Consent actions
        ('grant', 'Grant'),
        ('withdraw', 'Withdraw'),
    ]

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    parent = models.ForeignKey(  # 2026-02-12: Link to parent
        Parent, on_delete=models.CASCADE, related_name='consent_records'
    )
    consent_version = models.CharField(max_length=20)  # 2026-02-12: Consent doc version
    action = models.CharField(  # 2026-02-12: Grant or withdraw
        max_length=10, choices=ACTION_CHOICES
    )
    scroll_percentage = models.IntegerField(default=0)  # 2026-02-12: How far user scrolled
    ip_address = models.GenericIPAddressField(  # 2026-02-12: Client IP
        null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)  # 2026-02-12: When action occurred

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-timestamp']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"Consent {self.action} by {self.parent} v{self.consent_version}"


class AuditLog(models.Model):
    """
    2026-02-12: Security audit trail.

    Logs authentication events for security monitoring.
    """

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(  # 2026-02-12: Related user (nullable for failed attempts)
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=50)  # 2026-02-12: Action performed
    resource_type = models.CharField(  # 2026-02-12: What was accessed
        max_length=50, blank=True, default=''
    )
    ip_address = models.GenericIPAddressField(  # 2026-02-12: Client IP
        null=True, blank=True
    )
    metadata = models.JSONField(  # 2026-02-12: Additional context
        default=dict, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)  # 2026-02-12: When it happened

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-timestamp']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"{self.action} at {self.timestamp}"
