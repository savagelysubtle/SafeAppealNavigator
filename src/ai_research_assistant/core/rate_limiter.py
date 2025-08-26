"""
Universal Rate Limiter for AI Research Assistant

Supports Google Gemini, OpenAI, and Anthropic APIs with intelligent
rate limiting using token bucket algorithm and exponential backoff.

Based on research from:
- https://medium.com/@balakrishnamaduru/handling-api-rate-limits-with-python-a-simple-recursive-approach-08349dd71057
- https://cookbook.openai.com/examples/how_to_handle_rate_limits
- https://docs.anthropic.com/en/api/rate-limits
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported LLM providers"""

    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    WATSONX = "watsonx"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    tokens_per_minute: Optional[int] = None
    delay_range: tuple[int, int] = (1, 60)  # Min 1s, Max 60s as requested
    max_retries: int = 5
    exponential_base: float = 2.0
    jitter: bool = True
    provider: ProviderType = ProviderType.GOOGLE

    # Provider-specific retry status codes
    retryable_status_codes: list[int] = field(default_factory=lambda: [429, 500, 503])


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Based on the algorithm described in:
    https://dev.to/satrobit/rate-limiting-using-the-token-bucket-algorithm-3cjh
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens the bucket can hold
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_passed = now - self.last_refill
        self.last_refill = now

        # Add tokens based on time passed
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until enough tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait, or 0 if tokens are available now
        """
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class UniversalRateLimiter:
    """
    Universal rate limiter supporting all major LLM providers.

    Uses token bucket algorithm with provider-specific configurations
    and exponential backoff for error handling.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter with configuration."""
        self.config = config

        # Create token bucket for requests per minute
        rpm = config.requests_per_minute
        self.request_bucket = TokenBucket(
            capacity=rpm,
            refill_rate=rpm / 60.0,  # Convert per minute to per second
        )

        # Optional token bucket for tokens per minute
        self.token_bucket = None
        if config.tokens_per_minute:
            tpm = config.tokens_per_minute
            self.token_bucket = TokenBucket(capacity=tpm, refill_rate=tpm / 60.0)

        logger.info(
            f"Initialized rate limiter for {config.provider.value}: "
            f"{rpm} RPM, {config.tokens_per_minute or 'unlimited'} TPM"
        )

    def wait_if_needed(self, tokens: int = 1) -> float:
        """
        Wait if rate limit would be exceeded.

        Args:
            tokens: Estimated tokens for the request

        Returns:
            Seconds waited
        """
        # Check request rate limit
        request_wait = self.request_bucket.time_until_available(1)

        # Check token rate limit if configured
        token_wait = 0.0
        if self.token_bucket:
            token_wait = self.token_bucket.time_until_available(tokens)

        # Wait for the longer of the two
        wait_time = max(request_wait, token_wait)

        if wait_time > 0:
            logger.info(f"Rate limit preventive wait: {wait_time:.2f}s")
            time.sleep(wait_time)

        # Consume tokens
        self.request_bucket.consume(1)
        if self.token_bucket:
            self.token_bucket.consume(tokens)

        return wait_time

    async def await_if_needed(self, tokens: int = 1) -> float:
        """Async version of wait_if_needed."""
        # Check request rate limit
        request_wait = self.request_bucket.time_until_available(1)

        # Check token rate limit if configured
        token_wait = 0.0
        if self.token_bucket:
            token_wait = self.token_bucket.time_until_available(tokens)

        # Wait for the longer of the two
        wait_time = max(request_wait, token_wait)

        if wait_time > 0:
            logger.info(f"Rate limit preventive wait: {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        # Consume tokens
        self.request_bucket.consume(1)
        if self.token_bucket:
            self.token_bucket.consume(tokens)

        return wait_time

    def calculate_backoff_delay(self, attempt: int, base_delay: float = 1.0) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt (0-based)
            base_delay: Base delay in seconds

        Returns:
            Delay in seconds, clamped to delay_range
        """
        # Exponential backoff
        delay = base_delay * (self.config.exponential_base**attempt)

        # Add jitter if enabled
        if self.config.jitter:
            jitter = random.uniform(0.1, 1.0)
            delay *= jitter

        # Clamp to configured range
        min_delay, max_delay = self.config.delay_range
        delay = max(min_delay, min(max_delay, delay))

        return delay

    def extract_retry_after(self, response_headers: Dict[str, str]) -> Optional[float]:
        """
        Extract retry-after value from response headers.

        Args:
            response_headers: HTTP response headers

        Returns:
            Retry delay in seconds, or None if not found
        """
        # Standard retry-after header
        retry_after = response_headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except (ValueError, TypeError):
                pass

        # Provider-specific headers
        if self.config.provider == ProviderType.ANTHROPIC:
            # Anthropic uses detailed rate limit headers
            reset_time = response_headers.get("anthropic-ratelimit-requests-reset")
            if reset_time:
                # Parse RFC 3339 format - simplified for now
                # In practice, you'd want proper datetime parsing
                pass

        return None

    def is_retryable_error(
        self, status_code: int, exception: Optional[Exception] = None
    ) -> bool:
        """
        Check if an error is retryable based on status code or exception.

        Args:
            status_code: HTTP status code
            exception: Exception instance (optional)

        Returns:
            True if the error should be retried
        """
        # Check status codes
        if status_code in self.config.retryable_status_codes:
            return True

        # Check exception types (for different libraries)
        if exception:
            exception_name = type(exception).__name__

            # Common rate limit exceptions
            rate_limit_exceptions = [
                "RateLimitError",  # OpenAI
                "ResourceExhausted",  # Google
                "TooManyRequestsError",  # Generic
                "InternalServerError",  # Sometimes rate limits
            ]

            if any(exc in exception_name for exc in rate_limit_exceptions):
                return True

        return False


