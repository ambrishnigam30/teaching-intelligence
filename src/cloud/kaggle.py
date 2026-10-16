from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

class KaggleDispatcher:
    def __init__(self, worker_dir: Path):
        self.worker_dir = worker_dir

    @property
    def configured(self) -> bool:
        return bool(self.discover_accounts())

    @staticmethod
    def discover_accounts(env: dict[str, str] | None = None) -> list[tuple[str, str, int]]:
        """Collect (username, key, index) from unnumbered and numbered 1..5 env vars, deduplicated by username."""
        env = env or os.environ
        seen_usernames: set[str] = set()
        accounts: list[tuple[str, str, int]] = []

        u = env.get("KAGGLE_USERNAME", "").strip()
        k = env.get("KAGGLE_KEY", "").strip()
        if u and k:
            seen_usernames.add(u)
            accounts.append((u, k, 0))

        for i in range(1, 6):
            u_i = env.get(f"KAGGLE_USERNAME_{i}", "").strip()
            k_i = env.get(f"KAGGLE_KEY_{i}", "").strip()
            if u_i and k_i and u_i not in seen_usernames:
                seen_usernames.add(u_i)
                accounts.append((u_i, k_i, len(accounts)))

        return accounts

    def dispatch(self, input_manifest: dict) -> str:
        accounts = self.discover_accounts()
        if not accounts:
            raise RuntimeError("Kaggle credentials unavailable; API vision path remains active")
        manifest = self.worker_dir / "input_manifest.json"
        manifest.write_text(json.dumps(input_manifest), encoding="utf-8")
        try:
            result = subprocess.run(["kaggle", "kernels", "push", "-p", str(self.worker_dir)], check=True, capture_output=True, text=True)
            return result.stdout.strip()
        finally:
            manifest.unlink(missing_ok=True)

    def dispatch_fleet(self, base_manifest: dict) -> list[str]:
        """Dispatch parallel GPU kernels across all discovered Kaggle accounts with sharded work."""
        accounts = self.discover_accounts()
        if not accounts:
            return []
        shard_count = len(accounts)
        dispatched_outputs: list[str] = []
        for username, key, shard_idx in accounts:
            with TemporaryDirectory(prefix=f"kaggle-shard-{shard_idx}-") as temp_dir_str:
                kernel_dir = Path(temp_dir_str)
                slug = f"mentora-intelligence-worker-shard-{shard_idx}"
                metadata = {
                    "id": f"{username}/{slug}",
                    "title": f"Mentora Intelligence Worker Shard {shard_idx}",
                    "code_file": "worker.py",
                    "language": "python",
                    "kernel_type": "script",
                    "is_private": True,
                    "enable_gpu": True,
                    "enable_tpu": False,
                    "enable_internet": True,
                    "dataset_sources": [],
                    "competition_sources": [],
                    "kernel_sources": [],
                }
                (kernel_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

                worker_script_src = self.worker_dir / "worker.py"
                if not worker_script_src.exists():
                    worker_script_src = Path("scripts/kaggle_worker/worker.py")
                code = worker_script_src.read_text(encoding="utf-8") if worker_script_src.exists() else "# Default worker\nprint('Worker initialized')\n"

                injected_header = f"""# Auto-injected Kaggle Fleet Shard Configuration
import os
os.environ.setdefault("SHARD_INDEX", "{shard_idx}")
os.environ.setdefault("SHARD_COUNT", "{shard_count}")
os.environ.setdefault("ENABLE_LOCAL_OLLAMA", "1")
os.environ.setdefault("CONTINUOUS_HF_CHECKPOINT", "1")
os.environ.setdefault("AUTO_SKIP_DISCOVERY_IF_POPULATED", "1")
"""
                (kernel_dir / "worker.py").write_text(injected_header + code, encoding="utf-8")

                manifest = dict(base_manifest)
                manifest.update({"shard_index": shard_idx, "shard_count": shard_count, "private": True})
                (kernel_dir / "input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

                env = os.environ.copy()
                env["KAGGLE_USERNAME"] = username
                env["KAGGLE_KEY"] = key
                try:
                    res = subprocess.run(["kaggle", "kernels", "push", "-p", str(kernel_dir)], env=env, capture_output=True, text=True, check=True)
                    dispatched_outputs.append(res.stdout.strip())
                except subprocess.CalledProcessError as exc:
                    err_msg = exc.stderr or exc.stdout or str(exc)
                    dispatched_outputs.append(f"Shard {shard_idx} ({username}) push failed: {err_msg.strip()}")
                except Exception as exc:
                    dispatched_outputs.append(f"Shard {shard_idx} ({username}) error: {str(exc)}")
        return dispatched_outputs
