"""
2026-03-04: Passkey / WebAuthn serializers (BS-AUTH-002).

Purpose:
    Validate request bodies for registration and authentication
    endpoints.  credential_json is accepted as a free-form dict
    because the WebAuthn JSON structure is deeply nested and
    validated entirely by py_webauthn.
"""

from rest_framework import serializers  # 2026-03-04: DRF


class PasskeyRegisterStartSerializer(serializers.Serializer):
    """2026-03-04: Start passkey registration — optionally for a student."""

    device_name = serializers.CharField(  # 2026-03-04: Human label for the credential
        max_length=100, required=False, default='Passkey'
    )
    student_id = serializers.UUIDField(  # 2026-03-04: Parent registers for student
        required=False, allow_null=True, default=None
    )


class PasskeyRegisterCompleteSerializer(serializers.Serializer):
    """2026-03-04: Complete passkey registration."""

    challenge_id = serializers.UUIDField()  # 2026-03-04: ID returned from start
    credential = serializers.DictField()  # 2026-03-04: Raw WebAuthn JSON from browser
    device_name = serializers.CharField(
        max_length=100, required=False, default='Passkey'
    )
    student_id = serializers.UUIDField(  # 2026-03-04: Keep student context
        required=False, allow_null=True, default=None
    )


class PasskeyAuthStartSerializer(serializers.Serializer):
    """2026-03-04: Start passkey authentication."""

    student_id = serializers.UUIDField(  # 2026-03-04: Limit allowCredentials to student
        required=False, allow_null=True, default=None
    )


class PasskeyAuthCompleteSerializer(serializers.Serializer):
    """2026-03-04: Complete passkey authentication."""

    challenge_id = serializers.UUIDField()  # 2026-03-04: From start step
    credential = serializers.DictField()  # 2026-03-04: Raw WebAuthn JSON from browser
