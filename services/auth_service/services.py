"""
2026-02-12: Authentication business logic service.

Purpose:
    Core authentication operations: OTP send/verify, registration,
    parent login, student creation, and student login methods.
"""

import hashlib  # 2026-02-12: For picture sequence hashing
import logging  # 2026-02-12: Logging
import random  # 2026-02-12: OTP generation
import string  # 2026-02-12: Character sets

import bcrypt  # 2026-02-12: Password hashing
from django.conf import settings  # 2026-02-12: Settings access
from django.contrib.auth import get_user_model  # 2026-02-12: User model
from django.utils import timezone  # 2026-02-12: Timezone-aware datetimes
from datetime import timedelta  # 2026-02-12: Time calculations

from .models import Parent, Student, OTPRequest, ConsentRecord, AuditLog  # 2026-02-12: Models
from .otp_providers.factory import OTPFactory  # 2026-02-12: OTP provider
from .jwt_utils import get_tokens_for_parent, get_tokens_for_student  # 2026-02-12: JWT

User = get_user_model()  # 2026-02-12: Django User model
logger = logging.getLogger(__name__)  # 2026-02-12: Module logger


class AuthService:
    """2026-02-12: Core authentication service with all auth business logic."""

    @staticmethod
    def _get_otp_config():
        """2026-02-12: Get OTP configuration from settings."""
        return getattr(settings, 'OTP_CONFIG', {  # 2026-02-12: Defaults
            'otp_length': 6,
            'otp_expiry_minutes': 10,
            'max_attempts': 3,
            'cooldown_seconds': 60,
        })

    @staticmethod
    def _generate_otp(length=6):
        """
        2026-02-12: Generate a random numeric OTP.

        Args:
            length: Number of digits.

        Returns:
            str: OTP code.
        """
        return ''.join(  # 2026-02-12: Random digits
            random.choices(string.digits, k=length)
        )

    @staticmethod
    def _hash_value(value):
        """
        2026-02-12: Hash a value using bcrypt.

        Args:
            value: String to hash.

        Returns:
            str: bcrypt hash string.
        """
        return bcrypt.hashpw(  # 2026-02-12: bcrypt hash
            value.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def _verify_hash(value, hashed):
        """
        2026-02-12: Verify a value against a bcrypt hash.

        Args:
            value: Plain text value.
            hashed: bcrypt hash to check against.

        Returns:
            bool: True if value matches hash.
        """
        return bcrypt.checkpw(  # 2026-02-12: bcrypt verify
            value.encode('utf-8'), hashed.encode('utf-8')
        )

    @classmethod
    def send_otp(cls, phone, purpose='registration'):
        """
        2026-02-12: Generate and send OTP to phone number.

        Args:
            phone: Phone number string.
            purpose: OTP purpose ('registration', 'login').

        Returns:
            dict: Result with success status and message.
        """
        config = cls._get_otp_config()  # 2026-02-12: Get config

        # 2026-02-12: Check cooldown - find most recent OTP for this phone
        cooldown_cutoff = timezone.now() - timedelta(
            seconds=config.get('cooldown_seconds', 60)
        )
        recent_otp = OTPRequest.objects.filter(
            phone=phone,
            created_at__gte=cooldown_cutoff,
        ).first()

        if recent_otp:  # 2026-02-12: Cooldown active
            return {
                'success': False,
                'error': 'Please wait before requesting another OTP.',
                'code': 'COOLDOWN_ACTIVE',
            }

        # 2026-02-12: Generate and hash OTP
        otp_code = cls._generate_otp(config.get('otp_length', 6))
        otp_hash = cls._hash_value(otp_code)
        expires_at = timezone.now() + timedelta(
            minutes=config.get('otp_expiry_minutes', 10)
        )

        # 2026-02-12: Store OTP request
        OTPRequest.objects.create(
            phone=phone,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=expires_at,
        )

        # 2026-02-12: Send via provider
        provider = OTPFactory.get_provider()
        provider.send_otp(phone, otp_code)

        logger.info(f"OTP sent to {phone} for {purpose}")  # 2026-02-12: Log

        result = {  # 2026-02-12: Success response
            'success': True,
            'message': 'OTP sent successfully.',
            'expires_in_minutes': config.get('otp_expiry_minutes', 10),
        }

        # 2026-02-12: Include OTP in response for mock provider (dev only)
        from django.conf import settings as django_settings
        if getattr(django_settings, 'OTP_PROVIDER', 'mock') == 'mock':
            result['debug_otp'] = otp_code

        return result

    @classmethod
    def verify_otp(cls, phone, otp_code):
        """
        2026-02-12: Verify OTP code for a phone number.

        Args:
            phone: Phone number string.
            otp_code: OTP code to verify.

        Returns:
            dict: Result with success status.
        """
        config = cls._get_otp_config()  # 2026-02-12: Get config
        max_attempts = config.get('max_attempts', 3)  # 2026-02-12: Attempt limit

        # 2026-02-12: Find latest unverified, unexpired OTP
        otp_request = OTPRequest.objects.filter(
            phone=phone,
            is_verified=False,
            expires_at__gt=timezone.now(),
        ).order_by('-created_at').first()

        if not otp_request:  # 2026-02-12: No valid OTP found
            return {
                'success': False,
                'error': 'No valid OTP found. Please request a new one.',
                'code': 'OTP_NOT_FOUND',
            }

        if otp_request.attempts >= max_attempts:  # 2026-02-12: Too many attempts
            return {
                'success': False,
                'error': 'Maximum attempts exceeded. Please request a new OTP.',
                'code': 'MAX_ATTEMPTS',
            }

        # 2026-02-12: Increment attempt counter
        otp_request.attempts += 1
        otp_request.save(update_fields=['attempts'])

        # 2026-02-12: Verify OTP hash
        if not cls._verify_hash(otp_code, otp_request.otp_hash):
            return {
                'success': False,
                'error': 'Invalid OTP code.',
                'code': 'INVALID_OTP',
            }

        # 2026-02-12: Mark as verified
        otp_request.is_verified = True
        otp_request.save(update_fields=['is_verified'])

        return {'success': True, 'message': 'OTP verified successfully.'}

    @classmethod
    def complete_registration(cls, phone, full_name, email='', state='',
                              preferred_language='en'):
        """
        2026-02-12: Complete parent registration after OTP verification.

        Args:
            phone: Verified phone number.
            full_name: Parent's full name.
            email: Optional email.
            state: Indian state for language suggestions.
            preferred_language: UI language preference.

        Returns:
            dict: Result with tokens and parent data.
        """
        # 2026-02-12: Verify phone was OTP-verified
        verified_otp = OTPRequest.objects.filter(
            phone=phone,
            is_verified=True,
            purpose='registration',
        ).exists()

        if not verified_otp:  # 2026-02-12: Phone not verified
            return {
                'success': False,
                'error': 'Phone number not verified. Complete OTP verification first.',
                'code': 'PHONE_NOT_VERIFIED',
            }

        # 2026-02-12: Check if parent already exists
        if Parent.objects.filter(phone=phone).exists():
            return {
                'success': False,
                'error': 'An account with this phone number already exists.',
                'code': 'DUPLICATE_PHONE',
            }

        # 2026-02-12: Create Django user
        username = f"parent_{phone.replace('+', '')}"
        user = User.objects.create_user(
            username=username,
            password=None,  # 2026-02-12: No password - OTP based
        )

        # 2026-02-12: Create parent profile
        parent = Parent.objects.create(
            user=user,
            phone=phone,
            full_name=full_name,
            email=email,
            state=state,
            preferred_language=preferred_language,
            is_phone_verified=True,
            is_profile_complete=True,
        )

        # 2026-02-12: Generate JWT tokens
        tokens = get_tokens_for_parent(parent)

        # 2026-02-12: Audit log
        AuditLog.objects.create(
            user=user,
            action='registration_complete',
            resource_type='parent',
            metadata={'phone': phone},
        )

        return {  # 2026-02-12: Success with tokens
            'success': True,
            'tokens': tokens,
            'parent': {
                'id': str(parent.id),
                'phone': parent.phone,
                'full_name': parent.full_name,
                'email': parent.email,
                'state': parent.state,
            },
        }

    @classmethod
    def parent_login(cls, phone):
        """
        2026-02-12: Login existing parent after OTP verification.

        Args:
            phone: Verified phone number.

        Returns:
            dict: Result with tokens and parent data.
        """
        # 2026-02-12: Verify OTP was completed
        verified_otp = OTPRequest.objects.filter(
            phone=phone,
            is_verified=True,
            purpose='login',
        ).order_by('-created_at').first()

        if not verified_otp:  # 2026-02-12: Not verified
            return {
                'success': False,
                'error': 'Phone number not verified.',
                'code': 'PHONE_NOT_VERIFIED',
            }

        # 2026-02-12: Find parent
        try:
            parent = Parent.objects.get(phone=phone)
        except Parent.DoesNotExist:
            return {
                'success': False,
                'error': 'No account found with this phone number.',
                'code': 'PARENT_NOT_FOUND',
            }

        # 2026-02-12: Generate tokens
        tokens = get_tokens_for_parent(parent)

        # 2026-02-12: Audit log
        AuditLog.objects.create(
            user=parent.user,
            action='parent_login',
            resource_type='parent',
            metadata={'phone': phone},
        )

        return {  # 2026-02-12: Success
            'success': True,
            'tokens': tokens,
            'parent': {
                'id': str(parent.id),
                'phone': parent.phone,
                'full_name': parent.full_name,
                'students': [
                    {
                        'id': str(s.id),
                        'full_name': s.full_name,
                        'avatar_id': s.avatar_id,
                        'grade': s.grade,
                        'login_method': s.login_method,
                    }
                    for s in parent.students.filter(is_active=True)
                ],
            },
        }

    @classmethod
    def create_student(cls, parent, full_name, dob, grade, avatar_id='avatar_01',
                       pin=None, picture_sequence=None, password=None,
                       language_1='English', language_2='', language_3=''):
        """
        2026-02-12: Create a student profile under a parent.

        Args:
            parent: Parent model instance.
            full_name: Student name.
            dob: Date of birth.
            grade: Class/grade number.
            avatar_id: Avatar identifier.
            pin: 4-digit PIN (for ages 6-12).
            picture_sequence: Ordered picture IDs (for ages 3-6).
            password: Password string (for ages 12+).
            language_1: Primary language.
            language_2: Second language.
            language_3: Third language.

        Returns:
            dict: Result with student data.
        """
        # 2026-02-12: Compute age group and login method
        age_group = Student.compute_age_group(dob)
        login_method = Student.get_login_method_for_age_group(age_group)

        # 2026-02-12: Create Django user for JWT
        username = f"student_{str(parent.id)[:8]}_{full_name.lower().replace(' ', '_')}"
        user = User.objects.create_user(
            username=username,
            password=password if login_method == 'password' else None,
        )

        # 2026-02-12: Hash credentials based on login method
        pin_hash = ''
        picture_hash = ''
        if login_method == 'pin' and pin:
            pin_hash = cls._hash_value(pin)
        elif login_method == 'picture' and picture_sequence:
            sequence_str = ','.join(picture_sequence)
            picture_hash = cls._hash_value(sequence_str)

        # 2026-02-12: Create student record
        student = Student.objects.create(
            parent=parent,
            user=user,
            full_name=full_name,
            dob=dob,
            age_group=age_group,
            grade=grade,
            login_method=login_method,
            avatar_id=avatar_id,
            pin_hash=pin_hash,
            picture_sequence_hash=picture_hash,
            language_1=language_1,
            language_2=language_2,
            language_3=language_3,
        )

        # 2026-02-12: Audit log
        AuditLog.objects.create(
            user=parent.user,
            action='student_created',
            resource_type='student',
            metadata={
                'student_id': str(student.id),
                'age_group': age_group,
                'login_method': login_method,
            },
        )

        return {  # 2026-02-12: Success
            'success': True,
            'student': {
                'id': str(student.id),
                'full_name': student.full_name,
                'age_group': student.age_group,
                'grade': student.grade,
                'login_method': student.login_method,
                'avatar_id': student.avatar_id,
            },
        }

    @classmethod
    def student_picture_login(cls, student_id, picture_sequence):
        """
        2026-02-12: Verify picture sequence login for young students.

        Args:
            student_id: Student UUID.
            picture_sequence: List of picture IDs in order.

        Returns:
            dict: Result with tokens on success.
        """
        try:
            student = Student.objects.get(  # 2026-02-12: Find student
                id=student_id, login_method='picture', is_active=True
            )
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Student not found.',
                'code': 'STUDENT_NOT_FOUND',
            }

        # 2026-02-12: Verify picture sequence
        sequence_str = ','.join(picture_sequence)
        if not cls._verify_hash(sequence_str, student.picture_sequence_hash):
            return {
                'success': False,
                'error': 'Incorrect picture sequence.',
                'code': 'INVALID_PICTURES',
            }

        # 2026-02-12: Generate tokens
        tokens = get_tokens_for_student(student)

        AuditLog.objects.create(  # 2026-02-12: Audit
            user=student.user,
            action='student_picture_login',
            resource_type='student',
        )

        return {  # 2026-02-12: Success
            'success': True,
            'tokens': tokens,
            'student': {
                'id': str(student.id),
                'full_name': student.full_name,
                'grade': student.grade,
                'avatar_id': student.avatar_id,
            },
        }

    @classmethod
    def student_pin_login(cls, student_id, pin):
        """
        2026-02-12: Verify PIN login for middle childhood students.

        Args:
            student_id: Student UUID.
            pin: 4-digit PIN string.

        Returns:
            dict: Result with tokens on success.
        """
        try:
            student = Student.objects.get(  # 2026-02-12: Find student
                id=student_id, login_method='pin', is_active=True
            )
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Student not found.',
                'code': 'STUDENT_NOT_FOUND',
            }

        # 2026-02-12: Verify PIN
        if not cls._verify_hash(pin, student.pin_hash):
            return {
                'success': False,
                'error': 'Incorrect PIN.',
                'code': 'INVALID_PIN',
            }

        # 2026-02-12: Generate tokens
        tokens = get_tokens_for_student(student)

        AuditLog.objects.create(  # 2026-02-12: Audit
            user=student.user,
            action='student_pin_login',
            resource_type='student',
        )

        return {  # 2026-02-12: Success
            'success': True,
            'tokens': tokens,
            'student': {
                'id': str(student.id),
                'full_name': student.full_name,
                'grade': student.grade,
                'avatar_id': student.avatar_id,
            },
        }

    @classmethod
    def record_consent(cls, parent, consent_version, action, scroll_percentage=0,
                       ip_address=None):
        """
        2026-02-12: Record a consent grant or withdrawal.

        Args:
            parent: Parent model instance.
            consent_version: Version of consent document.
            action: 'grant' or 'withdraw'.
            scroll_percentage: How far user scrolled (0-100).
            ip_address: Client IP address.

        Returns:
            dict: Result with consent record.
        """
        record = ConsentRecord.objects.create(  # 2026-02-12: Append-only
            parent=parent,
            consent_version=consent_version,
            action=action,
            scroll_percentage=scroll_percentage,
            ip_address=ip_address,
        )

        AuditLog.objects.create(  # 2026-02-12: Audit
            user=parent.user,
            action=f'consent_{action}',
            resource_type='consent',
            metadata={'version': consent_version},
        )

        return {  # 2026-02-12: Success
            'success': True,
            'consent': {
                'id': str(record.id),
                'action': record.action,
                'consent_version': record.consent_version,
                'timestamp': record.timestamp.isoformat(),
            },
        }
