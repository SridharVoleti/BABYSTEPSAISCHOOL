"""
LLM Provider Factory

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Factory pattern for creating LLM provider instances.
    Enables easy switching between providers via configuration.

Design Pattern:
    - Factory Pattern: Centralized object creation
    - Singleton Pattern: Single provider instance per process
    - Strategy Pattern: Different providers are interchangeable

Usage:
    from services.llm_service import get_llm_provider
    
    # Get configured provider (reads from settings)
    llm = get_llm_provider()
    
    # Or specify provider explicitly
    llm = get_llm_provider(provider_name='openai')
"""

# Python standard library
import logging
from typing import Optional

# Django imports
from django.conf import settings

# Local imports
from .base import LLMProvider, LLMError
from .providers.ollama_provider import OllamaProvider

# Configure logging
logger = logging.getLogger(__name__)

# Singleton instance
_provider_instance: Optional[LLMProvider] = None


class LLMFactory:
    """
    Factory for creating LLM provider instances.
    
    Purpose:
        Centralize provider creation logic.
        Handle configuration and initialization.
        Provide singleton access to provider.
    
    Supported Providers:
        - ollama: Local Ollama models (default)
        - openai: OpenAI GPT models
        - anthropic: Anthropic Claude models
        - google: Google Gemini models
    
    Configuration:
        Set in Django settings.py:
        
        LLM_PROVIDER = 'ollama'  # or 'openai', 'anthropic', 'google'
        LLM_CONFIG = {
            'model_name': 'llama3.2',
            'base_url': 'http://127.0.0.1:11434',
            'timeout': 120,
            # Provider-specific settings
        }
    """
    
    # Map provider names to classes
    PROVIDERS = {
        'ollama': OllamaProvider,
        # Future providers (uncomment when implemented):
        # 'openai': OpenAIProvider,
        # 'anthropic': AnthropicProvider,
        # 'google': GoogleProvider,
    }
    
    @classmethod
    def create_provider(
        cls,
        provider_name: Optional[str] = None,
        **config
    ) -> LLMProvider:
        """
        Create LLM provider instance.
        
        Purpose:
            Factory method to create appropriate provider.
            Reads configuration from Django settings if not provided.
        
        Args:
            provider_name: Name of provider ('ollama', 'openai', etc.)
                          If None, reads from settings.LLM_PROVIDER
            **config: Provider configuration
                     If empty, reads from settings.LLM_CONFIG
        
        Returns:
            LLMProvider: Configured provider instance
        
        Raises:
            LLMError: If provider is not supported or configuration is invalid
        
        Example:
            # Use configured provider
            llm = LLMFactory.create_provider()
            
            # Use specific provider with custom config
            llm = LLMFactory.create_provider(
                provider_name='ollama',
                model_name='mistral',
                base_url='http://localhost:11434'
            )
        """
        # Get provider name from settings if not specified
        if provider_name is None:
            provider_name = getattr(settings, 'LLM_PROVIDER', 'ollama')
        
        # Normalize provider name
        provider_name = provider_name.lower().strip()
        
        # Get provider class
        provider_class = cls.PROVIDERS.get(provider_name)
        
        if provider_class is None:
            # Provider not supported
            available = ', '.join(cls.PROVIDERS.keys())
            raise LLMError(
                f"Unsupported LLM provider: {provider_name}. "
                f"Available providers: {available}",
                provider=provider_name
            )
        
        # Get configuration from settings if not provided
        if not config:
            config = getattr(settings, 'LLM_CONFIG', {})
        
        # Log provider creation
        logger.info(
            f"Creating LLM provider: {provider_name} "
            f"with config: {cls._safe_config_repr(config)}"
        )
        
        try:
            # Create provider instance
            provider = provider_class(**config)
            
            # Verify provider is healthy
            if not provider.health_check():
                logger.warning(
                    f"LLM provider {provider_name} created but health check failed. "
                    "Service may be unavailable."
                )
            
            return provider
        
        except Exception as e:
            # Provider creation failed
            logger.error(
                f"Failed to create LLM provider {provider_name}: {e}",
                exc_info=True
            )
            raise LLMError(
                f"Failed to initialize {provider_name} provider: {str(e)}",
                provider=provider_name,
                original_error=e
            )
    
    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        use_singleton: bool = True
    ) -> LLMProvider:
        """
        Get LLM provider instance (singleton by default).
        
        Purpose:
            Get provider instance with optional singleton pattern.
            Reuses instance across requests for efficiency.
        
        Args:
            provider_name: Provider name (None = use configured)
            use_singleton: Whether to use singleton pattern (default: True)
        
        Returns:
            LLMProvider: Provider instance
        
        Example:
            # Get singleton instance (recommended)
            llm = LLMFactory.get_provider()
            
            # Create new instance
            llm = LLMFactory.get_provider(use_singleton=False)
        """
        global _provider_instance
        
        # If singleton requested and instance exists, return it
        if use_singleton and _provider_instance is not None:
            # Verify it's the right provider
            configured_provider = provider_name or getattr(
                settings, 'LLM_PROVIDER', 'ollama'
            )
            
            # Check if provider type matches
            expected_class = cls.PROVIDERS.get(configured_provider.lower())
            if isinstance(_provider_instance, expected_class):
                return _provider_instance
            else:
                # Provider changed, recreate
                logger.info(
                    f"Provider changed from {type(_provider_instance).__name__} "
                    f"to {configured_provider}, recreating instance"
                )
                _provider_instance = None
        
        # Create new instance
        provider = cls.create_provider(provider_name=provider_name)
        
        # Store as singleton if requested
        if use_singleton:
            _provider_instance = provider
        
        return provider
    
    @staticmethod
    def _safe_config_repr(config: dict) -> dict:
        """
        Create safe representation of config (hide API keys).
        
        Purpose:
            Prevent logging sensitive information like API keys.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            dict: Safe config with sensitive fields masked
        """
        # Copy config
        safe_config = config.copy()
        
        # Mask sensitive fields
        sensitive_fields = ['api_key', 'password', 'secret', 'token']
        for field in sensitive_fields:
            if field in safe_config:
                safe_config[field] = '***REDACTED***'
        
        return safe_config


def get_llm_provider(
    provider_name: Optional[str] = None,
    use_singleton: bool = True
) -> LLMProvider:
    """
    Get LLM provider instance (convenience function).
    
    Purpose:
        Main public API for getting LLM provider.
        Simple wrapper around LLMFactory.get_provider().
    
    Args:
        provider_name: Provider name (None = use configured)
        use_singleton: Whether to use singleton pattern (default: True)
    
    Returns:
        LLMProvider: Configured provider instance
    
    Example:
        from services.llm_service import get_llm_provider
        
        llm = get_llm_provider()
        response = llm.chat(
            message="What is photosynthesis?",
            system_prompt="You are a science teacher"
        )
        print(response.text)
    """
    return LLMFactory.get_provider(
        provider_name=provider_name,
        use_singleton=use_singleton
    )
