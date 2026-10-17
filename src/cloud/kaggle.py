from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import zipfile


def bundle_src_as_base64(root_dir: Path) -> str:
    """Create an in-memory zip archive of the src/ package and return it base64-encoded."""
    src_dir = root_dir / "src"
    if not src_dir.exists() and Path("src").exists():
        src_dir = Path("src")
        root_dir = src_dir.parent
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in src_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".pyc") and "__pycache__" not in file_path.parts:
                arcname = file_path.relative_to(root_dir).as_posix()
                zf.write(file_path, arcname)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def collect_runtime_secrets(root_dir: Path, env: dict[str, str] | None = None) -> dict[str, str]:
    """Gather runtime secrets to embed in worker scripts from env and .env.keys."""
    if env is not None:
        merged_env = dict(env)
    else:
        merged_env = dict(os.environ)
        env_keys_path = root_dir / ".env.keys"
        if not env_keys_path.exists():
            env_keys_path = Path(".env.keys")
        if env_keys_path.exists():
            for line in env_keys_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    merged_env.setdefault(k.strip(), v.strip())

    token_json_str = merged_env.get("GOOGLE_DRIVE_TOKEN_JSON", "")
    if not token_json_str:
        for candidate in [root_dir / "token.json", Path("token.json")]:
            if candidate.is_file():
                token_json_str = candidate.read_text(encoding="utf-8")
                break

    secret_keys = [
        "HF_TOKEN",
        "HF_DATASET_REPO",
        "GOOGLE_OAUTH_CLIENT_SECRETS",
        "GOOGLE_DRIVE_TOKEN_PATH",
    ]
    for i in range(1, 6):
        secret_keys.extend([f"GEMINI_API_KEY_{i}", f"GROQ_API_KEY_{i}", f"OPENROUTER_API_KEY_{i}"])

    collected: dict[str, str] = {}
    if token_json_str:
        collected["GOOGLE_DRIVE_TOKEN_JSON"] = token_json_str
        collected["GOOGLE_DRIVE_TOKEN_PATH"] = "token.json"

    for k in secret_keys:
        val = merged_env.get(k, "").strip()
        if val:
            collected[k] = val

    for k, v in merged_env.items():
        if (k.startswith("GEMINI_API_") or k.startswith("GROQ_API_") or k.startswith("OPENROUTER_API_")) and v:
            collected[k] = v

    return collected


