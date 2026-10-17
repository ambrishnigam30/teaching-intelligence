from __future__ import annotations

import os
import warnings
from pathlib import Path
from tempfile import NamedTemporaryFile
from io import BytesIO

def is_secret_bearing_file(path_str: str) -> bool:
    """Detect if a file path or name could carry secrets, tokens, or credentials."""
    lower = path_str.lower()
    return any(
        pattern in lower
        for pattern in (
            "secret",
            "token",
            "credential",
            ".env",
            "password",
            "api_key",
            "apikey",
        )
    )


class HuggingFaceVault:
    """Canonical private Dataset storage for ledgers and generated packages."""
    def __init__(self, repo_id: str, token: str, api: Any = None, spill_dir: Path | None = None):
        if not repo_id or not token: raise ValueError("HF_DATASET_REPO and HF_TOKEN are required")
        self.repo_id, self.token = repo_id, token
        self.api = api
        self.spill_dir = Path(spill_dir) if spill_dir else Path("state/hf_spill")

    def _save_to_spill(self, files: dict[str, bytes]) -> None:
        self.spill_dir.mkdir(parents=True, exist_ok=True)
        for dest, content in files.items():
            if is_secret_bearing_file(dest):
                continue
            spill_file = self.spill_dir / dest.replace("/", "__")
            spill_file.parent.mkdir(parents=True, exist_ok=True)
            spill_file.write_bytes(content)

    def _flush_spillover(self, message: str = "Flush spillover") -> bool:
        return self.commit_bytes({}, message=message)

    @classmethod
    def from_environment(cls) -> "HuggingFaceVault":
        return cls(os.environ["HF_DATASET_REPO"], os.environ["HF_TOKEN"])

    def ensure_private(self) -> None:
        from huggingface_hub import HfApi
        client = self.api or HfApi(token=self.token)
        client.create_repo(self.repo_id, repo_type="dataset", private=True, exist_ok=True)

    def upload_bytes(self, destination: str, content: bytes, message: str) -> None:
        from huggingface_hub import HfApi
        client = self.api or HfApi(token=self.token)
        with NamedTemporaryFile(delete=False) as output:
            output.write(content); path = Path(output.name)
        try:
            client.upload_file(path_or_fileobj=str(path), path_in_repo=destination, repo_id=self.repo_id, repo_type="dataset", commit_message=message)
        finally:
            path.unlink(missing_ok=True)

    def upload_file(self, destination: str, source: Path, message: str) -> None:
        from huggingface_hub import HfApi
        client = self.api or HfApi(token=self.token)
        client.upload_file(path_or_fileobj=str(source), path_in_repo=destination, repo_id=self.repo_id, repo_type="dataset", commit_message=message)

    def commit_bytes(
        self,
        files: dict[str, bytes],
        message: str,
        max_retries: int = 4,
        force: bool = False,
        spill_dir: Path | None = None,
    ) -> bool:
        """Atomically checkpoint a batch in one Hub commit, enforcing commit interval and spillover protection."""
        effective_spill = spill_dir or self.spill_dir
        if not files and not (effective_spill.exists() and any(effective_spill.iterdir())):
            return True

        effective_spill.mkdir(parents=True, exist_ok=True)

        # Stage incoming files in spill directory to protect against memory loss / crashes
        for dest, content in files.items():
            if is_secret_bearing_file(dest):
                continue
            spill_file = effective_spill / dest.replace("/", "__")
            spill_file.parent.mkdir(parents=True, exist_ok=True)
            spill_file.write_bytes(content)

        import time
        import random
        from huggingface_hub import CommitOperationAdd, HfApi

        # Reconstruct all staged operations from spill directory, filtering out forbidden files
        operations = []
        for spill_file in effective_spill.glob("*"):
            if spill_file.is_file():
                dest = spill_file.name.replace("__", "/")
                if is_secret_bearing_file(dest):
                    spill_file.unlink(missing_ok=True)
                    continue
                operations.append(CommitOperationAdd(path_in_repo=dest, path_or_fileobj=spill_file.read_bytes()))

        if not operations:
            return True

        backoff = 15.0
        client = self.api or HfApi(token=self.token)
        for attempt in range(max_retries):
            try:
                client.create_commit(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    operations=operations,
                    commit_message=message,
                )
                # Success: clear the spill directory
                for spill_file in effective_spill.glob("*"):
                    if spill_file.is_file():
                        spill_file.unlink(missing_ok=True)
                return True
            except Exception as exc:
                response = getattr(exc, "response", None)
                status_code = getattr(response, "status_code", None)
                if status_code == 429:
                    jitter = random.uniform(0.8, 1.2)
                    wait_time = backoff * jitter
                    if attempt < max_retries - 1:
                        warnings.warn(
                            f"Hugging Face 429 rate limit hit. Backing off for {wait_time:.1f}s (attempt {attempt+1}/{max_retries})...",
                            RuntimeWarning,
                        )
                        time.sleep(wait_time)
                        backoff *= 2.0
                        continue
                    warnings.warn(
                        "Hugging Face commit rate limit reached; staged files preserved in state/hf_spill for next run.",
                        RuntimeWarning,
                    )
                    return False
                raise
        return False

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

    def checkpoint_ledger(self, ledger_json: str, message: str) -> bool:
        return self.commit_bytes({"state/corpus_ledger.json": ledger_json.encode("utf-8")}, message)
