from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

class KaggleDispatcher:
    def __init__(self, worker_dir: Path): self.worker_dir = worker_dir
    @property
    def configured(self) -> bool: return bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))
    def dispatch(self, input_manifest: dict) -> str:
        if not self.configured: raise RuntimeError("Kaggle credentials unavailable; API vision path remains active")
        manifest = self.worker_dir / "input_manifest.json"
        manifest.write_text(json.dumps(input_manifest), encoding="utf-8")
        try:
            result = subprocess.run(["kaggle", "kernels", "push", "-p", str(self.worker_dir)], check=True, capture_output=True, text=True)
            return result.stdout.strip()
        finally:
            manifest.unlink(missing_ok=True)
