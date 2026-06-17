"""
认证限流属性测试与边界测试。
"""
from app.services.rate_limit import SlidingWindowRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_login_failed_limiter_allows_ten_failures_then_returns_retry_after() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(limit=10, window_seconds=15 * 60, clock=clock)

    for _ in range(10):
        assert limiter.hit("ip:127.0.0.1").allowed

    blocked = limiter.hit("ip:127.0.0.1")

    assert not blocked.allowed
    assert blocked.retry_after == 15 * 60


def test_login_failed_limiter_does_not_count_successful_checks() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(limit=10, window_seconds=15 * 60, clock=clock)

    for _ in range(100):
        assert limiter.check("ip:127.0.0.1").allowed

    for _ in range(10):
        assert limiter.hit("ip:127.0.0.1").allowed

    assert not limiter.hit("ip:127.0.0.1").allowed


def test_limiter_window_expires_and_allows_new_attempts() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60, clock=clock)

    assert limiter.hit("email:user@example.com").allowed
    assert limiter.hit("email:user@example.com").allowed
    assert not limiter.hit("email:user@example.com").allowed

    clock.advance(61)

    assert limiter.hit("email:user@example.com").allowed


def test_limiter_keys_are_independent_for_password_reset_email_scope() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)

    assert limiter.hit("email:a@example.com").allowed
    assert limiter.hit("email:b@example.com").allowed
    assert not limiter.hit("email:a@example.com").allowed


def test_successful_login_can_clear_failed_attempts() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)

    assert limiter.hit("ip:127.0.0.1").allowed
    assert not limiter.hit("ip:127.0.0.1").allowed

    limiter.clear("ip:127.0.0.1")

    assert limiter.hit("ip:127.0.0.1").allowed