class RateLimitedClient:
    """
    Rate-limited wrapper for API clients.

    Can be used as a decorator or context manager to add rate limiting
    to any function that makes API calls.
    """

    def __init__(self, limiter: UniversalRateLimiter):
        """Initialize with a rate limiter."""
        self.limiter = limiter

    def __call__(self, func: Callable) -> Callable:
        """Use as decorator."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_retry(func, *args, **kwargs)

        return wrapper

    def __enter__(self):
        """Use as context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with rate limiting and retry logic."""
        return self._execute_with_retry(func, *args, **kwargs)

    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        for attempt in range(self.limiter.config.max_retries + 1):
            try:
                # Wait if needed to respect rate limits
                estimated_tokens = kwargs.get("estimated_tokens", 1)
                self.limiter.wait_if_needed(estimated_tokens)

                # Execute the function
                result = func(*args, **kwargs)

                # Success!
                if attempt > 0:
                    logger.info(f"Success after {attempt} retries")

                return result

            except Exception as e:
                # Check if this is a retryable error
                status_code = getattr(
                    e, "status_code", getattr(e, "response", {}).get("status", 0)
                )

                if not self.limiter.is_retryable_error(status_code, e):
                    # Not retryable, re-raise immediately
                    raise

                if attempt >= self.limiter.config.max_retries:
                    # Max retries exceeded
                    logger.error(
                        f"Max retries ({self.limiter.config.max_retries}) exceeded"
                    )
                    raise

                # Calculate delay
                delay = self.limiter.calculate_backoff_delay(attempt)

                # Try to extract retry-after from response
                response = getattr(e, "response", None)
                if response and hasattr(response, "headers"):
                    retry_after = self.limiter.extract_retry_after(
                        dict(response.headers)
                    )
                    if retry_after:
                        delay = max(delay, retry_after)

                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}), waiting {delay:.2f}s: {e}"
                )
                time.sleep(delay)

        # Should never reach here
        raise RuntimeError("Retry logic error")


# Convenience functions for quick setup
def create_rate_limiter(
    provider: Union[str, ProviderType],
    requests_per_minute: int = 60,
    tokens_per_minute: Optional[int] = None,
    **kwargs,
) -> UniversalRateLimiter:
    """
    Create a rate limiter for a specific provider.

    Args:
        provider: Provider name or enum
        requests_per_minute: Maximum requests per minute
        tokens_per_minute: Maximum tokens per minute (optional)
        **kwargs: Additional configuration options

    Returns:
        Configured UniversalRateLimiter
    """
    if isinstance(provider, str):
        try:
            provider = ProviderType(provider.lower())
        except ValueError:
            raise ValueError(f"Unknown provider: {provider}")

    # Provider-specific defaults
    provider_configs = {
        ProviderType.GOOGLE: {
            "requests_per_minute": 5,  # Conservative for experimental models
            "retryable_status_codes": [429, 500, 503],
        },
        ProviderType.OPENAI: {
            "requests_per_minute": 60,
            "retryable_status_codes": [429, 500, 502, 503, 504],
        },
        ProviderType.ANTHROPIC: {
            "requests_per_minute": 50,  # Tier 1 default
            "retryable_status_codes": [429, 500, 502, 503],
        },
    }

    config_defaults = provider_configs.get(provider, {})
    # Only use provider default for requests_per_minute if not explicitly provided
    if requests_per_minute == 60:  # Default value
        requests_per_minute = config_defaults.get("requests_per_minute", 60)

    # Remove requests_per_minute from config_defaults to avoid conflict
    config_defaults = {
        k: v for k, v in config_defaults.items() if k != "requests_per_minute"
    }
    config_defaults.update(kwargs)

    config = RateLimitConfig(
        provider=provider,
        requests_per_minute=requests_per_minute,
        tokens_per_minute=tokens_per_minute,
        **config_defaults,
    )

    return UniversalRateLimiter(config)


def rate_limited(
    provider: Union[str, ProviderType], requests_per_minute: int = 60, **kwargs
):
    """
    Decorator for adding rate limiting to functions.

    Usage:
        @rate_limited('google', requests_per_minute=5)
        def call_gemini_api():
            # Your API call here
            pass
    """
    limiter = create_rate_limiter(provider, requests_per_minute, **kwargs)
    client = RateLimitedClient(limiter)
    return client


# Provider-specific convenience functions
def google_rate_limiter(requests_per_minute: int = 5, **kwargs) -> RateLimitedClient:
    """Create rate limiter for Google Gemini (default 5 RPM for experimental models)."""
    limiter = create_rate_limiter(ProviderType.GOOGLE, requests_per_minute, **kwargs)
    return RateLimitedClient(limiter)


def openai_rate_limiter(requests_per_minute: int = 60, **kwargs) -> RateLimitedClient:
    """Create rate limiter for OpenAI."""
    limiter = create_rate_limiter(ProviderType.OPENAI, requests_per_minute, **kwargs)
    return RateLimitedClient(limiter)


def anthropic_rate_limiter(
    requests_per_minute: int = 50, **kwargs
) -> RateLimitedClient:
    """Create rate limiter for Anthropic."""
    limiter = create_rate_limiter(ProviderType.ANTHROPIC, requests_per_minute, **kwargs)
    return RateLimitedClient(limiter)


# Example usage
if __name__ == "__main__":
    # Test the rate limiter
    import time

    @rate_limited("google", requests_per_minute=5)
    def mock_api_call(message: str):
        print(f"API call: {message}")
        return f"Response to: {message}"

    print("Testing rate limiter...")
    start_time = time.time()

    for i in range(3):
        result = mock_api_call(f"Message {i + 1}")
        print(f"Result: {result}")

    elapsed = time.time() - start_time
    print(f"Total time: {elapsed:.2f} seconds")


# ===== COMPREHENSIVE USAGE EXAMPLES =====

"""
🛠️ Universal Rate Limiter - Usage Examples

