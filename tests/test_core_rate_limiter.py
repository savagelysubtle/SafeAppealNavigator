"""
Test suite for core.rate_limiter module.

This module contains comprehensive tests for the universal rate limiting system,
including token bucket algorithm, provider-specific configurations, exponential
backoff, retry logic, and convenience functions.
"""

import time
from unittest.mock import patch

import pytest

from ai_research_assistant.core.rate_limiter import (
    ProviderType,
    RateLimitConfig,
    RateLimitedClient,
    TokenBucket,
    UniversalRateLimiter,
    anthropic_rate_limiter,
    create_rate_limiter,
    google_rate_limiter,
    openai_rate_limiter,
)


class TestProviderType:
    """Test cases for ProviderType enum."""

    def test_provider_type_values(self):
        """Test that all expected provider types exist with correct values."""
        expected_providers = {
            "GOOGLE": "google",
            "OPENAI": "openai",
            "ANTHROPIC": "anthropic",
            "MISTRAL": "mistral",
            "OLLAMA": "ollama",
            "DEEPSEEK": "deepseek",
            "WATSONX": "watsonx",
        }

        for enum_name, enum_value in expected_providers.items():
            provider_enum = getattr(ProviderType, enum_name)
            assert provider_enum.value == enum_value


class TestRateLimitConfig:
    """Test cases for RateLimitConfig dataclass."""

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig with default values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.tokens_per_minute is None
        assert config.delay_range == (1, 60)
        assert config.max_retries == 5
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.provider == ProviderType.GOOGLE
        assert config.retryable_status_codes == [429, 500, 503]

    def test_rate_limit_config_custom_values(self):
        """Test RateLimitConfig with custom values."""
        config = RateLimitConfig(
            requests_per_minute=10,
            tokens_per_minute=1000,
            delay_range=(2, 30),
            max_retries=3,
            exponential_base=1.5,
            jitter=False,
            provider=ProviderType.OPENAI,
            retryable_status_codes=[429, 502, 503, 504],
        )

        assert config.requests_per_minute == 10
        assert config.tokens_per_minute == 1000
        assert config.delay_range == (2, 30)
        assert config.max_retries == 3
        assert config.exponential_base == 1.5
        assert config.jitter is False
        assert config.provider == ProviderType.OPENAI
        assert config.retryable_status_codes == [429, 502, 503, 504]


class TestTokenBucket:
    """Test cases for TokenBucket algorithm implementation."""

    def test_token_bucket_initialization(self):
        """Test TokenBucket initialization."""
        capacity = 10
        refill_rate = 2.0

        bucket = TokenBucket(capacity, refill_rate)

        assert bucket.capacity == capacity
        assert bucket.refill_rate == refill_rate
        assert bucket.tokens == capacity  # Starts full
        assert bucket.last_refill <= time.time()

    def test_token_bucket_consume_available_tokens(self):
        """Test consuming tokens when available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Should be able to consume tokens initially
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

        # Should be able to consume remaining tokens
        assert bucket.consume(5) is True
        assert abs(bucket.tokens) < 1e-4  # Use consistent tolerance for floating point

    def test_token_bucket_consume_insufficient_tokens(self):
        """Test consuming tokens when insufficient."""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        # Consume all tokens first
        assert bucket.consume(5) is True
        assert (
            abs(bucket.tokens) < 1e-4
        )  # Use more lenient tolerance for floating point

        # Should not be able to consume more
        assert bucket.consume(1) is False
        assert (
            abs(bucket.tokens) < 1e-4
        )  # Use more lenient tolerance for floating point

    @patch("time.time")
    def test_token_bucket_refill_mechanism(self, mock_time):
        """Test token bucket refill mechanism."""
        # Setup time progression
        mock_time.side_effect = [0, 1, 2, 3]  # Time advancing by 1 second each call

        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens per second

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0

        # Advance time by 1 second (should add 2 tokens)
        mock_time.return_value = 1
        bucket._refill()
        assert bucket.tokens == 2

    def test_token_bucket_time_until_available(self):
        """Test calculation of time until tokens are available."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens per second

        # Consume all tokens
        bucket.consume(10)
        assert abs(bucket.tokens) < 1e-4  # Use consistent tolerance for floating point

        # Should need 2.5 seconds to get 5 tokens
        time_needed = bucket.time_until_available(5)
        assert (
            abs(time_needed - 2.5) < 1e-4
        )  # Use consistent tolerance for floating point


