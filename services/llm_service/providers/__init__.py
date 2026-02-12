"""
LLM Providers Package

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Contains concrete implementations of LLM providers.
    Each provider implements the LLMProvider interface.

Available Providers:
    - OllamaProvider: Local Ollama integration (llama3.2, mistral, etc.)
    - OpenAIProvider: OpenAI API integration (GPT-4, GPT-3.5)
    - AnthropicProvider: Anthropic API integration (Claude)
    - GoogleProvider: Google Gemini API integration

Adding New Provider:
    1. Create new file: providers/my_provider.py
    2. Create class: MyProvider(LLMProvider)
    3. Implement all abstract methods
    4. Import here for easy access
"""

# Import all provider implementations
from .ollama_provider import OllamaProvider

# Future providers (templates provided)
# from .openai_provider import OpenAIProvider
# from .anthropic_provider import AnthropicProvider
# from .google_provider import GoogleProvider

# Export all providers
__all__ = [
    'OllamaProvider',
    # 'OpenAIProvider',
    # 'AnthropicProvider',
    # 'GoogleProvider',
]
