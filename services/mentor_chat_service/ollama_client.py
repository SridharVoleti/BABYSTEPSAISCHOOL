# 2025-11-26: Robust Ollama Client with Connection Pooling and Retry Logic
# Author: BabySteps Development Team
# Purpose: Reliable Ollama LLM connectivity with resilience patterns

import os
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Lock
import json

# 2025-11-26: Configure logging for debugging connection issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2025-11-26: Environment configuration with sensible defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT", "60"))
POOL_CONNECTIONS = int(os.getenv("OLLAMA_POOL_CONNECTIONS", "10"))
POOL_MAXSIZE = int(os.getenv("OLLAMA_POOL_MAXSIZE", "20"))

class CircuitBreaker:
    """
    2025-11-26: Circuit breaker pattern to prevent cascading failures
    Opens circuit after threshold failures, closes after recovery period
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        # 2025-11-26: Initialize circuit breaker state
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """
        2025-11-26: Execute function with circuit breaker protection
        """
        with self.lock:
            # 2025-11-26: Check if circuit is open
            if self.state == 'open':
                # 2025-11-26: Check if recovery timeout has passed
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                    logger.info("Circuit breaker: Attempting recovery (half-open state)")
                    self.state = 'half_open'
                else:
                    # 2025-11-26: Circuit still open, fail fast
                    raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            # 2025-11-26: Execute the function
            result = func(*args, **kwargs)
            
            # 2025-11-26: Success - reset failure count and close circuit
            with self.lock:
                self.failure_count = 0
                if self.state == 'half_open':
                    logger.info("Circuit breaker: Recovery successful, closing circuit")
                    self.state = 'closed'
            
            return result
            
        except Exception as e:
            # 2025-11-26: Failure - increment count and potentially open circuit
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                # 2025-11-26: Open circuit if threshold exceeded
                if self.failure_count >= self.failure_threshold:
                    logger.error(f"Circuit breaker: Opening circuit after {self.failure_count} failures")
                    self.state = 'open'
                elif self.state == 'half_open':
                    logger.warning("Circuit breaker: Recovery failed, reopening circuit")
                    self.state = 'open'
            
            raise e


class OllamaClient:
    """
    2025-11-26: Singleton Ollama client with connection pooling and resilience
    Implements retry logic, circuit breaker, and health monitoring
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        # 2025-11-26: Singleton pattern to ensure single connection pool
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 2025-11-26: Initialize only once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # 2025-11-26: Configure session with connection pooling
        self.session = requests.Session()
        
        # 2025-11-26: Configure retry strategy for transient failures
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,  # 2025-11-26: Exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],  # 2025-11-26: Retry on these HTTP status codes
            allowed_methods=["GET", "POST"]  # 2025-11-26: Retry for both GET and POST
        )
        
        # 2025-11-26: Create HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=POOL_CONNECTIONS,
            pool_maxsize=POOL_MAXSIZE,
            pool_block=False  # 2025-11-26: Don't block when pool is full, create new connection
        )
        
        # 2025-11-26: Mount adapter for both HTTP and HTTPS
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 2025-11-26: Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'  # 2025-11-26: Reuse connections
        })
        
        # 2025-11-26: Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        # 2025-11-26: Health check state
        self.last_health_check = None
        self.is_healthy = False
        
        logger.info(f"OllamaClient initialized: {OLLAMA_BASE_URL}, model: {DEFAULT_MODEL}")
    
    def health_check(self, force: bool = False) -> bool:
        """
        2025-11-26: Check if Ollama service is healthy
        Caches result for 30 seconds to avoid excessive checks
        """
        # 2025-11-26: Return cached result if recent
        if not force and self.last_health_check:
            if datetime.now() - self.last_health_check < timedelta(seconds=30):
                return self.is_healthy
        
        try:
            # 2025-11-26: Check if Ollama is running and model is available
            response = self.session.get(
                f"{OLLAMA_BASE_URL}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            # 2025-11-26: Check if our model is available
            models = response.json().get('models', [])
            model_available = any(DEFAULT_MODEL in m['name'] for m in models)
            
            # 2025-11-26: Update health state
            self.is_healthy = model_available
            self.last_health_check = datetime.now()
            
            if not model_available:
                logger.warning(f"Model {DEFAULT_MODEL} not found in Ollama")
            
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.is_healthy = False
            self.last_health_check = datetime.now()
            return False
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        2025-11-26: Generate response from Ollama with retry logic
        Returns dict with 'response' key containing generated text
        """
        # 2025-11-26: Validate inputs
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # 2025-11-26: Use default model if not specified
        model = model or DEFAULT_MODEL
        
        # 2025-11-26: Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        # 2025-11-26: Add max_tokens if specified
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # 2025-11-26: Define the API call function
        def make_request():
            logger.info(f"Generating response for prompt (length: {len(prompt)})")
            start_time = time.time()
            
            try:
                # 2025-11-26: Make POST request to Ollama
                response = self.session.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=TIMEOUT_SECONDS
                )
                
                # 2025-11-26: Raise exception for HTTP errors
                response.raise_for_status()
                
                # 2025-11-26: Parse response
                result = response.json()
                
                # 2025-11-26: Log success
                elapsed = time.time() - start_time
                logger.info(f"Response generated successfully in {elapsed:.2f}s")
                
                return result
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout after {TIMEOUT_SECONDS}s")
                raise Exception(f"Ollama request timed out after {TIMEOUT_SECONDS}s")
            
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise Exception(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
            
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if e.response.status_code == 404:
                    raise Exception(f"Model {model} not found. Run: ollama pull {model}")
                raise Exception(f"Ollama HTTP error: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        # 2025-11-26: Execute with circuit breaker protection
        try:
            return self.circuit_breaker.call(make_request)
        except Exception as e:
            # 2025-11-26: Log and re-raise with context
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        2025-11-26: Simplified chat interface
        Returns just the response text
        """
        # 2025-11-26: Build prompt with system context
        if system_prompt:
            prompt = f"System: {system_prompt}\nUser: {message}\nAssistant:"
        else:
            prompt = f"User: {message}\nAssistant:"
        
        # 2025-11-26: Generate response
        result = self.generate(prompt, temperature=temperature)
        
        # 2025-11-26: Extract and return text
        return result.get('response', '').strip()
    
    def close(self):
        """
        2025-11-26: Clean up resources
        """
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("OllamaClient session closed")


# 2025-11-26: Create singleton instance
ollama_client = OllamaClient()
