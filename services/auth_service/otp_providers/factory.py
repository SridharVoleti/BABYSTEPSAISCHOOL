"""
2026-02-12: OTP provider factory.

Purpose:
    Factory pattern for creating OTP provider instances.
    Reads provider config from Django settings.
"""

import logging  # 2026-02-12: Logging
from typing import Optional  # 2026-02-12: Type hints

from django.conf import settings  # 2026-02-12: Django settings

from .base import OTPProvider  # 2026-02-12: Abstract base
from .mock_provider import MockOTPProvider  # 2026-02-12: Mock provider
from .twilio_provider import TwilioOTPProvider  # 2026-02-12: Twilio provider

logger = logging.getLogger(__name__)  # 2026-02-12: Module logger

# 2026-02-12: Singleton instance
_provider_instance: Optional[OTPProvider] = None


class OTPFactory:
    """2026-02-12: Factory for creating OTP provider instances."""

    PROVIDERS = {  # 2026-02-12: Provider name to class mapping
        'mock': MockOTPProvider,
        'twilio': TwilioOTPProvider,
    }

    @classmethod
    def get_provider(cls) -> OTPProvider:
        """
        2026-02-12: Get OTP provider instance (singleton).

        Returns:
            OTPProvider: Configured provider instance.

        Raises:
            ValueError: If provider name is not supported.
        """
        global _provider_instance  # 2026-02-12: Use singleton
        if _provider_instance is not None:  # 2026-02-12: Return cached instance
            return _provider_instance

        provider_name = getattr(  # 2026-02-12: Read from settings
            settings, 'OTP_PROVIDER', 'mock'
        )
        provider_class = cls.PROVIDERS.get(provider_name)  # 2026-02-12: Lookup class

        if provider_class is None:  # 2026-02-12: Unknown provider
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported OTP provider: {provider_name}. "
                f"Available: {available}"
            )

        logger.info(f"Creating OTP provider: {provider_name}")  # 2026-02-12: Log
        _provider_instance = provider_class()  # 2026-02-12: Create and cache
        return _provider_instance

    @classmethod
    def reset(cls):
        """2026-02-12: Reset singleton (for testing)."""
        global _provider_instance  # 2026-02-12: Clear cache
        _provider_instance = None
