"""
2026-02-12: Abstract base class for OTP providers.

Purpose:
    Define interface for all OTP providers (Mock, Twilio, Gupshup).
    Follows the same Factory+Strategy+ABC pattern as llm_service.
"""

from abc import ABC, abstractmethod  # 2026-02-12: Abstract base class


class OTPProvider(ABC):
    """
    2026-02-12: Abstract base class for OTP delivery providers.

    All OTP providers must implement send_otp() and health_check().
    """

    @abstractmethod
    def send_otp(self, phone: str, otp_code: str) -> bool:
        """
        2026-02-12: Send OTP to the given phone number.

        Args:
            phone: Phone number with country code.
            otp_code: The OTP code to send.

        Returns:
            bool: True if sent successfully.
        """
        pass  # pragma: no cover

    @abstractmethod
    def health_check(self) -> bool:
        """
        2026-02-12: Check if the OTP provider is available.

        Returns:
            bool: True if provider is healthy.
        """
        pass  # pragma: no cover
