"""Test atomic Hugging Face commit batching, multi-file CommitOperationAdd, and spillover handling."""
from pathlib import Path
from unittest.mock import MagicMock, patch
from huggingface_hub import CommitOperationAdd

from src.cloud.hf_vault import HuggingFaceVault

def test_atomic_commit_batches_multiple_files_into_single_commit(tmp_path):
    mock_api = MagicMock()
    vault = HuggingFaceVault("test/repo", "hf_test_token", api=mock_api, spill_dir=tmp_path / "spill")

    files = {
        "intelligence/chapters/kinematics/doc1/page-0001.jsonl": b'{"page": 1}\n',
        "intelligence/chapters/kinematics/doc1/page-0002.jsonl": b'{"page": 2}\n',
        "assets/images/doc1/diagram-01.png": b"\x89PNG\r\n\x1a\nfakeimage1",
        "assets/images/doc1/diagram-02.png": b"\x89PNG\r\n\x1a\nfakeimage2",
    }

    vault.commit_bytes(files, "Atomic batch of 4 files")

    # create_commit must be called exactly once
    assert mock_api.create_commit.call_count == 1
    call_kwargs = mock_api.create_commit.call_args[1]
    assert call_kwargs["repo_id"] == "test/repo"
    assert call_kwargs["commit_message"] == "Atomic batch of 4 files"

    operations = call_kwargs["operations"]
    assert len(operations) == 4
    for op in operations:
        assert isinstance(op, CommitOperationAdd)
        assert op.path_in_repo in files

def test_spillover_directory_saves_and_clears_on_flush(tmp_path):
    mock_api = MagicMock()
    spill_dir = tmp_path / "spill_test"
    vault = HuggingFaceVault("test/repo", "hf_test_token", api=mock_api, spill_dir=spill_dir)

    files = {"test/file.txt": b"important payload"}
    vault._save_to_spill(files)

    # Verify file saved on disk in spill dir
    spill_files = [f for f in spill_dir.glob("*") if f.is_file()]
    assert len(spill_files) == 1

    # Flush spillover
    vault._flush_spillover()
    assert mock_api.create_commit.call_count == 1
    # Spill directory should now be empty
    assert len([f for f in spill_dir.glob("*") if f.is_file()]) == 0


def test_is_secret_bearing_file_detection():
    from src.cloud.hf_vault import is_secret_bearing_file

    assert is_secret_bearing_file("state/.mentora_secrets.json")
    assert is_secret_bearing_file("token.json")
    assert is_secret_bearing_file("credentials.json")
    assert is_secret_bearing_file(".env.keys")
    assert is_secret_bearing_file(".env")
    assert is_secret_bearing_file("path/to/my_api_key.txt")
    assert is_secret_bearing_file("gemini_apikey.json")
    assert is_secret_bearing_file("user_password.hash")

    # Safe files must not trigger detection
    assert not is_secret_bearing_file("state/corpus_ledger.json")
    assert not is_secret_bearing_file("intelligence/chapters/kinematics/doc1/page-0001.jsonl")
    assert not is_secret_bearing_file("STATUS.md")
    assert not is_secret_bearing_file("AUTONOMOUS_FINAL_REPORT.md")


def test_commit_bytes_filters_out_secrets_and_purges_spill(tmp_path):
    mock_api = MagicMock()
    spill_dir = tmp_path / "spill_security"
    spill_dir.mkdir(parents=True, exist_ok=True)

    # Pre-populate spill with an old secret file that might have caused 400 Bad Request
    old_secret_spill = spill_dir / "state__.mentora_secrets.json"
    old_secret_spill.write_bytes(b'{"HF_TOKEN": "secret_val"}')
    assert old_secret_spill.exists()

    vault = HuggingFaceVault("test/repo", "hf_test_token", api=mock_api, spill_dir=spill_dir)

    # Attempt to commit files, including secret-bearing files
    files = {
        "state/corpus_ledger.json": b'{"items": []}',
        "state/.mentora_secrets.json": b'{"HF_TOKEN": "bad_leak"}',
        "token.json": b'{"refresh_token": "ya29.xyz"}',
    }

    success = vault.commit_bytes(files, "Safe commit test")
    assert success is True

    # The offending spill file must have been unlinked/purged
    assert not old_secret_spill.exists()

    # The commit operations must ONLY contain non-secret files
    call_kwargs = mock_api.create_commit.call_args[1]
    operations = call_kwargs["operations"]
    committed_paths = [op.path_in_repo for op in operations]

    assert "state/corpus_ledger.json" in committed_paths
    assert "state/.mentora_secrets.json" not in committed_paths
    assert "token.json" not in committed_paths

