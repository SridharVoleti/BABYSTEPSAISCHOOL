"""
2026-03-04: Mock LLM Provider for testing.

Purpose:
    Deterministic, zero-latency LLM provider for use in tests.
    Returns configurable responses without any network calls.
    Register with LLM_PROVIDER = 'mock' in test settings.

Usage:
    # In conftest.py or Django test settings:
    settings.LLM_PROVIDER = 'mock'
    settings.LLM_CONFIG = {'model_name': 'mock', 'response': 'test response'}

    # Or patch globally for a test:
    @patch('services.llm_service.factory._provider_instance', MockLLMProvider())
"""

# Python standard library
import logging  # 2026-03-04: Module logger
from typing import List, Optional  # 2026-03-04: Type hints

# Local imports
from ..base import LLMProvider, LLMResponse  # 2026-03-04: ABC + response type

# Configure logging
logger = logging.getLogger(__name__)  # 2026-03-04: Module logger


class MockLLMProvider(LLMProvider):
    """
    2026-03-04: Mock LLM provider for automated tests.

    Purpose:
        Provides deterministic, instant responses without network calls.
        Supports a configurable default response and a callable override
        so individual tests can control what the 'LLM' returns.

    Attributes:
        default_response: Text returned for every chat() call.
        response_override: Optional callable(message, system_prompt) → str
                           for dynamic per-call control.
        call_count: Number of chat() calls made (useful for assertions).
    """

    def __init__(  # 2026-03-04: Initialize mock provider
        self,
        model_name: str = 'mock',
        default_response: str = 'Mock LLM response.',
        response_override=None,  # 2026-03-04: Optional callable(message, system_prompt) → str
        **kwargs,
    ):
        """
        2026-03-04: Initialize mock provider.

        Args:
            model_name: Model name string (cosmetic).
            default_response: Text returned for every chat() call.
            response_override: If provided, called with (message, system_prompt)
                               and its return value is used instead of default_response.
            **kwargs: Ignored (absorbs LLM_CONFIG extras).
        """
        super().__init__(model_name=model_name, base_url=None, api_key=None)
        self.default_response = default_response  # 2026-03-04: Default reply text
        self.response_override = response_override  # 2026-03-04: Optional callable
        self.call_count: int = 0  # 2026-03-04: Track call count for assertions
        self.last_message: Optional[str] = None  # 2026-03-04: Last message received
        self.last_system_prompt: Optional[str] = None  # 2026-03-04: Last system prompt

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        2026-03-04: Return a mock response.

        Args:
            message: User message (stored in last_message).
            system_prompt: System prompt (stored in last_system_prompt).
            temperature: Ignored.
            max_tokens: Ignored.
            **kwargs: Ignored.

        Returns:
            LLMResponse: Instant response with mock text.
        """
        self.call_count += 1  # 2026-03-04: Increment call count
        self.last_message = message  # 2026-03-04: Record last message
        self.last_system_prompt = system_prompt  # 2026-03-04: Record system prompt

        # 2026-03-04: Use override callable if provided, otherwise use default
        if self.response_override is not None:
            text = self.response_override(message, system_prompt)  # 2026-03-04: Dynamic response
        else:
            text = self.default_response  # 2026-03-04: Static default

        logger.debug(  # 2026-03-04: Debug log for test visibility
            "MockLLMProvider.chat() called #%d — returning: %r",
            self.call_count,
            text[:80],
        )

        return LLMResponse(  # 2026-03-04: Return standardized response
            text=text,
            model=self.model_name,
            tokens_used=len(text.split()),  # 2026-03-04: Approximate token count
            latency_ms=0.0,  # 2026-03-04: No latency for mock
            metadata={'provider': 'mock'},
            success=True,
            error=None,
        )

    def health_check(self, force: bool = False) -> bool:
        """
        2026-03-04: Mock health check always returns True.

        Returns:
            bool: Always True (mock is always healthy).
        """
        return True  # 2026-03-04: Mock is always available

    def get_available_models(self) -> List[str]:
        """
        2026-03-04: Return a single mock model name.

        Returns:
            List[str]: ['mock']
        """
        return [self.model_name]  # 2026-03-04: Return mock model name
