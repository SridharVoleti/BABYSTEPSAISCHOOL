"""
2026-03-04: Passkey / WebAuthn URL configuration (BS-AUTH-002).

Purpose:
    Mount all passkey endpoints under /api/v1/passkeys/ (set in backend/urls.py).
"""

from django.urls import path  # 2026-03-04: URL routing

from .views import (  # 2026-03-04: Views
    PasskeyRegisterStartView, PasskeyRegisterCompleteView,
    PasskeyAuthStartView, PasskeyAuthCompleteView,
    PasskeyCredentialListView, PasskeyCredentialDeleteView,
)

urlpatterns = [
    # 2026-03-04: Registration flow
    path('register/start/', PasskeyRegisterStartView.as_view(), name='passkey-register-start'),
    path('register/complete/', PasskeyRegisterCompleteView.as_view(), name='passkey-register-complete'),
    # 2026-03-04: Authentication flow (public — login endpoint)
    path('authenticate/start/', PasskeyAuthStartView.as_view(), name='passkey-auth-start'),
    path('authenticate/complete/', PasskeyAuthCompleteView.as_view(), name='passkey-auth-complete'),
    # 2026-03-04: Credential management
    path('credentials/', PasskeyCredentialListView.as_view(), name='passkey-credentials-list'),
    path('credentials/<uuid:pk>/', PasskeyCredentialDeleteView.as_view(), name='passkey-credentials-delete'),
]
