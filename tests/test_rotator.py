from datetime import datetime, timezone
import pytest
from src.rotator.key_pool import KeyPool, ProviderKey, QuotaExhausted

def test_interleaved_order_and_cross_family_exclusion():
    pool = KeyPool([ProviderKey(f, n, "x") for n in range(1, 3) for f in ("gemini", "groq", "openrouter")])
    assert [pool.acquire().label for _ in range(6)] == ["gemini_1", "groq_1", "openrouter_1", "gemini_2", "groq_2", "openrouter_2"]
    assert pool.acquire(exclude_family="gemini").family != "gemini"

def test_all_keys_on_cooldown_checkpoints():
    now = datetime.now(timezone.utc)
    pool = KeyPool([ProviderKey("gemini", 1, "x")])
    pool.cooldown(pool.keys[0], 60, now)
    with pytest.raises(QuotaExhausted): pool.acquire(now=now)
