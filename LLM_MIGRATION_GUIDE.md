# LLM Provider - Plug & Play Migration Guide

**Date**: 2025-12-11  
**Purpose**: Simple guide to switch LLM providers without code changes

---

## 🎯 Overview

Your BabySteps platform now has a **plug-and-play LLM abstraction layer**. This means you can switch between different AI providers (Ollama, OpenAI, Claude, etc.) by **just changing configuration** - no code changes needed!

---

## ✅ Current Status

**Active Provider**: Ollama (llama3.2)  
**Architecture**: Abstraction layer implemented  
**Migration Status**: Ready for any provider switch

---

## 🔄 How to Switch Providers

### Option 1: Stay with Ollama (Current)

**No changes needed!** Already configured and working.

```python
# backend/settings.py (current)
LLM_PROVIDER = 'ollama'
LLM_CONFIG = {
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
}
```

### Option 2: Switch to OpenAI (GPT-4)

**Step 1**: Install OpenAI SDK
```bash
pip install openai
```

**Step 2**: Get API Key
- Sign up at https://platform.openai.com
- Create API key
- Set environment variable: `OPENAI_API_KEY=your-key`

**Step 3**: Update Settings
```python
# backend/settings.py
LLM_PROVIDER = 'openai'  # Changed from 'ollama'
LLM_CONFIG = {
    'model_name': 'gpt-4',  # or 'gpt-3.5-turbo' for lower cost
    'api_key': os.getenv('OPENAI_API_KEY'),
    'timeout': 60,
}
```

**Step 4**: Uncomment Provider
```python
# services/llm_service/providers/openai_provider.py
# Uncomment the entire file (remove triple quotes)

# services/llm_service/providers/__init__.py
from .openai_provider import OpenAIProvider  # Uncomment this line
```

**That's it!** All your AI features now use GPT-4 instead of Ollama.

### Option 3: Switch to Anthropic (Claude)

**Step 1**: Install Anthropic SDK
```bash
pip install anthropic
```

**Step 2**: Get API Key
- Sign up at https://console.anthropic.com
- Create API key
- Set environment variable: `ANTHROPIC_API_KEY=your-key`

**Step 3**: Update Settings
```python
# backend/settings.py
LLM_PROVIDER = 'anthropic'  # Changed from 'ollama'
LLM_CONFIG = {
    'model_name': 'claude-3-sonnet-20240229',
    'api_key': os.getenv('ANTHROPIC_API_KEY'),
    'timeout': 60,
}
```

**Step 4**: Uncomment Provider
```python
# services/llm_service/providers/anthropic_provider.py
# Uncomment the entire file (remove triple quotes)

# services/llm_service/providers/__init__.py
from .anthropic_provider import AnthropicProvider  # Uncomment this line
```

**Done!** All AI features now use Claude.

---

## 🧪 Testing After Switch

After changing providers, test with:

```bash
# Test mentor chat (uses LLM)
python manage.py test tests.test_mentor_chat_api -v 2

# Test in Python shell
python manage.py shell
```

```python
from services.llm_service import get_llm_provider

# Get configured provider
llm = get_llm_provider()
print(f"Using: {llm}")

# Test health check
if llm.health_check():
    print("✅ Provider is healthy")
else:
    print("❌ Provider is not available")

# Test chat
response = llm.chat(
    message="What is 2+2?",
    system_prompt="You are a math teacher"
)
print(f"Response: {response.text}")
print(f"Model: {response.model}")
print(f"Latency: {response.latency_ms}ms")
```

---

## 💰 Cost Comparison

### Ollama (Current)
- **Cost**: FREE (self-hosted)
- **Speed**: Fast (local)
- **Privacy**: 100% private (no data sent outside)
- **Setup**: Requires local installation
- **Best for**: Development, privacy-sensitive applications

### OpenAI
- **Cost**: Pay-per-token
  - GPT-3.5-turbo: ~$0.002 per 1K tokens
  - GPT-4: ~$0.03 per 1K tokens
- **Speed**: Fast (API)
- **Privacy**: Data sent to OpenAI
- **Setup**: Just API key
- **Best for**: Production, highest quality responses

### Anthropic (Claude)
- **Cost**: Pay-per-token
  - Claude 3 Haiku: ~$0.0025 per 1K tokens
  - Claude 3 Sonnet: ~$0.015 per 1K tokens
  - Claude 3 Opus: ~$0.075 per 1K tokens
- **Speed**: Fast (API)
- **Privacy**: Data sent to Anthropic
- **Setup**: Just API key
- **Best for**: Long conversations, complex reasoning

---

## 🔐 Security Best Practices

### ❌ NEVER Do This
```python
# DON'T hardcode API keys
LLM_CONFIG = {
    'api_key': 'sk-1234567890'  # NEVER!
}
```

### ✅ ALWAYS Do This
```python
# DO use environment variables
import os

LLM_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY')
}
```

