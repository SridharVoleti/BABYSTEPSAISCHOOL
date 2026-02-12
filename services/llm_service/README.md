**# LLM Service - Provider Abstraction Layer**

**Date**: 2025-12-11  
**Version**: 1.0.0  
**Author**: BabySteps Development Team

---

## 🎯 Purpose

The LLM Service provides a **plug-and-play abstraction layer** for Large Language Model providers. This allows you to easily switch between different LLM providers (Ollama, OpenAI, Anthropic, Google, etc.) **without changing any application code**.

### Problem Solved
- **Vendor Lock-in**: No longer tied to a single LLM provider
- **Easy Migration**: Switch providers with just configuration changes
- **Testing**: Easy to mock LLM calls for testing
- **Cost Optimization**: Compare costs across providers
- **Redundancy**: Fall back to alternative providers if one fails

---

## 🏗️ Architecture

### Design Patterns

1. **Strategy Pattern**: Different LLM providers are interchangeable strategies
2. **Factory Pattern**: `LLMFactory` creates appropriate provider instances
3. **Dependency Inversion**: Application depends on `LLMProvider` interface, not concrete implementations
4. **Singleton Pattern**: Single provider instance per process (optional)

### Class Structure

```
LLMProvider (Abstract Base Class)
├── OllamaProvider (Ollama models: llama3.2, mistral, etc.)
├── OpenAIProvider (GPT-4, GPT-3.5-turbo)
├── AnthropicProvider (Claude 3, Claude 2)
└── GoogleProvider (Gemini Pro, Gemini Ultra)
```

---

## 🚀 Quick Start

### Basic Usage

```python
from services.llm_service import get_llm_provider

# Get configured provider (reads from settings.py)
llm = get_llm_provider()

# Generate response
response = llm.chat(
    message="What is photosynthesis?",
    system_prompt="You are a science teacher for grade 5",
    temperature=0.7
)

print(response.text)
print(f"Generated in {response.latency_ms}ms using {response.model}")
```

### Current Implementation (Ollama)

```python
# Uses Ollama by default
llm = get_llm_provider()

# Make a request
response = llm.chat(
    message="Explain gravity simply",
    system_prompt="You are a teacher",
    temperature=0.7
)

print(response.text)
# Generated text from llama3.2
```

---

## ⚙️ Configuration

### Django Settings (settings.py)

Add to your `settings.py`:

```python
# LLM Provider Configuration
# 2025-12-11: Generic LLM provider abstraction

# Which provider to use: 'ollama', 'openai', 'anthropic', 'google'
LLM_PROVIDER = 'ollama'

# Provider-specific configuration
LLM_CONFIG = {
    # Ollama configuration
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
    'timeout': 120,
    'max_retries': 3,
}

# Alternative: OpenAI configuration
# LLM_PROVIDER = 'openai'
# LLM_CONFIG = {
#     'model_name': 'gpt-3.5-turbo',
#     'api_key': 'your-api-key-here',  # Or set OPENAI_API_KEY env var
#     'timeout': 60,
# }

# Alternative: Anthropic configuration
# LLM_PROVIDER = 'anthropic'
# LLM_CONFIG = {
#     'model_name': 'claude-3-sonnet-20240229',
#     'api_key': 'your-api-key-here',  # Or set ANTHROPIC_API_KEY env var
#     'timeout': 60,
# }
```

---

## 🔄 Switching Providers

### From Ollama to OpenAI

**Before (Ollama)**:
```python
# settings.py
LLM_PROVIDER = 'ollama'
LLM_CONFIG = {
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
}
```

**After (OpenAI)** - **NO CODE CHANGES NEEDED**:
```python
# settings.py
LLM_PROVIDER = 'openai'
LLM_CONFIG = {
    'model_name': 'gpt-4',
    'api_key': 'your-openai-key',
}
```

**Application code stays the same**:
```python
# This works with any provider
llm = get_llm_provider()
response = llm.chat(message="Hello")
```

---

## 📦 Supported Providers

### 1. Ollama (Default) ✅ **IMPLEMENTED**

**Status**: Fully implemented and tested  
**Models**: llama3.2, mistral, codellama, etc.  
**Cost**: Free (self-hosted)  
**Setup**: Install Ollama locally

```python
LLM_PROVIDER = 'ollama'
LLM_CONFIG = {
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
    'timeout': 120,
}
```

### 2. OpenAI 📝 **TEMPLATE PROVIDED**

**Status**: Template implementation ready  
**Models**: GPT-4, GPT-3.5-turbo, GPT-4-turbo  
**Cost**: Pay-per-token  
**Setup**: Get API key from OpenAI

```bash
# Install OpenAI SDK
pip install openai

# Uncomment in providers/__init__.py
from .openai_provider import OpenAIProvider
```

