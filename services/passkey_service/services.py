"""
2026-03-04: Passkey / WebAuthn business logic (BS-AUTH-002).

Purpose:
    Wrap py_webauthn to handle credential registration and authentication.
    Challenges are stored in Django's cache (30 s expiry); no DB model needed.
    After successful authentication, the caller can issue JWT tokens via the
    existing jwt_utils helpers in auth_service.
"""

import json
import logging
import uuid
from typing import Optional

from django.conf import settings  # 2026-03-04: WEBAUTHN_RP_ID etc.
from django.contrib.auth import get_user_model  # 2026-03-04: Django User model
from django.core.cache import cache  # 2026-03-04: Challenge storage
from django.utils import timezone  # 2026-03-04: last_used_at

import webauthn  # 2026-03-04: py_webauthn v2+
from webauthn.helpers.structs import (  # 2026-03-04: Typed structs
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier  # 2026-03-04: Key algorithm

from .models import PasskeyCredential  # 2026-03-04: Credential model

logger = logging.getLogger(__name__)
User = get_user_model()  # 2026-03-04: Concrete user class

_CHALLENGE_TTL = 30  # 2026-03-04: Cache seconds for WebAuthn challenges
_CHALLENGE_KEY = 'webauthn_challenge:{challenge_id}'  # 2026-03-04: Cache key pattern


class PasskeyService:
    """
    2026-03-04: Service layer for WebAuthn credential management.

    All methods are static/class-level — no instance state needed.
    """

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @staticmethod
    def get_registration_options(user, device_name: str = '') -> tuple[dict, str]:
        """
        2026-03-04: Generate WebAuthn registration options for a user.

        Returns (options_dict, challenge_id) where challenge_id is stored
        in cache and must be echoed back to complete_registration.

        Args:
            user: Django User instance.
            device_name: Human-readable label for the credential.

        Returns:
            Tuple of (options_as_dict, challenge_id_string).
        """
        challenge_id = str(uuid.uuid4())  # 2026-03-04: Unique challenge identifier

        # 2026-03-04: Collect existing credential IDs to exclude (avoid duplicate registrations)
        existing = list(
            PasskeyCredential.objects.filter(user=user)
            .values_list('credential_id', flat=True)
        )
        exclude_credentials = [
            PublicKeyCredentialDescriptor(id=bytes(cid)) for cid in existing
        ]

        options = webauthn.generate_registration_options(
            rp_id=settings.WEBAUTHN_RP_ID,
            rp_name=settings.WEBAUTHN_RP_NAME,
            user_id=str(user.pk).encode(),  # 2026-03-04: Must be bytes
            user_name=user.username,
            user_display_name=getattr(user, 'get_full_name', lambda: user.username)() or user.username,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )

        # 2026-03-04: Cache the challenge bytes so we can verify them later
        cache.set(
            _CHALLENGE_KEY.format(challenge_id=challenge_id),
            bytes(options.challenge),
            timeout=_CHALLENGE_TTL,
        )

        options_dict = json.loads(webauthn.options_to_json(options))
        options_dict['challenge_id'] = challenge_id  # 2026-03-04: Add our tracking ID
        return options_dict, challenge_id

    @staticmethod
    def complete_registration(
        user,
        challenge_id: str,
        credential_json: dict,
        device_name: str = '',
    ) -> 'PasskeyCredential':
        """
        2026-03-04: Verify registration response and persist PasskeyCredential.

        Args:
            user: Django User instance (must be authenticated).
            challenge_id: UUID string returned from get_registration_options.
            credential_json: Full JSON body from @simplewebauthn/browser startRegistration().
            device_name: Label for the credential.

        Returns:
            New PasskeyCredential instance.

        Raises:
            ValueError: Challenge not found, invalid response, or duplicate credential_id.
        """
        cache_key = _CHALLENGE_KEY.format(challenge_id=challenge_id)
        expected_challenge = cache.get(cache_key)  # 2026-03-04: Retrieve cached challenge
        if expected_challenge is None:
            raise ValueError('Challenge expired or not found.')

        try:
            verification = webauthn.verify_registration_response(
                credential=credential_json,
                expected_challenge=expected_challenge,
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                expected_origin=settings.WEBAUTHN_ORIGIN,
                require_user_verification=False,  # 2026-03-04: Optional UV
            )
        except Exception as exc:  # 2026-03-04: py_webauthn raises generic Exception
            logger.warning('WebAuthn registration verification failed: %s', exc)
            raise ValueError(f'Registration verification failed: {exc}') from exc
        finally:
            cache.delete(cache_key)  # 2026-03-04: One-time use

        # 2026-03-04: Persist credential
        if PasskeyCredential.objects.filter(
            credential_id=verification.credential_id
        ).exists():
            raise ValueError('Credential ID already registered.')

        transports = credential_json.get('response', {}).get('transports', [])  # 2026-03-04: Optional
        credential = PasskeyCredential.objects.create(
            user=user,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            device_name=device_name or 'Passkey',
            transports=transports if isinstance(transports, list) else [],
        )
        logger.info('Passkey registered for user %s (%s)', user.pk, device_name)
        return credential

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @staticmethod
    def get_authentication_options(
        user_credential_ids: Optional[list] = None,
    ) -> tuple[dict, str]:
        """
        2026-03-04: Generate WebAuthn authentication options.

        Args:
            user_credential_ids: Optional list of credential_id bytes to limit
                allowCredentials (pass for student flow; None = discoverable).

        Returns:
            Tuple of (options_as_dict, challenge_id_string).
        """
        challenge_id = str(uuid.uuid4())  # 2026-03-04: Unique challenge

        allow_credentials = []
        if user_credential_ids:
            allow_credentials = [
                PublicKeyCredentialDescriptor(id=bytes(cid))
                for cid in user_credential_ids
            ]

        options = webauthn.generate_authentication_options(
            rp_id=settings.WEBAUTHN_RP_ID,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        cache.set(
            _CHALLENGE_KEY.format(challenge_id=challenge_id),
            bytes(options.challenge),
            timeout=_CHALLENGE_TTL,
        )

        options_dict = json.loads(webauthn.options_to_json(options))
        options_dict['challenge_id'] = challenge_id
        return options_dict, challenge_id

    @staticmethod
    def complete_authentication(
        challenge_id: str,
        credential_json: dict,
    ) -> tuple:
        """
        2026-03-04: Verify authentication response and return (User, role).

        Performs sign-count clone detection: if the stored sign_count >=
        the new sign count (and both are non-zero), the credential may be cloned.

        Args:
            challenge_id: UUID string returned from get_authentication_options.
            credential_json: Full JSON body from @simplewebauthn/browser startAuthentication().

        Returns:
            Tuple (django_user, role_string) where role_string is one of
            'student', 'parent', 'monitor'.

        Raises:
            ValueError: Challenge expired, credential unknown, or clone detected.
        """
        cache_key = _CHALLENGE_KEY.format(challenge_id=challenge_id)
        expected_challenge = cache.get(cache_key)
        if expected_challenge is None:
            raise ValueError('Challenge expired or not found.')

        # 2026-03-04: Look up credential by raw ID
        raw_id_hex = credential_json.get('rawId', '')
        try:
            # 2026-03-04: rawId arrives as base64url from the browser
            import base64
            # 2026-03-04: Decode base64url (may have padding issues)
            raw_id_bytes = base64.urlsafe_b64decode(raw_id_hex + '==')
        except Exception:
            raw_id_bytes = b''

        # 2026-03-04: Find matching credential (search all, py_webauthn does the match)
        # We try to find by credential id; rawId in JSON may differ in encoding
        credential_id_from_json = credential_json.get('id', '')
        try:
            import base64 as _b64
            cid_bytes = _b64.urlsafe_b64decode(credential_id_from_json + '==')
        except Exception:
            cid_bytes = b''

        try:
            stored = PasskeyCredential.objects.get(credential_id=cid_bytes)
        except PasskeyCredential.DoesNotExist:
            raise ValueError('Credential not found.')

        try:
            verification = webauthn.verify_authentication_response(
                credential=credential_json,
                expected_challenge=expected_challenge,
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                expected_origin=settings.WEBAUTHN_ORIGIN,
                credential_public_key=bytes(stored.public_key),
                credential_current_sign_count=stored.sign_count,
                require_user_verification=False,
            )
        except Exception as exc:
            logger.warning('WebAuthn authentication failed: %s', exc)
            raise ValueError(f'Authentication verification failed: {exc}') from exc
        finally:
            cache.delete(cache_key)

        # 2026-03-04: Clone detection
        new_count = verification.new_sign_count
        if stored.sign_count > 0 and new_count <= stored.sign_count:
            raise ValueError(
                'Sign count did not increase — possible cloned authenticator.'
            )

        # 2026-03-04: Update sign count and last_used_at
        stored.sign_count = new_count
        stored.last_used_at = timezone.now()
        stored.save(update_fields=['sign_count', 'last_used_at'])

        user = stored.user
        role = PasskeyService._determine_role(user)
        return user, role

    @staticmethod
    def _determine_role(user) -> str:
        """2026-03-04: Map Django User to BabySteps role string."""
        if hasattr(user, 'student_profile') and user.student_profile:
            return 'student'
        if hasattr(user, 'parent_profile') and user.parent_profile:
            return 'parent'
        if user.is_staff:
            return 'monitor'
        return 'unknown'

    # ------------------------------------------------------------------
    # Student helper
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_student_user(student) -> object:
        """
        2026-03-04: Return the Django User linked to a Student, creating one if absent.

        Creates a minimal User (username=student_{uuid}, unusable password)
        so the student can have passkeys linked via User FK.

        Args:
            student: Student model instance from auth_service.

        Returns:
            Django User instance.
        """
        if student.user_id:
            return student.user

        username = f'student_{student.pk}'
        user = User.objects.create_user(
            username=username,
            password=None,  # 2026-03-04: Unusable password — passkey only
        )
        user.set_unusable_password()
        user.save(update_fields=['password'])

        student.user = user
        student.save(update_fields=['user'])
        logger.info('Created Django User %s for Student %s', user.pk, student.pk)
        return user