### Environment Variables Setup

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY = "your-key-here"
```

**Linux/Mac (Bash)**:
```bash
export OPENAI_API_KEY="your-key-here"
```

**Production (.env file)**:
```bash
# .env file
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-other-key
```

---

## 📊 Provider Comparison Matrix

| Feature | Ollama | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| **Cost** | Free | Paid | Paid |
| **Privacy** | 100% Private | Shared with provider | Shared with provider |
| **Setup** | Complex | Simple | Simple |
| **Speed** | Fast | Fast | Fast |
| **Quality** | Good | Excellent | Excellent |
| **Context Window** | 8K-128K | 4K-128K | 100K-200K |
| **Customization** | High | Low | Low |
| **Offline** | Yes | No | No |

---

## 🚀 Switching Strategy

### Development → Production Migration

**Phase 1: Development (Current)**
```python
LLM_PROVIDER = 'ollama'  # Free, private, fast iteration
```

**Phase 2: Testing**
```python
# Test with real provider
LLM_PROVIDER = 'openai'
LLM_CONFIG = {
    'model_name': 'gpt-3.5-turbo',  # Cheaper for testing
}
```

**Phase 3: Production**
```python
# Best quality for users
LLM_PROVIDER = 'openai'
LLM_CONFIG = {
    'model_name': 'gpt-4',  # or 'claude-3-sonnet-20240229'
}
```

### Multi-Provider Strategy

You can even support multiple providers:

```python
# settings.py
import os

# Use environment variable to choose provider
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')

# Provider-specific configs
OLLAMA_CONFIG = {
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
}

OPENAI_CONFIG = {
    'model_name': 'gpt-4',
    'api_key': os.getenv('OPENAI_API_KEY'),
}

# Select config based on provider
LLM_CONFIG = {
    'ollama': OLLAMA_CONFIG,
    'openai': OPENAI_CONFIG,
}.get(LLM_PROVIDER, OLLAMA_CONFIG)
```

Then switch providers with environment variable:
```bash
# Use Ollama
export LLM_PROVIDER=ollama

# Use OpenAI
export LLM_PROVIDER=openai
```

---

## 🐛 Troubleshooting

### Provider Not Available

**Error**: `LLMError: Unsupported LLM provider: xyz`

**Solution**: 
1. Check spelling in settings.py: `LLM_PROVIDER = 'ollama'` (not 'Ollama')
2. Ensure provider is uncommented in `providers/__init__.py`

### API Key Not Working

**Error**: `OpenAI API key not found`

**Solution**:
1. Verify environment variable: `echo $OPENAI_API_KEY`
2. Restart Django server after setting env var
3. Check API key is valid on provider's website

### Health Check Failing

**Error**: `health_check() returns False`

**Solutions**:
- **Ollama**: Ensure Ollama is running (`ollama serve`)
- **OpenAI**: Check internet connection and API key
- **Anthropic**: Check internet connection and API key

---

## 📝 Checklist for Provider Switch

Before switching providers:

- [ ] Choose new provider (openai/anthropic/google)
- [ ] Install required SDK (`pip install openai`)
- [ ] Get API key from provider
- [ ] Set API key in environment variable
- [ ] Update `backend/settings.py` (LLM_PROVIDER and LLM_CONFIG)
- [ ] Uncomment provider implementation file
- [ ] Uncomment provider import in `providers/__init__.py`
- [ ] Restart Django server
- [ ] Run health check test
- [ ] Run full test suite
- [ ] Test in browser
- [ ] Monitor costs (if using paid provider)

---

## 💡 Quick Reference

### Current Setup
```python
# File: backend/settings.py
LLM_PROVIDER = 'ollama'
LLM_CONFIG = {
    'model_name': 'llama3.2',
    'base_url': 'http://127.0.0.1:11434',
}
```

### Application Code (Never Changes!)
```python
# Your application code stays the same regardless of provider
from services.llm_service import get_llm_provider

llm = get_llm_provider()
response = llm.chat(message="Hello", system_prompt="You are helpful")
print(response.text)
```

### Available Providers
- `'ollama'` - ✅ Implemented (current)
- `'openai'` - 📝 Template ready
- `'anthropic'` - 📝 Template ready
- `'google'` - 🔮 Future

---

## 🎓 Learning Resources

### Ollama
- Docs: https://github.com/ollama/ollama
- Models: https://ollama.com/library

### OpenAI
- Docs: https://platform.openai.com/docs
- Pricing: https://openai.com/pricing

### Anthropic
- Docs: https://docs.anthropic.com
- Pricing: https://www.anthropic.com/pricing

---

**Questions?** Check `services/llm_service/README.md` for detailed documentation.

**Status**: ✅ Plug-and-Play Architecture Complete  
**Current Provider**: Ollama (llama3.2)  
**Ready to Switch**: YES - Just change configuration!
