"""
LLM Provider Base Classes and Interfaces

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Define abstract base class and interfaces for LLM providers.
    All LLM providers (Ollama, OpenAI, Anthropic, etc.) must implement this interface.

Design Pattern:
    - Abstract Base Class: Defines contract for all providers
    - Dependency Inversion Principle: Application depends on abstraction, not concrete providers
    - Strategy Pattern: Different providers are interchangeable strategies

Usage:
    # Creating a custom provider
    class MyLLMProvider(LLMProvider):
        def chat(self, message, system_prompt=None, **kwargs):
            # Implementation here
            pass
        
        def health_check(self):
            # Implementation here
            pass
"""

# Python standard library
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class LLMResponse:
    """
    Standardized LLM response structure.
    
    Purpose:
        Provide consistent response format across all LLM providers.
        Makes it easy to switch providers without changing application code.
    
    Attributes:
        text: Generated text response
        model: Name of the model used
        tokens_used: Approximate token count (if available)
        latency_ms: Response generation time in milliseconds
        metadata: Provider-specific metadata
        timestamp: When response was generated
        success: Whether the request succeeded
        error: Error message if success=False
    """
    
    # The generated text response
    text: str
    
    # Model name used for generation
    model: str
    
    # Number of tokens used (None if not available)
    tokens_used: Optional[int] = None
    
    # Response latency in milliseconds
    latency_ms: Optional[float] = None
    
    # Additional provider-specific metadata
    metadata: Dict[str, Any] = None
    
    # Timestamp of response generation
    timestamp: datetime = None
    
    # Success flag
    success: bool = True
    
    # Error message if success=False
    error: Optional[str] = None
    
    def __post_init__(self):
        """
        Initialize fields after dataclass creation.
        
        Purpose:
            Set default values for mutable fields.
            Ensure timestamp is set.
        """
        # Set default empty dict for metadata if not provided
        if self.metadata is None:
            self.metadata = {}
        
        # Set timestamp to now if not provided
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LLMError(Exception):
    """
    Base exception for LLM-related errors.
    
    Purpose:
        Provide consistent error handling across all LLM providers.
        Makes it easy to catch all LLM errors with single except clause.
    
    Usage:
        try:
            response = llm.chat(message)
        except LLMError as e:
            logger.error(f"LLM error: {e}")
    """
    
    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        """
        Initialize LLM error.
        
        Args:
            message: Error message
            provider: Name of LLM provider that raised error
            original_error: Original exception if this wraps another error
        """
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    Purpose:
        Define interface that all LLM providers must implement.
        Ensures consistent API across Ollama, OpenAI, Anthropic, etc.
    
    Design Principles:
        - Abstract Base Class: Cannot be instantiated directly
        - Template Method: Defines algorithm structure, subclasses fill in details
        - Open/Closed: Open for extension, closed for modification
    
    Subclasses Must Implement:
        - chat(): Generate chat response
        - health_check(): Check if provider is available
        - get_available_models(): List available models
    
    Subclasses May Override:
        - __init__(): Custom initialization
        - _validate_parameters(): Custom parameter validation
    """
    
    def __init__(self, model_name: str, base_url: str = None, api_key: str = None, **kwargs):
        """
        Initialize LLM provider.
        
        Args:
            model_name: Name of the model to use
            base_url: Base URL for API endpoint (provider-specific)
            api_key: API key for authentication (if required)
            **kwargs: Additional provider-specific configuration
        
        Note:
            Subclasses should call super().__init__() and add their own initialization.
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion response.
        
        Purpose:
            Main method for generating AI responses.
            Must be implemented by all providers.
        
        Args:
            message: User message/prompt
            system_prompt: System prompt to set context (optional)
            temperature: Randomness of response (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response (None = provider default)
            **kwargs: Provider-specific parameters
        
        Returns:
            LLMResponse: Standardized response object
        
        Raises:
            LLMError: If generation fails
        
        Example:
            response = provider.chat(
                message="What is photosynthesis?",
                system_prompt="You are a science teacher for grade 5",
                temperature=0.7
            )
            print(response.text)
        """
        pass
    
    @abstractmethod
    def health_check(self, force: bool = False) -> bool:
        """
        Check if LLM provider is available and healthy.
        
        Purpose:
            Verify that the provider can accept requests.
            Used for service health monitoring.
        
        Args:
            force: Force fresh check (ignore cache)
        
        Returns:
            bool: True if provider is healthy, False otherwise
        
        Example:
            if provider.health_check():
                response = provider.chat(message)
            else:
                # Use fallback or show error
                pass
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from this provider.
        
        Purpose:
            Allow dynamic model selection.
            Useful for admin interfaces and configuration.
        
        Returns:
            List[str]: List of model names
        
        Example:
            models = provider.get_available_models()
            # ['llama3.2', 'mistral', 'codellama']
        """
        pass
    
    def _validate_parameters(self, **kwargs) -> None:
        """
        Validate parameters before making request.
        
        Purpose:
            Catch invalid parameters early.
            Provide helpful error messages.
        
        Args:
            **kwargs: Parameters to validate
        
        Raises:
            ValueError: If parameters are invalid
        
        Note:
            Subclasses can override to add custom validation.
        """
        # Validate temperature
        if 'temperature' in kwargs:
            temp = kwargs['temperature']
            if not 0.0 <= temp <= 2.0:
                raise ValueError(f"Temperature must be between 0.0 and 2.0, got {temp}")
        
        # Validate max_tokens
        if 'max_tokens' in kwargs and kwargs['max_tokens'] is not None:
            if kwargs['max_tokens'] <= 0:
                raise ValueError(f"max_tokens must be positive, got {kwargs['max_tokens']}")
    
    def __repr__(self) -> str:
        """
        String representation of provider.
        
        Returns:
            str: Provider description
        """
        return f"{self.__class__.__name__}(model={self.model_name})"


# Future: Add streaming support
class StreamingLLMProvider(LLMProvider):
    """
    Abstract base class for LLM providers that support streaming.
    
    Purpose:
        Define interface for streaming chat responses.
        Allows real-time display of generated text.
    
    Note:
        This is a future enhancement. Not all providers need to implement this.
    """
    
    @abstractmethod
    async def chat_stream(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate streaming chat completion.
        
        Purpose:
            Stream response tokens as they're generated.
            Provides better UX for long responses.
        
        Args:
            message: User message/prompt
            system_prompt: System prompt (optional)
            temperature: Response randomness
            **kwargs: Provider-specific parameters
        
        Yields:
            str: Response chunks as they're generated
        
        Example:
            async for chunk in provider.chat_stream(message):
                print(chunk, end='', flush=True)
        """
        pass
