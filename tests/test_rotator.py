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

def test_from_environment_supports_up_to_20_and_openrouter_fallback():
    env = {
        "GEMINI_API_KEY_1": "g1",
        "GROQ_API_KEY_1": "gr1",
        "OPENROUTER_API_1": "or1",  # fallback typo
        "GEMINI_API_KEY_20": "g20",
        "GROQ_API_KEY_20": "gr20",
        "OPENROUTER_API_KEY_20": "or20",
    }
    pool = KeyPool.from_environment(env)
    labels = [k.label for k in pool.keys]
    assert labels == ["gemini_1", "groq_1", "openrouter_1", "gemini_20", "groq_20", "openrouter_20"]
    assert pool.keys[2].value == "or1"

def test_shortest_cooldown_wait():
    now = datetime.now(timezone.utc)
    pool = KeyPool([ProviderKey("gemini", 1, "x"), ProviderKey("groq", 1, "y")])
    assert pool.shortest_cooldown_wait(now) == 0.0
    pool.cooldown(pool.keys[0], 60, now)
    # groq is still available
    assert pool.shortest_cooldown_wait(now) == 0.0
    # put groq on 30s cooldown
    pool.cooldown(pool.keys[1], 30, now)
    # shortest cooldown wait should be 30.0s
    assert abs(pool.shortest_cooldown_wait(now) - 30.0) < 0.01

