"""
2026-02-12: Mock OTP provider for development.

Purpose:
    Logs OTP to console instead of sending via WhatsApp.
    Used in development and testing environments.
"""

import logging  # 2026-02-12: Logging

from .base import OTPProvider  # 2026-02-12: Abstract base

logger = logging.getLogger(__name__)  # 2026-02-12: Module logger


class MockOTPProvider(OTPProvider):
    """2026-02-12: Mock OTP provider that logs OTP to console."""

    def send_otp(self, phone: str, otp_code: str) -> bool:
        """
        2026-02-12: Log OTP to console instead of sending.

        Args:
            phone: Phone number.
            otp_code: The OTP code.

        Returns:
            bool: Always True.
        """
        logger.info(  # 2026-02-12: Log OTP for dev use
            f"[MOCK OTP] Phone: {phone} | OTP: {otp_code}"
        )
        print(f"\n{'='*50}")  # 2026-02-12: Visible console output
        print(f"  MOCK OTP for {phone}: {otp_code}")
        print(f"{'='*50}\n")
        return True  # 2026-02-12: Always succeeds

    def health_check(self) -> bool:
        """
        2026-02-12: Mock provider is always healthy.

        Returns:
            bool: Always True.
        """
        return True  # 2026-02-12: Always available