This module provides universal rate limiting for all LLM providers.
Based on research from Google Gemini forums, OpenAI Cookbook, and Anthropic docs.

## Quick Usage Examples:

### 1. Decorator Pattern (Simplest)
```python
from src.ai_research_assistant.utils.rate_limiter import rate_limited

@rate_limited('google', requests_per_minute=5)
def call_gemini_api(prompt):
    # Your API call here
    response = gemini_client.generate_content(prompt)
    return response.text

# Automatically handles rate limiting and retries
result = call_gemini_api("What is AI?")
```

### 2. Context Manager Pattern
```python
from src.ai_research_assistant.utils.rate_limiter import google_rate_limiter

with google_rate_limiter(requests_per_minute=5) as limiter:
    for prompt in prompts:
        result = limiter.execute(gemini_client.generate_content, prompt)
        print(result.text)
```

### 3. Manual Rate Limiter (Full Control)
```python
from src.ai_research_assistant.utils.rate_limiter import create_rate_limiter

# Create limiter for specific provider
limiter = create_rate_limiter(
    provider='google',
    requests_per_minute=5,
    delay_range=(1, 60),
    max_retries=5
)

# Use with any function
def my_api_call():
    return gemini_client.generate_content("Hello")

try:
    # Wait if needed, then call
    limiter.wait_if_needed(estimated_tokens=100)
    result = my_api_call()
except Exception as e:
    print(f"API call failed: {e}")
```

