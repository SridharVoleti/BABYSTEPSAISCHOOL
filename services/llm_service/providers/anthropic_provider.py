"""
2026-03-04: Anthropic Claude LLM Provider implementation.

Purpose:
    Concrete LLMProvider for Anthropic Claude models (claude-opus-4-6,
    claude-sonnet-4-6, claude-haiku-4-5, etc.)
    Uses the anthropic SDK (anthropic.Anthropic client).

Setup:
    1. pip install anthropic>=0.20
    2. Set ANTHROPIC_API_KEY in environment (or pass api_key directly)
    3. In settings.py:
           LLM_PROVIDER = 'anthropic'
           LLM_CONFIG = {
               'model_name': 'claude-haiku-4-5-20251001',  # fast + cheap
               'api_key': os.getenv('ANTHROPIC_API_KEY'),
               'timeout': 60,
           }

Usage:
    llm = get_llm_provider()
    response = llm.chat(message="Hello", system_prompt="You are helpful")
    print(response.text)
"""

# Python standard library
import time  # 2026-03-04: Latency measurement
import logging  # 2026-03-04: Module logger
from typing import List, Optional  # 2026-03-04: Type hints

# Third-party imports — installed separately: pip install anthropic>=0.20
try:
    import anthropic  # 2026-03-04: Anthropic SDK
    _anthropic_available = True  # 2026-03-04: SDK present
except ImportError:
    _anthropic_available = False  # 2026-03-04: SDK not installed

# Local imports
from ..base import LLMProvider, LLMResponse, LLMError  # 2026-03-04: ABC + types

# Configure logging
logger = logging.getLogger(__name__)  # 2026-03-04: Module logger


class AnthropicProvider(LLMProvider):
    """
    2026-03-04: Anthropic Claude provider.

    Purpose:
        Provide a standardized LLM interface for Claude models.
        Supports the full Claude 4.x/3.x model family.

    Design:
        - Uses anthropic.Anthropic() client (SDK v0.20+).
        - Claude requires max_tokens; defaults to 1024 if not specified.
        - Raises LLMError on failure.

    Configuration (via settings.LLM_CONFIG):
        model_name: Claude model id (default: claude-haiku-4-5-20251001)
        api_key: Anthropic API key (or ANTHROPIC_API_KEY env var)
        timeout: Request timeout seconds (default: 60)
    """

    def __init__(  # 2026-03-04: Initialize Anthropic provider
        self,
        model_name: str = 'claude-haiku-4-5-20251001',
        api_key: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ):
        """
        2026-03-04: Initialize the Anthropic provider.

        Args:
            model_name: Claude model id (e.g. 'claude-haiku-4-5-20251001').
            api_key: API key. Falls back to ANTHROPIC_API_KEY env var if None.
            timeout: HTTP request timeout in seconds.
            **kwargs: Absorbed for forward-compatibility.

        Raises:
            LLMError: If the anthropic package is not installed.
        """
        if not _anthropic_available:  # 2026-03-04: SDK not installed
            raise LLMError(
                "anthropic package not installed. Run: pip install anthropic>=0.20",
                provider='anthropic',
            )

        super().__init__(  # 2026-03-04: Call LLMProvider base
            model_name=model_name,
            base_url=None,
            api_key=api_key,
        )

        self.timeout = timeout  # 2026-03-04: Store timeout

        # 2026-03-04: Create the anthropic.Anthropic client
        client_kwargs = {}
        if api_key:
            client_kwargs['api_key'] = api_key  # 2026-03-04: Explicit key
        self._client = anthropic.Anthropic(**client_kwargs)  # 2026-03-04: SDK client

        logger.info(  # 2026-03-04: Log initialization
            "AnthropicProvider initialized: model=%s", model_name
        )

    def chat(  # 2026-03-04: Generate chat completion
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs,
    ) -> LLMResponse:
        """
        2026-03-04: Generate a response from Claude.

        Args:
            message: User message.
            system_prompt: Optional system context (Claude 'system' param).
            temperature: Sampling temperature (0.0–1.0).
            max_tokens: Max output tokens (Claude requires this; default 1024).
            **kwargs: Extra params forwarded to the API.

        Returns:
            LLMResponse: Standardized response.

        Raises:
            LLMError: On API error.
        """
        self._validate_parameters(temperature=temperature, max_tokens=max_tokens)

        if max_tokens is None:  # 2026-03-04: Claude requires max_tokens
            max_tokens = 1024

        start_time = time.time()  # 2026-03-04: Start latency timer

        try:
            # 2026-03-04: Build API call kwargs
            api_kwargs = {
                'model': self.model_name,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': [{'role': 'user', 'content': message}],
                **kwargs,
            }
            if system_prompt:  # 2026-03-04: Claude uses top-level 'system' param
                api_kwargs['system'] = system_prompt

            response = self._client.messages.create(**api_kwargs)  # 2026-03-04: API call

            latency_ms = (time.time() - start_time) * 1000  # 2026-03-04: Latency

            response_text = response.content[0].text  # 2026-03-04: Extract text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return LLMResponse(  # 2026-03-04: Return standardized response
                text=response_text,
                model=self.model_name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    'provider': 'anthropic',
                    'stop_reason': response.stop_reason,
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                },
                success=True,
                error=None,
            )

        except Exception as exc:  # 2026-03-04: API or network error
            latency_ms = (time.time() - start_time) * 1000
            logger.error(  # 2026-03-04: Log error details
                "Anthropic chat failed: %s (model=%s, latency=%.0fms)",
                exc,
                self.model_name,
                latency_ms,
                exc_info=True,
            )
            raise LLMError(  # 2026-03-04: Re-raise as LLMError
                f"Anthropic generation failed: {exc}",
                provider='anthropic',
                original_error=exc,
            )

    def health_check(self, force: bool = False) -> bool:  # 2026-03-04: Health check
        """
        2026-03-04: Check if Anthropic API is reachable via a minimal message call.

        Args:
            force: Ignored (reserved for cache invalidation).

        Returns:
            bool: True if API responds, False on any error.
        """
        try:
            # 2026-03-04: Minimal 1-token call to verify connectivity + key validity
            self._client.messages.create(
                model=self.model_name,
                max_tokens=1,
                messages=[{'role': 'user', 'content': 'ping'}],
            )
            if force:
                logger.info("Anthropic health: healthy (model=%s)", self.model_name)
            return True
        except Exception as exc:  # 2026-03-04: Connection or auth error
            logger.warning("Anthropic health check failed: %s", exc)
            return False

    def get_available_models(self) -> List[str]:  # 2026-03-04: List known models
        """
        2026-03-04: Return the known Claude model catalogue.

        Anthropic does not expose a REST models-list endpoint, so we return
        a static list of current production models.

        Returns:
            List[str]: Known Claude model ids.
        """
        return [  # 2026-03-04: Current Claude models (March 2026)
            'claude-opus-4-6',
            'claude-sonnet-4-6',
            'claude-haiku-4-5-20251001',
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
        ]