```python
LLM_PROVIDER = 'openai'
LLM_CONFIG = {
    'model_name': 'gpt-4',
    'api_key': 'sk-...',  # Or set OPENAI_API_KEY env var
}
```

### 3. Anthropic (Claude) 📝 **TEMPLATE PROVIDED**

**Status**: Template implementation ready  
**Models**: Claude 3 Opus, Sonnet, Haiku  
**Cost**: Pay-per-token  
**Setup**: Get API key from Anthropic

```bash
# Install Anthropic SDK
pip install anthropic

# Uncomment in providers/__init__.py
from .anthropic_provider import AnthropicProvider
```

```python
LLM_PROVIDER = 'anthropic'
LLM_CONFIG = {
    'model_name': 'claude-3-sonnet-20240229',
    'api_key': 'sk-ant-...',  # Or set ANTHROPIC_API_KEY env var
}
```

### 4. Google (Gemini) 🔮 **FUTURE**

**Status**: Not yet implemented  
**Models**: Gemini Pro, Gemini Ultra  
**Cost**: Free tier available, then pay-per-token

---

## 🛠️ Adding a New Provider

### Step-by-Step Guide

#### Step 1: Create Provider Class

Create `services/llm_service/providers/my_provider.py`:

```python
from ..base import LLMProvider, LLMResponse, LLMError

class MyProvider(LLMProvider):
    def __init__(self, model_name='my-model', **kwargs):
        super().__init__(model_name=model_name, **kwargs)
        # Initialize your provider client here
    
    def chat(self, message, system_prompt=None, temperature=0.7, **kwargs):
        # Implement chat logic
        # Must return LLMResponse object
        return LLMResponse(
            text="Generated response",
            model=self.model_name,
            success=True
        )
    
    def health_check(self, force=False):
        # Check if provider is available
        return True
    
    def get_available_models(self):
        # Return list of available models
        return ['my-model-1', 'my-model-2']
```

#### Step 2: Register Provider

Update `services/llm_service/providers/__init__.py`:

```python
from .my_provider import MyProvider

__all__ = [
    'OllamaProvider',
    'MyProvider',  # Add your provider
]
```

#### Step 3: Add to Factory

Update `services/llm_service/factory.py`:

```python
from .providers.my_provider import MyProvider

class LLMFactory:
    PROVIDERS = {
        'ollama': OllamaProvider,
        'my_provider': MyProvider,  # Add here
    }
```

#### Step 4: Configure and Use

Update `settings.py`:

```python
LLM_PROVIDER = 'my_provider'
LLM_CONFIG = {
    'model_name': 'my-model-1',
    # Your provider-specific config
}
```

**That's it!** Your provider is now available:

```python
llm = get_llm_provider()  # Returns MyProvider
response = llm.chat(message="Hello")
```

---

## 📖 API Reference

### LLMProvider (Base Class)

All providers implement this interface:

#### `chat(message, system_prompt=None, temperature=0.7, max_tokens=None, **kwargs)`

Generate chat completion.

**Args:**
- `message` (str): User message/prompt
- `system_prompt` (str, optional): System prompt for context
- `temperature` (float): Response randomness (0.0 = deterministic, 2.0 = very random)
- `max_tokens` (int, optional): Maximum response length
- `**kwargs`: Provider-specific parameters

**Returns:**
- `LLMResponse`: Response object with text, metadata, timing

**Raises:**
- `LLMError`: If generation fails

**Example:**
```python
response = llm.chat(
    message="What is AI?",
    system_prompt="You are a teacher",
    temperature=0.7,
    max_tokens=500
)
```

#### `health_check(force=False)`

Check if provider is available.

**Args:**
- `force` (bool): Force fresh check (ignore cache)

**Returns:**
- `bool`: True if healthy, False otherwise

**Example:**
```python
if llm.health_check():
    response = llm.chat(message="Hello")
else:
    # Handle offline provider
    pass
```

#### `get_available_models()`

Get list of available models.

**Returns:**
- `List[str]`: Model names

**Example:**
```python
models = llm.get_available_models()
# ['llama3.2', 'mistral', 'codellama']
```

### LLMResponse

Standardized response object:

**Attributes:**
- `text` (str): Generated text
- `model` (str): Model name used
- `tokens_used` (int, optional): Token count
- `latency_ms` (float, optional): Generation time in milliseconds
- `metadata` (dict): Provider-specific metadata
- `timestamp` (datetime): When generated
- `success` (bool): Whether request succeeded
- `error` (str, optional): Error message if failed

**Example:**
```python
response = llm.chat(message="Hello")
print(response.text)           # "Hello! How can I help you?"
print(response.model)          # "llama3.2"
print(response.latency_ms)     # 1234.56
print(response.success)        # True
```

### LLMError

Exception raised on LLM errors:

**Attributes:**
- `message` (str): Error description
- `provider` (str): Provider name
- `original_error` (Exception): Original exception

