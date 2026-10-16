import json

from src.drive.auth import _token_payload


def test_token_payload_uses_disk_token_when_actions_secret_is_empty(tmp_path, monkeypatch):
    token_file = tmp_path / "token.json"
    token_file.write_text(json.dumps({"token": "opaque", "refresh_token": "refresh"}), encoding="utf-8")
    monkeypatch.setenv("GOOGLE_DRIVE_TOKEN_JSON", "")
    monkeypatch.setenv("GOOGLE_DRIVE_TOKEN_PATH", str(token_file))
    payload, source = _token_payload()
    assert payload["token"] == "opaque"
    assert source == token_file


def test_explicit_actions_secret_takes_precedence_over_disk_token(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token":"disk"}', encoding="utf-8")
    payload, source = _token_payload('{"token":"secret"}', str(token_file))
    assert payload["token"] == "secret"
    assert source is None
