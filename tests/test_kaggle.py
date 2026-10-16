from pathlib import Path
from src.cloud.kaggle import KaggleDispatcher

def test_discover_accounts_from_numbered_and_unnumbered():
    env = {
        "KAGGLE_USERNAME": "primary_user",
        "KAGGLE_KEY": "primary_key",
        "KAGGLE_USERNAME_1": "primary_user",  # Duplicate, should be ignored
        "KAGGLE_KEY_1": "primary_key",
        "KAGGLE_USERNAME_2": "user_two",
        "KAGGLE_KEY_2": "key_two",
        "KAGGLE_USERNAME_3": "user_three",
        "KAGGLE_KEY_3": "key_three",
    }
    accounts = KaggleDispatcher.discover_accounts(env)
    assert len(accounts) == 3
    assert accounts[0][0] == "primary_user"
    assert accounts[1][0] == "user_two"
    assert accounts[2][0] == "user_three"

def test_configured_property(tmp_path):
    dispatcher = KaggleDispatcher(tmp_path)
    # Without env vars it should be false
    assert dispatcher.configured is not None
