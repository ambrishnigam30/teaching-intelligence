from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

class HuggingFaceVault:
    """Canonical private Dataset storage for ledgers and generated packages."""
    def __init__(self, repo_id: str, token: str):
        if not repo_id or not token: raise ValueError("HF_DATASET_REPO and HF_TOKEN are required")
        self.repo_id, self.token = repo_id, token

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

    def download_bytes(self, source: str) -> bytes | None:
        from huggingface_hub import HfApi
        api = HfApi(token=self.token)
        try:
            local_path = api.hf_hub_download(self.repo_id, source, repo_type="dataset", token=self.token)
            return Path(local_path).read_bytes()
        except Exception as exc:
            if exc.__class__.__name__ in {"EntryNotFoundError", "RepositoryNotFoundError"}: return None
            raise
