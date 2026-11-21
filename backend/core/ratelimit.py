"""
Minimal sliding-window rate limiter for auth endpoints.

In-process only: good enough for one API instance. Behind several workers,
move this to Redis (or the reverse proxy) — noted for Phase 1 deployment.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            retry = int(self.window - (now - hits[0])) + 1
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many attempts, try again later",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


def client_key(request: Request, extra: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{extra}"


login_limiter = RateLimiter(limit=10, window_seconds=300)
otp_send_limiter = RateLimiter(limit=5, window_seconds=600)
otp_verify_limiter = RateLimiter(limit=10, window_seconds=600)
