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
        keys: list[ProviderKey] = []
        for ordinal in range(1, 21):
            for family in ("gemini", "groq", "openrouter"):
                val = env.get(f"{family.upper()}_API_KEY_{ordinal}")
                if not val and family == "openrouter":
                    val = env.get(f"OPENROUTER_API_{ordinal}")
                if val:
                    keys.append(ProviderKey(family, ordinal, val))
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

    def shortest_cooldown_wait(self, now: datetime | None = None) -> float:
        if not self.keys:
            return 0.0
        now = now or datetime.now(timezone.utc)
        if any(k.available(now) for k in self.keys):
            return 0.0
        cooling = [k for k in self.keys if k.cooldown_until is not None]
        if not cooling:
            return 0.0
        return max(0.0, (min(k.cooldown_until for k in cooling) - now).total_seconds())

    def jitter(self) -> float:
        return random.uniform(*self.jitter_seconds)