**Example:**
```python
try:
    response = llm.chat(message="Hello")
except LLMError as e:
    print(f"Provider {e.provider} failed: {e}")
```

---

## 🧪 Testing

### Mocking LLM Calls

```python
from unittest.mock import Mock, patch
from services.llm_service import get_llm_provider
from services.llm_service.base import LLMResponse

def test_my_feature():
    # Create mock LLM
    mock_llm = Mock()
    mock_llm.chat.return_value = LLMResponse(
        text="Mocked response",
        model="test-model",
        success=True
    )
    
    # Patch provider
    with patch('services.llm_service.get_llm_provider', return_value=mock_llm):
        # Your test code here
        llm = get_llm_provider()
        response = llm.chat(message="Test")
        assert response.text == "Mocked response"
```

### Integration Testing

```python
def test_ollama_integration():
    # Get real provider
    llm = get_llm_provider()
    
    # Check health
    assert llm.health_check(), "Ollama not running"
    
    # Test chat
    response = llm.chat(
        message="Say hello",
        temperature=0.1  # Low temperature for consistency
    )
    
    assert response.success
    assert len(response.text) > 0
    assert response.model == 'llama3.2'
```

---

## 📊 Monitoring & Observability

### Response Metadata

Every response includes metadata for monitoring:

```python
response = llm.chat(message="Hello")

print(response.metadata)
# {
#     'provider': 'ollama',
#     'base_url': 'http://127.0.0.1:11434',
#     'temperature': 0.7,
#     'circuit_breaker_state': 'closed'
# }
```

### Logging

All providers log important events:

```python
import logging

# Enable debug logging
logging.getLogger('services.llm_service').setLevel(logging.DEBUG)

# Logs will show:
# - Provider initialization
# - Health check results
# - Request/response timing
# - Errors and retries
```

### Circuit Breaker (Ollama Only)

Ollama provider includes circuit breaker for resilience:

```python
from services.llm_service import get_llm_provider

llm = get_llm_provider()

# Check circuit breaker state
if hasattr(llm, 'get_circuit_breaker_state'):
    state = llm.get_circuit_breaker_state()
    # 'closed' = healthy, 'open' = degraded, 'half_open' = recovering
    
    if state == 'open':
        # Circuit breaker tripped, service degraded
        logger.warning("LLM circuit breaker is open")
```

---

## 🔒 Security Best Practices

### API Key Management

**❌ DON'T** hardcode API keys:
```python
# BAD - API key in code
LLM_CONFIG = {
    'api_key': 'sk-1234567890abcdef'  # NEVER DO THIS
}
```

**✅ DO** use environment variables:
```python
# GOOD - API key from environment
import os

LLM_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY')
}
```

**✅ DO** use Django settings:
```python
# settings.py
from decouple import config  # pip install python-decouple

LLM_CONFIG = {
    'api_key': config('OPENAI_API_KEY', default=None)
}
```

### Production Checklist

- [ ] API keys stored in environment variables
- [ ] Timeouts configured appropriately
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Health checks monitoring
- [ ] Rate limiting implemented (if needed)
- [ ] Cost monitoring in place (for paid APIs)

---

## 💡 Migration Examples

### Migrating from Direct Ollama Usage

**Before**:
```python
# mentor_chat_service/views.py
from .ollama_client import ollama_client

response_text = ollama_client.chat(
    message=message,
    system_prompt=system_prompt
)
```

**After**:
```python
# mentor_chat_service/views.py
from services.llm_service import get_llm_provider

llm = get_llm_provider()
response = llm.chat(
    message=message,
    system_prompt=system_prompt
)
response_text = response.text
```

### Benefits of Migration

1. **Provider Independence**: Easy to switch from Ollama to OpenAI
2. **Consistent Interface**: Same code works with all providers
3. **Better Testing**: Easy to mock LLM calls
4. **Metadata**: Access to timing, token counts, etc.
5. **Error Handling**: Standardized error handling

---

## 🚧 Roadmap

### Version 1.0 (Current) ✅
- [x] Abstract base class
- [x] Ollama provider implementation
- [x] Factory pattern
- [x] OpenAI template
- [x] Anthropic template
- [x] Documentation

### Version 1.1 (Planned)
- [ ] Streaming support
- [ ] Async/await support
- [ ] Response caching
- [ ] Google Gemini provider
- [ ] Cost tracking

### Version 2.0 (Future)
- [ ] Multi-provider fallback
- [ ] A/B testing support
- [ ] Automatic provider selection
- [ ] Load balancing across providers
- [ ] Prompt templates library

---

## 📞 Support

For issues or questions:
- Check this documentation
- Review provider templates
- Check application logs
- Contact: dev@babystepsdigitalschool.com

---

**Status**: ✅ Production Ready  
**Tested With**: Ollama (llama3.2)  
**Last Updated**: 2025-12-11
