"""
Test Suite for Task 1.1: Race Condition Fix
===========================================

Validates that the asyncio.Lock in RateLimiter prevents race conditions
when multiple concurrent tasks attempt to check rate limits.

Run with: pytest tests/test_task_1_1_race_condition.py -v
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.orchestrator.supervisor import RateLimiter


@pytest.fixture
def rate_limiter():
    """Create a fresh RateLimiter for each test"""
    return RateLimiter()


class TestRateLimiterAtomic:
    """Test atomicity of rate limiting operations"""
    
    @pytest.mark.asyncio
    async def test_lock_exists(self, rate_limiter):
        """Verify that asyncio.Lock is initialized"""
        assert hasattr(rate_limiter, 'lock'), "RateLimiter must have 'lock' attribute"
        assert isinstance(rate_limiter.lock, asyncio.Lock), "lock must be asyncio.Lock instance"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_is_async(self, rate_limiter):
        """Verify that check_rate_limit is an async function"""
        import inspect
        assert inspect.iscoroutinefunction(rate_limiter.check_rate_limit), \
            "check_rate_limit must be async function"
    
    @pytest.mark.asyncio
    async def test_single_request_allowed(self, rate_limiter):
        """Test that first request is always allowed"""
        permitted, reason = await rate_limiter.check_rate_limit("test_agent", "agent")
        assert permitted is True, "First request should be allowed"
        assert reason == "", "No reason should be given for allowed request"
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test that rate limit is enforced after max requests"""
        # Agent limit is 100 per 60 seconds
        for i in range(100):
            permitted, _ = await rate_limiter.check_rate_limit("test_agent", "agent")
            assert permitted is True, f"Request {i + 1} should be allowed (under limit)"
        
        # 101st request should be denied
        permitted, reason = await rate_limiter.check_rate_limit("test_agent", "agent")
        assert permitted is False, "Request 101 should be denied (over limit)"
        assert "Rate limit exceeded" in reason, "Should indicate rate limit exceeded"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_no_race_condition(self, rate_limiter):
        """
        CRITICAL TEST: Verify that 1000 concurrent requests are correctly tracked.
        
        Without asyncio.Lock, this test would fail because multiple tasks would:
        1. Read tokens = N
        2. Decrement tokens = N-1
        3. Write tokens = N-1
        
        But both tasks would read the same N, resulting in only 1 token consumed
        instead of 2, allowing more requests than the limit.
        
        With asyncio.Lock, all operations are atomic.
        """
        limiter = RateLimiter()
        
        # Reset bucket to start with 0 Docker commands (very restrictive)
        limiter.limits["docker_command"]["max_requests"] = 10
        
        successful_requests = []
        failed_requests = []
        
        async def make_request(task_id):
            """Simulate concurrent request"""
            permitted, reason = await limiter.check_rate_limit(
                "docker_commands",
                resource_type="docker_command"
            )
            if permitted:
                successful_requests.append(task_id)
            else:
                failed_requests.append(task_id)
        
        # Create 100 concurrent tasks (much more than limit of 10)
        tasks = [make_request(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        # Verify that exactly 10 succeeded and 90 failed
        assert len(successful_requests) == 10, \
            f"Should allow exactly 10 requests, got {len(successful_requests)}"
        assert len(failed_requests) == 90, \
            f"Should deny exactly 90 requests, got {len(failed_requests)}"
    
    @pytest.mark.asyncio
    async def test_massive_concurrent_load(self, rate_limiter):
        """
        Stress test: 1000 concurrent tasks all contending for locks
        
        This simulates the original race condition scenario where many agents
        try to make requests simultaneously. Without asyncio.Lock, this would
        allow more than the configured limit.
        """
        limiter = RateLimiter()
        limiter.limits["api_call"]["max_requests"] = 200  # 200 per 60s
        
        success_count = [0]  # Use list to allow mutation in nested function
        
        async def stress_request(task_id):
            """Make a request and track success"""
            permitted, _ = await limiter.check_rate_limit(
                "api_endpoint",
                resource_type="api_call"
            )
            if permitted:
                success_count[0] += 1
        
        # Create 1000 tasks (5x the limit)
        tasks = [stress_request(i) for i in range(1000)]
        await asyncio.gather(*tasks)
        
        # Should allow exactly 200, not more
        assert success_count[0] == 200, \
            f"Stress test: Expected 200 successful requests, got {success_count[0]}"
    
    @pytest.mark.asyncio
    async def test_different_resource_types_independent(self, rate_limiter):
        """Verify that different resource types have independent limits"""
        # Agent limit: 100 per 60s
        # Docker limit: 50 per 60s
        
        agent_count = 0
        docker_count = 0
        
        # Exhaust agent limit (100)
        for i in range(100):
            permitted, _ = await rate_limiter.check_rate_limit("agent1", "agent")
            if permitted:
                agent_count += 1
        
        # Exhaust docker limit (50)
        for i in range(50):
            permitted, _ = await rate_limiter.check_rate_limit("docker", "docker_command")
            if permitted:
                docker_count += 1
        
        assert agent_count == 100, f"Agent requests: expected 100, got {agent_count}"
        assert docker_count == 50, f"Docker requests: expected 50, got {docker_count}"
        
        # Both should be exhausted now
        agent_denied, _ = await rate_limiter.check_rate_limit("agent1", "agent")
        docker_denied, _ = await rate_limiter.check_rate_limit("docker", "docker_command")
        
        assert agent_denied is False, "Agent limit should be exhausted"
        assert docker_denied is False, "Docker limit should be exhausted"


class TestRateLimitErrorHandling:
    """Test error handling in rate limiter"""
    
    @pytest.mark.asyncio
    async def test_unknown_resource_type_allowed(self, rate_limiter):
        """Unknown resource types should pass through (no limit configured)"""
        permitted, reason = await rate_limiter.check_rate_limit(
            "unknown_resource",
            resource_type="unknown_type"
        )
        assert permitted is True, "Unknown resource type should be allowed"
        assert reason == "", "No reason needed for passthrough"
    
    @pytest.mark.asyncio
    async def test_reset_bucket(self, rate_limiter):
        """Verify that reset_bucket works correctly"""
        # Exhaust the bucket
        for i in range(100):
            await rate_limiter.check_rate_limit("reset_test", "agent")
        
        # Verify it's exhausted
        permitted, _ = await rate_limiter.check_rate_limit("reset_test", "agent")
        assert permitted is False, "Bucket should be exhausted"
        
        # Reset the bucket
        rate_limiter.reset_bucket("reset_test", "agent")
        
        # Verify it's replenished
        permitted, _ = await rate_limiter.check_rate_limit("reset_test", "agent")
        assert permitted is True, "Bucket should be replenished after reset"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
