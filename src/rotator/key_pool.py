from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
import random
from typing import Iterable

class QuotaExhausted(RuntimeError): pass

@dataclass
class ProviderKey:
    family: str
    ordinal: int
    value: str
    cooldown_until: datetime | None = None
    failures: int = 0

    @property
    def label(self) -> str: return f"{self.family}_{self.ordinal}"
    def available(self, now: datetime) -> bool: return self.cooldown_until is None or self.cooldown_until <= now

@dataclass
class KeyPool:
    keys: list[ProviderKey]
    jitter_seconds: tuple[float, float] = (0.1, 0.8)
    _cursor: int = field(default=0, init=False)

    @classmethod
    def from_environment(cls, env: dict[str, str] | None = None) -> "KeyPool":
        env = env or os.environ
        keys = [ProviderKey(family, ordinal, env[f"{family.upper()}_API_KEY_{ordinal}"])
                for ordinal in range(1, 6)
                for family in ("gemini", "groq", "openrouter")
                if env.get(f"{family.upper()}_API_KEY_{ordinal}")]
        return cls(keys)

    def acquire(self, exclude_family: str | None = None, now: datetime | None = None) -> ProviderKey:
        now = now or datetime.now(timezone.utc)
        for offset in range(len(self.keys)):
            index = (self._cursor + offset) % len(self.keys)
            candidate = self.keys[index]
            if candidate.family != exclude_family and candidate.available(now):
                self._cursor = (index + 1) % len(self.keys)
                return candidate
        raise QuotaExhausted("No eligible provider key is available; checkpoint work as PENDING_QUOTA")

    def cooldown(self, key: ProviderKey, seconds: int, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        key.failures += 1
        key.cooldown_until = now + timedelta(seconds=seconds)

    def jitter(self) -> float:
        return random.uniform(*self.jitter_seconds)