### 4. Global Settings Integration
```python
from src.ai_research_assistant.webui.components.global_settings_panel import GlobalSettingsManager

# Get rate limiting config from global settings
settings = GlobalSettingsManager()
rate_config = settings.get_rate_limiting_config('google')

if rate_config['enabled']:
    limiter = create_rate_limiter(
        provider='google',
        requests_per_minute=rate_config['requests_per_minute'],
        delay_range=rate_config['delay_range'],
        max_retries=rate_config['max_retries']
    )
```

### 5. Provider-Specific Examples

#### Google Gemini (Conservative 5 RPM)
```python
@rate_limited('google', requests_per_minute=5)
def call_gemini_2_5_experimental(prompt):
    # Handles 429, 500, 503 errors automatically
    return genai.GenerativeModel('gemini-2.5-pro-preview-05-06').generate_content(prompt)
```

#### OpenAI (Standard 60 RPM)
```python
@rate_limited('openai', requests_per_minute=60)
def call_gpt4(messages):
    # Handles 429 errors with retry-after headers
    return openai.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
```

#### Anthropic (Tier 1: 50 RPM)
```python
@rate_limited('anthropic', requests_per_minute=50)
def call_claude(prompt):
    # Handles token bucket algorithm and detailed headers
    return anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        messages=[{"role": "user", "content": prompt}]
    )
```

### 6. Advanced Configuration
```python
# Custom configuration for high-throughput scenarios
config = RateLimitConfig(
    provider=ProviderType.GOOGLE,
    requests_per_minute=10,           # Higher for paid accounts
    delay_range=(2, 30),             # Custom delay range
    max_retries=3,                   # Fewer retries
    exponential_base=1.5,            # Slower backoff
    jitter=True,                     # Prevent synchronized retries
    retryable_status_codes=[429, 500, 503, 502]  # Custom retry codes
)

limiter = UniversalRateLimiter(config)
client = RateLimitedClient(limiter)

# Use with any function
result = client.execute(my_api_function, arg1, arg2, estimated_tokens=500)
```

### 7. Async Support
```python
import asyncio

async def my_async_api_call():
    limiter = create_rate_limiter('openai', requests_per_minute=60)

    # Async waiting
    await limiter.await_if_needed(estimated_tokens=100)

    # Your async API call
    response = await openai_async_client.chat.completions.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    return response

# Run async
result = asyncio.run(my_async_api_call())
```

## 🎯 Rate Limit Recommendations by Provider:

### Google Gemini
- **Free Tier**: 5 RPM (very conservative due to experimental model limits)
- **Paid Tier**: Can increase to 15-60 RPM depending on model
- **Error Codes**: Watch for 429, 500, 503 (sometimes inconsistent)

### OpenAI
- **Free Tier**: 3-20 RPM depending on model
- **Tier 1**: 60 RPM for GPT-4, higher for GPT-3.5
- **Error Codes**: Standard 429 with reliable retry-after headers

### Anthropic
- **Tier 1**: 50 RPM (requests), also has token limits
- **Higher Tiers**: 1000+ RPM
- **Error Codes**: 429 with detailed rate limit headers

### Local Providers (Ollama)
- **No Limits**: Set high RPM (100+) since it's local
- **Hardware Limited**: Only by your machine's capabilities

## 🚨 Troubleshooting:

### Still Getting 429 Errors?
1. Lower your RPM setting
2. Check if you have multiple clients running
3. Verify your provider tier/limits
4. Enable jitter to prevent synchronized requests

### Slow Performance?
1. Increase RPM if you're under your limit
2. Reduce delay_range maximum
3. Check if preventive waiting is too conservative

### Integration Issues?
1. Use GlobalSettingsManager to get config from UI
2. Check provider-specific error codes
3. Test with simple mock functions first

For more information, see:
- Google Gemini API docs: https://ai.google.dev/gemini-api/docs/rate-limits
- OpenAI Rate Limits: https://cookbook.openai.com/examples/how_to_handle_rate_limits
- Anthropic Rate Limits: https://docs.anthropic.com/en/api/rate-limits
"""