class TestUniversalRateLimiter:
    """Test cases for UniversalRateLimiter class."""

    def test_universal_rate_limiter_initialization(self):
        """Test UniversalRateLimiter initialization."""
        config = RateLimitConfig(
            requests_per_minute=60, tokens_per_minute=1000, provider=ProviderType.OPENAI
        )

        limiter = UniversalRateLimiter(config)

        assert limiter.config == config
        assert limiter.request_bucket.capacity == 60
        assert limiter.request_bucket.refill_rate == 1.0  # 60/60 seconds
        assert limiter.token_bucket is not None
        assert limiter.token_bucket.capacity == 1000

    @patch("time.sleep")
    def test_wait_if_needed_no_wait_required(self, mock_sleep):
        """Test wait_if_needed when no waiting is required."""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = UniversalRateLimiter(config)

        # Should not need to wait initially
        wait_time = limiter.wait_if_needed(1)

        assert wait_time == 0.0
        mock_sleep.assert_not_called()

    def test_calculate_backoff_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RateLimitConfig(
            exponential_base=2.0,
            delay_range=(1, 60),
            jitter=False,  # Disable jitter for predictable results
        )
        limiter = UniversalRateLimiter(config)

        # Test exponential progression
        assert limiter.calculate_backoff_delay(0, 1.0) == 1.0  # 1 * 2^0
        assert limiter.calculate_backoff_delay(1, 1.0) == 2.0  # 1 * 2^1
        assert limiter.calculate_backoff_delay(2, 1.0) == 4.0  # 1 * 2^2

    def test_calculate_backoff_delay_clamping(self):
        """Test that backoff delay is clamped to configured range."""
        config = RateLimitConfig(
            exponential_base=2.0,
            delay_range=(2, 10),  # Narrow range
            jitter=False,
        )
        limiter = UniversalRateLimiter(config)

        # Very small delay should be clamped to minimum
        delay = limiter.calculate_backoff_delay(0, 0.5)
        assert delay == 2

        # Very large delay should be clamped to maximum
        delay = limiter.calculate_backoff_delay(10, 1.0)
        assert delay == 10

    def test_is_retryable_error_status_codes(self):
        """Test retryable error detection by status code."""
        config = RateLimitConfig(retryable_status_codes=[429, 500, 503])
        limiter = UniversalRateLimiter(config)

        # Test retryable status codes
        assert limiter.is_retryable_error(429) is True
        assert limiter.is_retryable_error(500) is True
        assert limiter.is_retryable_error(503) is True

        # Test non-retryable status codes
        assert limiter.is_retryable_error(404) is False
        assert limiter.is_retryable_error(401) is False
        assert limiter.is_retryable_error(200) is False


class TestRateLimitedClient:
    """Test cases for RateLimitedClient wrapper."""

    def test_rate_limited_client_initialization(self):
        """Test RateLimitedClient initialization."""
        config = RateLimitConfig()
        limiter = UniversalRateLimiter(config)
        client = RateLimitedClient(limiter)

        assert client.limiter == limiter

    @patch(
        "ai_research_assistant.core.rate_limiter.UniversalRateLimiter.wait_if_needed"
    )
    def test_rate_limited_client_successful_execution(self, mock_wait):
        """Test successful function execution through RateLimitedClient."""
        config = RateLimitConfig()
        limiter = UniversalRateLimiter(config)
        client = RateLimitedClient(limiter)

        mock_wait.return_value = 0.0

        def test_function(arg1, arg2=None):
            return f"Result: {arg1}, {arg2}"

        result = client.execute(test_function, "value1", arg2="value2")

        assert result == "Result: value1, value2"
        mock_wait.assert_called_once()

    @patch(
        "ai_research_assistant.core.rate_limiter.UniversalRateLimiter.wait_if_needed"
    )
    @patch("time.sleep")
    def test_rate_limited_client_retry_logic(self, mock_sleep, mock_wait):
        """Test retry logic in RateLimitedClient."""
        config = RateLimitConfig(max_retries=2, delay_range=(1, 5))
        limiter = UniversalRateLimiter(config)
        client = RateLimitedClient(limiter)

        mock_wait.return_value = 0.0

        call_count = 0

        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times, succeed on 3rd
                error = Exception("Rate limit error")
                error.status_code = 429
                raise error
            return "Success"

        result = client.execute(failing_function)

        assert result == "Success"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep between retries

    def test_rate_limited_client_as_decorator(self):
        """Test using RateLimitedClient as a decorator."""
        config = RateLimitConfig()
        limiter = UniversalRateLimiter(config)
        client = RateLimitedClient(limiter)

        @client
        def decorated_function(value):
            return f"Decorated: {value}"

        result = decorated_function("test")
        assert result == "Decorated: test"


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_create_rate_limiter_with_string_provider(self):
        """Test creating rate limiter with string provider."""
        limiter = create_rate_limiter("google", requests_per_minute=10)

        assert isinstance(limiter, UniversalRateLimiter)
        assert limiter.config.provider == ProviderType.GOOGLE
        assert limiter.config.requests_per_minute == 10

    def test_create_rate_limiter_invalid_provider(self):
        """Test creating rate limiter with invalid provider."""
        with pytest.raises(ValueError) as exc_info:
            create_rate_limiter("invalid_provider")

        assert "Unknown provider" in str(exc_info.value)

    def test_google_rate_limiter_convenience_function(self):
        """Test google_rate_limiter convenience function."""
        client = google_rate_limiter(requests_per_minute=10)

        assert isinstance(client, RateLimitedClient)
        assert client.limiter.config.provider == ProviderType.GOOGLE
        assert client.limiter.config.requests_per_minute == 10

    def test_openai_rate_limiter_convenience_function(self):
        """Test openai_rate_limiter convenience function."""
        client = openai_rate_limiter(requests_per_minute=30)

        assert isinstance(client, RateLimitedClient)
        assert client.limiter.config.provider == ProviderType.OPENAI
        assert client.limiter.config.requests_per_minute == 30

    def test_anthropic_rate_limiter_convenience_function(self):
        """Test anthropic_rate_limiter convenience function."""
        client = anthropic_rate_limiter(requests_per_minute=25)

        assert isinstance(client, RateLimitedClient)
        assert client.limiter.config.provider == ProviderType.ANTHROPIC
        assert client.limiter.config.requests_per_minute == 25


