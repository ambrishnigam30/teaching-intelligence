from __future__ import annotations

import os
import warnings
from pathlib import Path
from tempfile import NamedTemporaryFile
from io import BytesIO

class HuggingFaceVault:
    """Canonical private Dataset storage for ledgers and generated packages."""
    def __init__(self, repo_id: str, token: str):
        if not repo_id or not token: raise ValueError("HF_DATASET_REPO and HF_TOKEN are required")
        self.repo_id, self.token = repo_id, token

    @classmethod
    def from_environment(cls) -> "HuggingFaceVault":
        return cls(os.environ["HF_DATASET_REPO"], os.environ["HF_TOKEN"])

    def ensure_private(self) -> None:
        from huggingface_hub import HfApi
        HfApi(token=self.token).create_repo(self.repo_id, repo_type="dataset", private=True, exist_ok=True)

    def upload_bytes(self, destination: str, content: bytes, message: str) -> None:
        from huggingface_hub import HfApi
        with NamedTemporaryFile(delete=False) as output:
            output.write(content); path = Path(output.name)
        try:
            HfApi(token=self.token).upload_file(path_or_fileobj=str(path), path_in_repo=destination, repo_id=self.repo_id, repo_type="dataset", commit_message=message)
        finally:
            path.unlink(missing_ok=True)

    def upload_file(self, destination: str, source: Path, message: str) -> None:
        from huggingface_hub import HfApi
        HfApi(token=self.token).upload_file(path_or_fileobj=str(source), path_in_repo=destination, repo_id=self.repo_id, repo_type="dataset", commit_message=message)

    def commit_bytes(self, files: dict[str, bytes], message: str) -> None:
        """Atomically checkpoint a page batch in one Hub commit to stay within free-tier commit limits."""
        if not files: return
        from huggingface_hub import CommitOperationAdd, HfApi
        operations = [CommitOperationAdd(path_in_repo=destination, path_or_fileobj=content) for destination, content in files.items()]
        try:
            HfApi(token=self.token).create_commit(repo_id=self.repo_id, repo_type="dataset", operations=operations, commit_message=message)
        except Exception as exc:
            response = getattr(exc, "response", None)
            if getattr(response, "status_code", None) == 429:
                warnings.warn("Hugging Face commit rate limit reached; local ledger and STATUS.md remain available for the next run.", RuntimeWarning)
                return
            raise

    def download_bytes(self, source: str) -> bytes | None:
        from huggingface_hub import HfApi
        api = HfApi(token=self.token)
        try:
            local_path = api.hf_hub_download(self.repo_id, source, repo_type="dataset", token=self.token)
            return Path(local_path).read_bytes()
        except Exception as exc:
            if exc.__class__.__name__ in {"EntryNotFoundError", "RepositoryNotFoundError"}: return None
            raise

    def restore_ledger(self, local_path: Path) -> bool:
        data = self.download_bytes("state/corpus_ledger.json")
        if data is None: return False
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        return True

    def checkpoint_ledger(self, ledger_json: str, message: str) -> None:
        self.upload_bytes("state/corpus_ledger.json", ledger_json.encode("utf-8"), message)
