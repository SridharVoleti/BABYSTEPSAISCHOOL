"""
2026-03-04: OpenAI LLM Provider implementation.

Purpose:
    Concrete LLMProvider for OpenAI GPT models (GPT-4o, GPT-4, GPT-3.5-turbo, etc.)
    Uses the openai v1.x SDK (openai.OpenAI client).

Setup:
    1. pip install openai>=1.0
    2. Set OPENAI_API_KEY in environment (or pass api_key directly)
    3. In settings.py:
           LLM_PROVIDER = 'openai'
           LLM_CONFIG = {
               'model_name': 'gpt-4o-mini',   # or 'gpt-4o', 'gpt-4-turbo', etc.
               'api_key': os.getenv('OPENAI_API_KEY'),
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

# Third-party imports — installed separately: pip install openai>=1.0
try:
    import openai  # 2026-03-04: OpenAI SDK v1.x
    _openai_available = True  # 2026-03-04: SDK present
except ImportError:
    _openai_available = False  # 2026-03-04: SDK not installed

# Local imports
from ..base import LLMProvider, LLMResponse, LLMError  # 2026-03-04: ABC + types

# Configure logging
logger = logging.getLogger(__name__)  # 2026-03-04: Module logger


class OpenAIProvider(LLMProvider):
    """
    2026-03-04: OpenAI GPT provider using the v1.x SDK.

    Purpose:
        Provide a standardized LLM interface for OpenAI chat-completion models.
        Supports GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo, and any
        future OpenAI chat-completion model.

    Design:
        - Uses the new openai.OpenAI() client (v1.x+ API).
        - Raises LLMError on failure (caller decides fallback strategy).
        - Stateless: each chat() call is independent.

    Configuration (via settings.LLM_CONFIG):
        model_name: OpenAI model id (default: gpt-4o-mini)
        api_key: OpenAI API key (or OPENAI_API_KEY env var)
        organization: OpenAI org id (optional)
        timeout: Request timeout seconds (default: 60)
    """

    def __init__(  # 2026-03-04: Initialize OpenAI provider
        self,
        model_name: str = 'gpt-4o-mini',
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ):
        """
        2026-03-04: Initialize the OpenAI provider.

        Args:
            model_name: OpenAI chat model id (e.g. 'gpt-4o-mini', 'gpt-4o').
            api_key: API key. Falls back to OPENAI_API_KEY env var if None.
            organization: Optional OpenAI organization id.
            timeout: HTTP request timeout in seconds.
            **kwargs: Absorbed for forward-compatibility with LLM_CONFIG extras.

        Raises:
            LLMError: If the openai package is not installed.
        """
        if not _openai_available:  # 2026-03-04: SDK not installed
            raise LLMError(
                "openai package not installed. Run: pip install openai>=1.0",
                provider='openai',
            )

        super().__init__(  # 2026-03-04: Call LLMProvider base
            model_name=model_name,
            base_url=None,
            api_key=api_key,
        )

        self.timeout = timeout  # 2026-03-04: Store timeout

        # 2026-03-04: Create the openai.OpenAI client (v1.x pattern)
        client_kwargs = {'timeout': float(timeout)}
        if api_key:
            client_kwargs['api_key'] = api_key  # 2026-03-04: Explicit key
        if organization:
            client_kwargs['organization'] = organization  # 2026-03-04: Optional org

        self._client = openai.OpenAI(**client_kwargs)  # 2026-03-04: v1.x client

        logger.info(  # 2026-03-04: Log initialization
            "OpenAIProvider initialized: model=%s org=%s",
            model_name,
            organization or 'default',
        )

    def chat(  # 2026-03-04: Generate chat completion
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        2026-03-04: Generate a chat-completion response from OpenAI.

        Args:
            message: User message.
            system_prompt: Optional system context.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens: Max output tokens (None = model default).
            **kwargs: Extra params forwarded to the API call.

        Returns:
            LLMResponse: Standardized response with .text, .tokens_used, .latency_ms.

        Raises:
            LLMError: On API error or network failure.
        """
        self._validate_parameters(temperature=temperature, max_tokens=max_tokens)

        # 2026-03-04: Build messages list (system + user)
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': message})

        start_time = time.time()  # 2026-03-04: Start latency timer

        try:
            # 2026-03-04: Call OpenAI v1.x API
            api_kwargs = {
                'model': self.model_name,
                'messages': messages,
                'temperature': temperature,
                **kwargs,
            }
            if max_tokens is not None:  # 2026-03-04: Only set if provided
                api_kwargs['max_tokens'] = max_tokens

            completion = self._client.chat.completions.create(**api_kwargs)

            latency_ms = (time.time() - start_time) * 1000  # 2026-03-04: Latency

            response_text = completion.choices[0].message.content  # 2026-03-04: Extract text
            tokens_used = completion.usage.total_tokens  # 2026-03-04: Token count

            return LLMResponse(  # 2026-03-04: Return standardized response
                text=response_text,
                model=self.model_name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    'provider': 'openai',
                    'finish_reason': completion.choices[0].finish_reason,
                    'prompt_tokens': completion.usage.prompt_tokens,
                    'completion_tokens': completion.usage.completion_tokens,
                },
                success=True,
                error=None,
            )

        except Exception as exc:  # 2026-03-04: API or network error
            latency_ms = (time.time() - start_time) * 1000
            logger.error(  # 2026-03-04: Log error details
                "OpenAI chat failed: %s (model=%s, latency=%.0fms)",
                exc,
                self.model_name,
                latency_ms,
                exc_info=True,
            )
            raise LLMError(  # 2026-03-04: Re-raise as LLMError
                f"OpenAI generation failed: {exc}",
                provider='openai',
                original_error=exc,
            )

    def health_check(self, force: bool = False) -> bool:  # 2026-03-04: Health check
        """
        2026-03-04: Check if OpenAI API is reachable.

        Performs a lightweight model list call. Returns False on any failure
        so the factory can warn without crashing startup.

        Args:
            force: Ignored (reserved for cache invalidation).

        Returns:
            bool: True if API is accessible, False otherwise.
        """
        try:
            models = self._client.models.list()  # 2026-03-04: v1.x models endpoint
            available = [m.id for m in models.data]
            is_healthy = self.model_name in available
            if force:
                logger.info(  # 2026-03-04: Verbose health log on forced check
                    "OpenAI health: %s (model=%s)",
                    'healthy' if is_healthy else 'model not found',
                    self.model_name,
                )
            return is_healthy
        except Exception as exc:  # 2026-03-04: Connection or auth error
            logger.warning("OpenAI health check failed: %s", exc)
            return False

    def get_available_models(self) -> List[str]:  # 2026-03-04: List models
        """
        2026-03-04: Return GPT chat models available on this account.

        Returns:
            List[str]: Model ids containing 'gpt'. Falls back to common models.
        """
        try:
            models = self._client.models.list()  # 2026-03-04: v1.x models list
            return [m.id for m in models.data if 'gpt' in m.id.lower()]  # 2026-03-04: Filter
        except Exception as exc:  # 2026-03-04: Return known fallback list
            logger.warning("Failed to list OpenAI models: %s", exc)
            return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
