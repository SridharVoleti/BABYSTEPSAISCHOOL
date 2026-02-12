"""
Ollama LLM Provider Implementation

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Concrete implementation of LLMProvider for Ollama.
    Wraps the existing robust OllamaClient to provide standardized interface.

Features:
    - Connection pooling
    - Retry logic
    - Circuit breaker pattern
    - Health check caching
    - Automatic error recovery

Usage:
    from services.llm_service import get_llm_provider
    
    llm = get_llm_provider()  # Returns OllamaProvider if configured
    response = llm.chat(message="Hello", system_prompt="You are helpful")
"""

# Python standard library
import time
import logging
from typing import List, Optional

# Local imports
from ..base import LLMProvider, LLMResponse, LLMError

# Import existing Ollama client
from services.mentor_chat_service.ollama_client import OllamaClient

# Configure logging
logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider implementation.
    
    Purpose:
        Provide standardized LLM interface for Ollama models.
        Wraps existing robust OllamaClient with circuit breaker and retry logic.
    
    Features:
        - Supports all Ollama models (llama3.2, mistral, codellama, etc.)
        - Built-in connection pooling
        - Automatic retry on failure
        - Circuit breaker pattern
        - Health check caching
    
    Configuration:
        base_url: Ollama server URL (default: http://127.0.0.1:11434)
        model_name: Model to use (default: llama3.2)
        timeout: Request timeout in seconds (default: 120)
        max_retries: Maximum retry attempts (default: 3)
    """
    
    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        timeout: int = 120,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model_name: Ollama model name (llama3.2, mistral, etc.)
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration
        """
        # Call parent constructor
        super().__init__(
            model_name=model_name,
            base_url=base_url,
            api_key=None,  # Ollama doesn't use API keys
            **kwargs
        )
        
        # Store timeout and retry settings
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create underlying Ollama client
        # Reuses existing robust implementation with circuit breaker
        self.client = OllamaClient(
            base_url=base_url,
            model=model_name,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Log initialization
        logger.info(
            f"OllamaProvider initialized: model={model_name}, "
            f"base_url={base_url}, timeout={timeout}s"
        )
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion using Ollama.
        
        Purpose:
            Generate AI response using Ollama model.
            Handles errors and provides standardized response format.
        
        Args:
            message: User message/prompt
            system_prompt: System prompt for context (optional)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum response tokens (None = unlimited)
            **kwargs: Additional Ollama-specific parameters
        
        Returns:
            LLMResponse: Standardized response with text, metadata, timing
        
        Raises:
            LLMError: If generation fails after retries
        
        Example:
            response = provider.chat(
                message="Explain photosynthesis",
                system_prompt="You are a grade 5 teacher",
                temperature=0.7
            )
            print(response.text)
            print(f"Generated in {response.latency_ms}ms")
        """
        # Validate parameters
        self._validate_parameters(
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Record start time for latency measurement
        start_time = time.time()
        
        try:
            # Call underlying Ollama client
            # This already has retry logic and circuit breaker
            response_text = self.client.chat(
                message=message,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Create standardized response
            return LLMResponse(
                text=response_text,
                model=self.model_name,
                tokens_used=None,  # Ollama doesn't provide token counts
                latency_ms=latency_ms,
                metadata={
                    'provider': 'ollama',
                    'base_url': self.base_url,
                    'temperature': temperature,
                    'circuit_breaker_state': self.client.circuit_breaker.state
                },
                success=True,
                error=None
            )
        
        except Exception as e:
            # Calculate latency even on failure
            latency_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Ollama chat failed: {e}",
                exc_info=True,
                extra={
                    'model': self.model_name,
                    'message_length': len(message),
                    'latency_ms': latency_ms
                }
            )
            
            # Raise standardized error
            raise LLMError(
                message=f"Ollama generation failed: {str(e)}",
                provider="ollama",
                original_error=e
            )
    
    def health_check(self, force: bool = False) -> bool:
        """
        Check if Ollama service is healthy.
        
        Purpose:
            Verify Ollama is running and model is available.
            Uses caching to avoid excessive health checks.
        
        Args:
            force: Force fresh check (ignore cache)
        
        Returns:
            bool: True if healthy, False otherwise
        
        Example:
            if provider.health_check():
                response = provider.chat(message)
            else:
                logger.error("Ollama is down!")
        """
        try:
            # Use underlying client's health check
            # This already has caching and circuit breaker
            is_healthy = self.client.health_check(force=force)
            
            # Log health status
            if force:
                logger.info(
                    f"Ollama health check: {'healthy' if is_healthy else 'unhealthy'} "
                    f"(model={self.model_name})"
                )
            
            return is_healthy
        
        except Exception as e:
            # Log error
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models.
        
        Purpose:
            Query Ollama for installed models.
            Useful for dynamic model selection.
        
        Returns:
            List[str]: List of model names
        
        Example:
            models = provider.get_available_models()
            # ['llama3.2:latest', 'mistral:latest', 'codellama:latest']
        """
        try:
            # Call Ollama API to get models
            import requests
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            # Log result
            logger.debug(f"Found {len(models)} Ollama models: {models}")
            
            return models
        
        except Exception as e:
            # Log error
            logger.error(f"Failed to get Ollama models: {e}")
            
            # Return empty list on error
            return []
    
    def _validate_parameters(self, **kwargs) -> None:
        """
        Validate Ollama-specific parameters.
        
        Purpose:
            Add Ollama-specific validation on top of base validation.
        
        Args:
            **kwargs: Parameters to validate
        
        Raises:
            ValueError: If parameters are invalid
        """
        # Call parent validation
        super()._validate_parameters(**kwargs)
        
        # Add Ollama-specific validation if needed
        # Currently no additional validation required
        pass
    
    def get_circuit_breaker_state(self) -> str:
        """
        Get current circuit breaker state.
        
        Purpose:
            Expose circuit breaker state for monitoring.
            Useful for debugging and health dashboards.
        
        Returns:
            str: Circuit breaker state ('closed', 'open', 'half_open')
        
        Example:
            state = provider.get_circuit_breaker_state()
            if state == 'open':
                logger.warning("Circuit breaker is open - service degraded")
        """
        return self.client.circuit_breaker.state
    
    def reset_circuit_breaker(self) -> None:
        """
        Reset circuit breaker to closed state.
        
        Purpose:
            Manually reset circuit breaker after fixing issues.
            Useful for administrative recovery actions.
        
        Example:
            # After fixing Ollama server
            provider.reset_circuit_breaker()
            # Circuit breaker is now closed, requests will be attempted
        """
        self.client.circuit_breaker.state = 'closed'
        self.client.circuit_breaker.failure_count = 0
        logger.info("Circuit breaker manually reset to closed state")
