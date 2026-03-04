"""
2026-03-04: LLM Providers Package.

Purpose:
    Contains concrete implementations of LLMProvider.
    All providers implement the LLMProvider interface (base.py).

Available Providers:
    - OllamaProvider : Local Ollama server (llama3.2, mistral, phi3, …)
    - OpenAIProvider : OpenAI API (GPT-4o, GPT-4o-mini, GPT-3.5-turbo, …)
    - AnthropicProvider: Anthropic API (Haiku / Sonnet / Opus)
    - MockLLMProvider : Deterministic mock for automated tests

Switching providers:
    Change two settings in settings.py — no code changes required:
        LLM_PROVIDER = 'openai'
        LLM_CONFIG   = {'model_name': 'gpt-4o-mini', 'api_key': '...'}

Adding a new provider:
    1. Create services/llm_service/providers/my_provider.py
    2. Implement class MyProvider(LLMProvider)
    3. Add conditional import below
    4. Register in LLMFactory.PROVIDERS (factory.py)
"""

# 2026-03-04: Core provider — always available (no extra dependencies)
from .ollama_provider import OllamaProvider  # 2026-03-04: Local Ollama
from .mock_provider import MockLLMProvider  # 2026-03-04: Test mock

# 2026-03-04: Optional providers — available when the SDK is installed
try:
    from .openai_provider import OpenAIProvider  # 2026-03-04: pip install openai>=1.0
except ImportError:
    OpenAIProvider = None  # type: ignore[assignment,misc]  # 2026-03-04: Not installed

try:
    from .anthropic_provider import AnthropicProvider  # 2026-03-04: pip install anthropic>=0.20
except ImportError:
    AnthropicProvider = None  # type: ignore[assignment,misc]  # 2026-03-04: Not installed

# 2026-03-04: Export all available providers
__all__ = [
    'OllamaProvider',
    'MockLLMProvider',
    'OpenAIProvider',
    'AnthropicProvider',
]
