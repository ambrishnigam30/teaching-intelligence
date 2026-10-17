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
