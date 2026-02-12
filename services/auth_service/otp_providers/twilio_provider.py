"""
2026-02-12: Twilio WhatsApp OTP provider stub.

Purpose:
    Placeholder for future Twilio/WhatsApp OTP integration.
    Will be implemented when moving to production.
"""

import logging  # 2026-02-12: Logging

from .base import OTPProvider  # 2026-02-12: Abstract base

logger = logging.getLogger(__name__)  # 2026-02-12: Module logger


class TwilioOTPProvider(OTPProvider):
    """2026-02-12: Twilio WhatsApp OTP provider (stub for future use)."""

    def __init__(self, account_sid: str = '', auth_token: str = '', from_number: str = ''):
        """
        2026-02-12: Initialize Twilio provider.

        Args:
            account_sid: Twilio account SID.
            auth_token: Twilio auth token.
            from_number: WhatsApp sender number.
        """
        self.account_sid = account_sid  # 2026-02-12: Store credentials
        self.auth_token = auth_token  # 2026-02-12: Store credentials
        self.from_number = from_number  # 2026-02-12: Sender number

    def send_otp(self, phone: str, otp_code: str) -> bool:
        """
        2026-02-12: Send OTP via Twilio WhatsApp (not yet implemented).

        Args:
            phone: Phone number.
            otp_code: The OTP code.

        Returns:
            bool: False (not implemented).
        """
        logger.warning("Twilio OTP provider not yet implemented")  # 2026-02-12: Warn
        raise NotImplementedError(  # 2026-02-12: Not ready yet
            "Twilio WhatsApp OTP sending is not yet implemented. "
            "Use 'mock' provider for development."
        )

    def health_check(self) -> bool:
        """
        2026-02-12: Check Twilio connectivity (not yet implemented).

        Returns:
            bool: False (not implemented).
        """
        return False  # 2026-02-12: Not available yet