class TestProviderSpecificConfigurations:
    """Test cases for provider-specific default configurations."""

    def test_google_provider_defaults(self):
        """Test Google provider default configuration."""
        limiter = create_rate_limiter(ProviderType.GOOGLE)

        # Google should have conservative defaults for experimental models
        assert (
            limiter.config.requests_per_minute == 5
        )  # Uses provider default since we didn't override
        assert 429 in limiter.config.retryable_status_codes
        assert 500 in limiter.config.retryable_status_codes
        assert 503 in limiter.config.retryable_status_codes

    def test_openai_provider_defaults(self):
        """Test OpenAI provider default configuration."""
        limiter = create_rate_limiter(ProviderType.OPENAI)

        # OpenAI should have standard defaults
        assert (
            limiter.config.requests_per_minute == 60
        )  # Uses provider default since we didn't override
        assert 429 in limiter.config.retryable_status_codes
        assert 502 in limiter.config.retryable_status_codes
        assert 504 in limiter.config.retryable_status_codes

    def test_provider_defaults_override(self):
        """Test that provider defaults can be overridden."""
        limiter = create_rate_limiter(
            ProviderType.GOOGLE,
            requests_per_minute=20,  # Override default
            retryable_status_codes=[429, 500],  # Override default
        )

        assert limiter.config.requests_per_minute == 20
        assert limiter.config.retryable_status_codes == [429, 500]


class TestAsyncSupport:
    """Test cases for async functionality."""

    @pytest.mark.asyncio
    @patch("asyncio.sleep")
    @patch("ai_research_assistant.core.rate_limiter.TokenBucket.time_until_available")
    async def test_await_if_needed_with_delay(self, mock_time_until, mock_sleep):
        """Test async await_if_needed when delay is required."""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = UniversalRateLimiter(config)

        # Mock request bucket to require waiting
        mock_time_until.return_value = 1.5
        limiter.request_bucket.time_until_available = mock_time_until

        wait_time = await limiter.await_if_needed(1)

        assert wait_time == 1.5
        mock_sleep.assert_called_once_with(1.5)


class TestEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_token_bucket_zero_capacity(self):
        """Test TokenBucket with zero capacity."""
        bucket = TokenBucket(capacity=0, refill_rate=1.0)

        assert bucket.capacity == 0
        assert bucket.tokens == 0
        assert bucket.consume(1) is False

    def test_rate_limiter_with_extreme_config(self):
        """Test rate limiter with extreme configuration values."""
        config = RateLimitConfig(
            requests_per_minute=1,
            tokens_per_minute=1,
            delay_range=(0, 1),
            max_retries=0,
            exponential_base=1.0,
        )

        limiter = UniversalRateLimiter(config)

        assert limiter.request_bucket.capacity == 1
        assert limiter.token_bucket.capacity == 1
        assert limiter.config.max_retries == 0
