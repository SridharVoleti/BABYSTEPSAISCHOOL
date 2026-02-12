"""
LLM Service Package

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Generic LLM provider abstraction layer for the BabySteps platform.
    Enables easy switching between different LLM providers (Ollama, OpenAI, Anthropic, etc.)
    without changing application code.

Design Pattern:
    - Strategy Pattern: Different LLM providers are interchangeable strategies
    - Factory Pattern: LLMFactory creates appropriate provider instances
    - Dependency Inversion: Application depends on abstract LLMProvider, not concrete implementations

Usage:
    from services.llm_service import get_llm_provider
    
    llm = get_llm_provider()  # Uses configured provider
    response = llm.chat(message="Hello", system_prompt="You are a teacher")

Supported Providers:
    - Ollama (llama3.2, mistral, etc.) - Default
    - OpenAI (gpt-4, gpt-3.5-turbo) - Template provided
    - Anthropic (claude-3, claude-2) - Template provided
    - Google (gemini-pro) - Template provided
    
Adding New Provider:
    1. Create new class inheriting from LLMProvider
    2. Implement all abstract methods
    3. Add to LLMFactory.create_provider()
    4. Update settings.LLM_PROVIDER
"""

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "BabySteps Development Team"
__email__ = "dev@babystepsdigitalschool.com"

# Default Django app configuration
# This points to the AppConfig class in apps.py
default_app_config = 'services.llm_service.apps.LLMServiceConfig'

# Public API exports
# Applications should only import from this __init__.py
from .factory import get_llm_provider, LLMFactory
from .base import LLMProvider, LLMResponse, LLMError

__all__ = [
    'get_llm_provider',  # Main function to get LLM instance
    'LLMFactory',         # Factory class for advanced usage
    'LLMProvider',        # Base class for creating custom providers
    'LLMResponse',        # Response data structure
    'LLMError',          # Exception class for LLM errors
]
