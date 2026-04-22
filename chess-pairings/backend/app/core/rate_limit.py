from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

from fastapi import HTTPException


@dataclass(frozen=True)
class RateLimitRule:
    max_attempts: int
    window_seconds: int
    detail: str


_attempt_buckets: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(scope: str, key: str, rule: RateLimitRule) -> None:
    bucket = _attempt_buckets[f"{scope}:{key}"]
    now = monotonic()
    while bucket and now - bucket[0] > rule.window_seconds:
        bucket.popleft()
    if len(bucket) >= rule.max_attempts:
        raise HTTPException(status_code=429, detail=rule.detail)
    bucket.append(now)


def reset_rate_limits() -> None:
    _attempt_buckets.clear()
