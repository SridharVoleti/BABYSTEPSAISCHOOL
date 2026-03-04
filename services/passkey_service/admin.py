"""
2026-03-04: Passkey / WebAuthn admin configuration (BS-AUTH-002).

Purpose:
    Register PasskeyCredential in Django admin for inspection and
    manual revocation.
"""

from django.contrib import admin  # 2026-03-04: Admin framework

from .models import PasskeyCredential  # 2026-03-04: Model


@admin.register(PasskeyCredential)
class PasskeyCredentialAdmin(admin.ModelAdmin):
    """2026-03-04: Admin for PasskeyCredential model."""

    list_display = [  # 2026-03-04: Table columns
        'id', 'user', 'device_name', 'sign_count', 'created_at', 'last_used_at'
    ]
    list_filter = ['created_at']  # 2026-03-04: Sidebar filter
    search_fields = ['user__username', 'device_name']  # 2026-03-04: Search bar
    readonly_fields = [  # 2026-03-04: Never editable in admin
        'id', 'credential_id', 'public_key', 'sign_count',
        'created_at', 'last_used_at',
    ]
    ordering = ['-created_at']  # 2026-03-04: Newest first
