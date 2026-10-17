import base64
import io
import json
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch
import zipfile

from src.cloud.kaggle import (
    KaggleDispatcher,
    bundle_src_as_base64,
    collect_runtime_secrets,
    generate_worker_script,
)


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
    assert dispatcher.configured is not None


def test_bundle_src_as_base64(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("print('hello')", encoding="utf-8")
    (src_dir / "__pycache__").mkdir()
    (src_dir / "__pycache__" / "temp.pyc").write_bytes(b"compiled")

    b64 = bundle_src_as_base64(tmp_path)
    assert isinstance(b64, str)
    raw = base64.b64decode(b64)
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        names = zf.namelist()
        assert "src/module.py" in names
        assert not any("__pycache__" in n or n.endswith(".pyc") for n in names)


def test_collect_runtime_secrets(tmp_path):
    env = {
        "HF_TOKEN": "hf_secret",
        "HF_DATASET_REPO": "mentora/vault",
        "GEMINI_API_KEY_1": "gem_key",
    }
    (tmp_path / "token.json").write_text('{"token": "test_token"}', encoding="utf-8")
    secrets = collect_runtime_secrets(tmp_path, env)
    assert secrets["HF_TOKEN"] == "hf_secret"
    assert secrets["HF_DATASET_REPO"] == "mentora/vault"
    assert secrets["GEMINI_API_KEY_1"] == "gem_key"
    assert "GOOGLE_DRIVE_TOKEN_JSON" in secrets
    assert "test_token" in secrets["GOOGLE_DRIVE_TOKEN_JSON"]


def test_generate_worker_script():
    script = generate_worker_script(
        shard_idx=1,
        shard_count=4,
        src_b64="VGVzdFNyYw==",
        secrets={"HF_TOKEN": "mock_token"},
    )
    assert "SHARD_INDEX = 1" in script
    assert "SHARD_COUNT = 4" in script
    assert "VGVzdFNyYw==" in script
    assert "ollama" in script and "serve" in script
    assert "qwen2.5vl:7b" in script
    assert "--shard-index" in script


def test_dispatch_fleet_gpu_and_cpu_fallback(tmp_path):
    env = {
        "KAGGLE_USERNAME_1": "user_gpu",
        "KAGGLE_KEY_1": "key_gpu",
        "KAGGLE_USERNAME_2": "user_cpu",
        "KAGGLE_KEY_2": "key_cpu",
    }
    dispatcher = KaggleDispatcher(tmp_path)

    # Simulate: first account succeeds on GPU; second account fails on GPU then succeeds on CPU fallback
    def mock_run(cmd, *args, **kwargs):
        call_env = kwargs.get("env", {})
        u = call_env.get("KAGGLE_USERNAME")
        k = call_env.get("KAGGLE_KEY")
        cfg_dir = Path(call_env.get("KAGGLE_CONFIG_DIR", ""))
        assert cfg_dir.exists(), f"KAGGLE_CONFIG_DIR {cfg_dir} must exist"
        kaggle_json = json.loads((cfg_dir / "kaggle.json").read_text(encoding="utf-8"))
        assert kaggle_json["username"] == u
        assert kaggle_json["key"] == k
        assert call_env.get("KAGGLE_API_TOKEN") is not None

        if u == "user_gpu":
            return subprocess.CompletedProcess(cmd, 0, stdout="Kernel pushed successfully", stderr="")
        elif u == "user_cpu":
            kernel_dir = Path(cmd[cmd.index("-p") + 1])
            meta = json.loads((kernel_dir / "kernel-metadata.json").read_text(encoding="utf-8"))
            if meta.get("enable_gpu") in (True, "true"):
                raise subprocess.CalledProcessError(1, cmd, stderr="GPU quota exceeded or phone not verified")
            return subprocess.CompletedProcess(cmd, 0, stdout="Kernel pushed on CPU fallback", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="OK", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        results = dispatcher.dispatch_fleet({}, env=env)
        assert len(results) == 2
        assert "GPU" in results[0] and "Kernel pushed successfully" in results[0]
        assert "CPU Fallback" in results[1] and "Kernel pushed on CPU fallback" in results[1]
