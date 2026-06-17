"""
认证相关精确限流工具。

MVP 使用进程内滑动窗口计数；后续多副本部署时应替换为 Redis 后端。
"""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import monotonic
from typing import Callable, Deque, Dict


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int = 0


@dataclass
class SlidingWindowRateLimiter:
    limit: int
    window_seconds: int
    clock: Callable[[], float] = monotonic
    _events: Dict[str, Deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def _prune(self, key: str, now: float) -> Deque[float]:
        events = self._events[key]
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        return events

    def check(self, key: str) -> RateLimitResult:
        now = self.clock()
        events = self._prune(key, now)
        if len(events) < self.limit:
            return RateLimitResult(allowed=True)

        retry_after = max(1, int(self.window_seconds - (now - events[0])))
        return RateLimitResult(allowed=False, retry_after=retry_after)

    def hit(self, key: str) -> RateLimitResult:
        result = self.check(key)
        if not result.allowed:
            return result

        self._events[key].append(self.clock())
        return RateLimitResult(allowed=True)

    def clear(self, key: str) -> None:
        self._events.pop(key, None)


login_failed_limiter = SlidingWindowRateLimiter(limit=10, window_seconds=15 * 60)
password_reset_limiter = SlidingWindowRateLimiter(limit=5, window_seconds=60 * 60)
register_limiter = SlidingWindowRateLimiter(limit=10, window_seconds=60 * 60)