def generate_worker_script(shard_idx: int, shard_count: int, src_b64: str, secrets: dict[str, str] | None = None, hf_token: str = "", hf_repo: str = "") -> str:
    """Generate self-contained worker.py that securely fetches runtime keys into memory from HF vault."""
    secrets_map = secrets or {}
    bootstrap_token = hf_token or secrets_map.get("HF_TOKEN", "")
    bootstrap_repo = hf_repo or secrets_map.get("HF_DATASET_REPO", "")

    return f'''# Auto-generated self-contained Mentora Intelligence Worker
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import zipfile

SHARD_INDEX = {shard_idx}
SHARD_COUNT = {shard_count}
BOOTSTRAP_HF_TOKEN = ""
BOOTSTRAP_HF_REPO = "{bootstrap_repo}"
SRC_BUNDLE_B64 = "{src_b64}"

def unpack_source() -> None:
    print("[Worker] Unpacking src/ package...")
    raw = base64.b64decode(SRC_BUNDLE_B64)
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        zf.extractall(".")
    print("[Worker] Unpacked src/ successfully.")

def check_network_connectivity() -> bool:
    print("[Worker] Checking outbound internet connectivity...")
    try:
        req = urllib.request.Request("https://huggingface.co", headers={{"User-Agent": "MentoraWorker/1.0"}})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("[Worker] Outbound network verified.")
            return True
    except Exception as exc:
        print(f"[Worker Error] Outbound network check failed: {{exc}}")
        print("[Worker Error] Note: On Kaggle, outbound internet requires SMS phone-verified accounts.")
        print("[Worker Error] Please verify phone number under kaggle.com -> Account Settings.")
        return False

def setup_environment() -> bool:
    print("[Worker] Setting up environment variables and credentials securely...")
    os.environ["SHARD_INDEX"] = str(SHARD_INDEX)
    os.environ["SHARD_COUNT"] = str(SHARD_COUNT)
    os.environ["ENABLE_LOCAL_OLLAMA"] = "1"
    os.environ["AUTO_SKIP_DISCOVERY_IF_POPULATED"] = "1"
    os.environ["CONTINUOUS_HF_CHECKPOINT"] = "1"

    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            from kaggle_secrets import UserSecretsClient
            token = UserSecretsClient().get_secret("HF_TOKEN")
        except Exception:
            token = BOOTSTRAP_HF_TOKEN

    repo = os.environ.get("HF_DATASET_REPO") or BOOTSTRAP_HF_REPO
    if token:
        os.environ["HF_TOKEN"] = token
    if repo:
        os.environ["HF_DATASET_REPO"] = repo

    if not check_network_connectivity():
        return False

    if token and repo:
        url = f"https://huggingface.co/datasets/{{repo}}/raw/main/state/.mentora_secrets.json"
        try:
            req = urllib.request.Request(url, headers={{"Authorization": f"Bearer {{token}}"}})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for k, v in data.items():
                    if v:
                        os.environ.setdefault(k, str(v))
                print(f"[Worker] Ingested {{len(data)}} runtime secrets into memory securely.")
        except Exception as exc:
            print(f"[Worker] Vault retrieval note: {{exc}}")

    token_json = os.environ.get("GOOGLE_DRIVE_TOKEN_JSON")
    if token_json:
        token_path = Path("token.json")
        token_path.write_text(token_json, encoding="utf-8")
        try:
            os.chmod("token.json", 0o600)
        except Exception:
            pass
        os.environ["GOOGLE_DRIVE_TOKEN_PATH"] = "token.json"
        print("[Worker] Written token.json securely from in-memory vault.")
    return True

def install_dependencies() -> None:
    print("[Worker] Installing runtime dependencies...")
    pkgs = [
        "pymupdf",
        "pillow",
        "httpx",
        "pydantic",
        "huggingface_hub",
        "google-api-python-client",
        "google-auth-oauthlib",
        "sympy",
        "rdkit",
    ]
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "-q"] + pkgs
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Worker] Warning during pip install: {{res.stderr[:200]}}")

def setup_ollama() -> None:
    if sys.platform.startswith("linux"):
        try:
            print("[Worker] Installing Ollama...")
            subprocess.run(["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"], check=False)
            print("[Worker] Starting Ollama daemon...")
            subprocess.Popen(["ollama", "serve"])
            time.sleep(5)
            print("[Worker] Pulling vision model (qwen2.5vl:7b with fallbacks)...")
            subprocess.run(
                ["sh", "-c", "ollama pull qwen2.5vl:7b || ollama pull qwen2.5vl:3b || ollama pull moondream || true"],
                check=False,
            )
        except Exception as exc:
            print(f"[Worker] Ollama setup warning: {{exc}}")

def main() -> None:
    print(f"=== Starting Mentora Worker Shard {{SHARD_INDEX}}/{{SHARD_COUNT}} ===")
    if not setup_environment():
        print("[Worker] Setup halted cleanly due to missing network connectivity.")
        sys.exit(0)
    unpack_source()
    install_dependencies()
    setup_ollama()

    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--skip-discovery",
        "--max-pages", "2000",
        "--time-budget-seconds", "39600",
        "--shard-index", str(SHARD_INDEX),
        "--shard-count", str(SHARD_COUNT),
    ]
    print(f"[Worker] Executing pipeline: {{' '.join(cmd)}}")
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
'''


