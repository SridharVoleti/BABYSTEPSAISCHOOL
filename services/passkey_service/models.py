"""
2026-03-04: Passkey / WebAuthn credential model (BS-AUTH-002).

Purpose:
    Store FIDO2 public-key credentials for each user.
    The private key never leaves the device — only the public key
    and a sign counter (clone detection) are stored server-side.
"""

import uuid  # 2026-03-04: UUID primary key

from django.conf import settings  # 2026-03-04: AUTH_USER_MODEL
from django.db import models  # 2026-03-04: Django ORM


class PasskeyCredential(models.Model):
    """
    2026-03-04: Stored WebAuthn credential for a Django user.

    One user can register multiple credentials (laptop, phone, etc.).
    credential_id is the FIDO2 credential identifier (binary, unique).
    public_key is the DER-encoded COSE public key.
    sign_count is incremented on each successful authentication to
    detect cloned authenticators.
    """

    id = models.UUIDField(  # 2026-03-04: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(  # 2026-03-04: Django user owning this credential
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='passkeys',
    )
    credential_id = models.BinaryField(  # 2026-03-04: FIDO2 credential ID (bytes)
        max_length=1024, unique=True
    )
    public_key = models.BinaryField(max_length=4096)  # 2026-03-04: DER-encoded public key
    sign_count = models.IntegerField(default=0)  # 2026-03-04: Clone-detection counter
    device_name = models.CharField(  # 2026-03-04: Human-readable label, e.g. "Windows Hello"
        max_length=100, blank=True, default=''
    )
    transports = models.JSONField(  # 2026-03-04: e.g. ["internal", "hybrid"]
        default=list, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-04: Registration time
    last_used_at = models.DateTimeField(null=True, blank=True)  # 2026-03-04: Last auth time

    class Meta:
        """2026-03-04: Model metadata."""

        ordering = ['-created_at']  # 2026-03-04: Newest first

    def __str__(self):
        """2026-03-04: String representation."""
        return f"{self.user.username} — {self.device_name or 'Passkey'}"