class KaggleDispatcher:
    def __init__(self, worker_dir: Path | None = None):
        self.worker_dir = worker_dir or Path(".")

    @property
    def configured(self) -> bool:
        return bool(self.discover_accounts())

    @staticmethod
    def discover_accounts(env: dict[str, str] | None = None) -> list[tuple[str, str, int]]:
        """Collect (username, key, index) from numbered 1..5 and unnumbered env vars, deduplicated by username."""
        env_map = dict(os.environ) if env is None else dict(env)
        if env is None and Path(".env.keys").exists():
            for line in Path(".env.keys").read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_map.setdefault(k.strip(), v.strip())

        seen_usernames: set[str] = set()
        accounts: list[tuple[str, str, int]] = []

        # Check numbered accounts 1..5 first to guarantee deterministic ordering
        for i in range(1, 6):
            u_i = env_map.get(f"KAGGLE_USERNAME_{i}", "").strip()
            k_i = env_map.get(f"KAGGLE_KEY_{i}", "").strip()
            if u_i and k_i and u_i not in seen_usernames:
                seen_usernames.add(u_i)
                accounts.append((u_i, k_i, len(accounts)))

        # Also check unnumbered KAGGLE_USERNAME / KAGGLE_KEY if not already discovered
        u = env_map.get("KAGGLE_USERNAME", "").strip()
        k = env_map.get("KAGGLE_KEY", "").strip()
        if u and k and u not in seen_usernames:
            seen_usernames.add(u)
            accounts.append((u, k, len(accounts)))

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

    def dispatch_fleet(self, base_manifest: dict, env: dict[str, str] | None = None) -> list[str]:
        """Dispatch parallel GPU kernels across all discovered Kaggle accounts with sharded work."""
        if env is not None:
            env_map = dict(env)
        else:
            env_map = dict(os.environ)
            env_keys_path = self.worker_dir / ".env.keys"
            if not env_keys_path.exists():
                env_keys_path = Path(".env.keys")
            if env_keys_path.exists():
                for line in env_keys_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_map.setdefault(k.strip(), v.strip())

        accounts = self.discover_accounts(env_map)
        if not accounts:
            return []

        shard_count = len(accounts)
        src_b64 = bundle_src_as_base64(self.worker_dir)
        secrets = collect_runtime_secrets(self.worker_dir, env_map)

        hf_token = secrets.get("HF_TOKEN")
        hf_repo = secrets.get("HF_DATASET_REPO")
        if hf_token and hf_repo:
            try:
                from src.cloud.hf_vault import HuggingFaceVault
                HuggingFaceVault(hf_repo, hf_token).upload_secret_bundle(secrets)
            except Exception as exc:
                print(f"[Dispatcher] Note on HF vault secret upload: {exc}")
        dispatched_outputs: list[str] = []
        for username, key, shard_idx in accounts:
            with TemporaryDirectory(prefix=f"kaggle-shard-{shard_idx}-") as temp_dir_str:
                root_temp = Path(temp_dir_str)
                kernel_dir = root_temp / "kernel"
                config_dir = root_temp / "config"
                kernel_dir.mkdir(parents=True, exist_ok=True)
                config_dir.mkdir(parents=True, exist_ok=True)

                # Isolated kaggle credentials for this specific account
                (config_dir / "kaggle.json").write_text(
                    json.dumps({"username": username, "key": key}, indent=2),
                    encoding="utf-8",
                )
                if key.startswith("KGAT_"):
                    (config_dir / "access_token").write_text(key, encoding="utf-8")
                    (config_dir / "access_token.txt").write_text(key, encoding="utf-8")

                slug = f"mentora-intelligence-worker-shard-{shard_idx}"
                metadata = {
                    "id": f"{username}/{slug}",
                    "title": f"mentora-intelligence-worker-shard-{shard_idx}",
                    "code_file": "worker.py",
                    "language": "python",
                    "kernel_type": "script",
                    "is_private": "true",
                    "enable_gpu": "true",
                    "enable_internet": "true",
                    "dataset_sources": [],
                    "competition_sources": [],
                    "kernel_sources": [],
                    "model_sources": [],
                }
                meta_file = kernel_dir / "kernel-metadata.json"
                meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

                worker_code = generate_worker_script(shard_idx, shard_count, src_b64, secrets)
                (kernel_dir / "worker.py").write_text(worker_code, encoding="utf-8")

                manifest = dict(base_manifest)
                manifest.update({"shard_index": shard_idx, "shard_count": shard_count, "private": True})
                (kernel_dir / "input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

                run_env = os.environ.copy()
                run_env["KAGGLE_CONFIG_DIR"] = str(config_dir)
                run_env["KAGGLE_USERNAME"] = username
                run_env["KAGGLE_KEY"] = key
                if key.startswith("KGAT_"):
                    run_env["KAGGLE_API_TOKEN"] = key
                else:
                    run_env["KAGGLE_API_TOKEN"] = "bypass_home_token"

                push_cmd = ["kaggle", "kernels", "push", "-p", str(kernel_dir)]
                try:
                    res = subprocess.run(push_cmd, env=run_env, capture_output=True, text=True, check=True)
                    dispatched_outputs.append(f"Shard {shard_idx} ({username}) [GPU]: {res.stdout.strip()}")
                except subprocess.CalledProcessError as exc:
                    err_msg = (exc.stderr or exc.stdout or str(exc)).strip()
                    # Fallback to CPU if GPU push is rejected
                    try:
                        metadata["enable_gpu"] = "false"
                        meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                        fallback_res = subprocess.run(push_cmd, env=run_env, capture_output=True, text=True, check=True)
                        dispatched_outputs.append(
                            f"Shard {shard_idx} ({username}) [CPU Fallback]: {fallback_res.stdout.strip()}"
                        )
                    except Exception as fallback_exc:
                        fallback_err = getattr(fallback_exc, "stderr", None) or str(fallback_exc)
                        dispatched_outputs.append(
                            f"Shard {shard_idx} ({username}) push failed on GPU ({err_msg}) and CPU ({str(fallback_err).strip()})"
                        )
                except Exception as exc:
                    dispatched_outputs.append(f"Shard {shard_idx} ({username}) error: {str(exc)}")
        return dispatched_outputs
