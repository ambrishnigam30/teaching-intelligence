#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${1:-.env.keys}"
test -f "$ENV_FILE" || { echo "Create $ENV_FILE from .env.keys.example and fill it."; exit 1; }
set -a; source "$ENV_FILE"; set +a
for name in HF_TOKEN HF_DATASET_REPO KAGGLE_USERNAME KAGGLE_KEY; do
  test -n "${!name:-}" || { echo "Missing required key: $name"; exit 1; }
done
for family in GEMINI GROQ OPENROUTER; do
  for ordinal in 1 2 3 4 5; do
    name="${family}_API_KEY_${ordinal}"
    test -n "${!name:-}" || { echo "Missing required key: $name"; exit 1; }
  done
done
test -f "${GOOGLE_DRIVE_TOKEN_PATH:-token.json}" || { echo "Run scripts/auth_google_drive.py first."; exit 1; }
python -m pip install -e '.[cloud,vision,verify,test]'
python -c "import pytest; raise SystemExit(pytest.main(['-q']))"
gh secret set -f "$ENV_FILE"
gh secret set GOOGLE_DRIVE_TOKEN_JSON < "${GOOGLE_DRIVE_TOKEN_PATH:-token.json}"
python -c "from src.cloud.hf_vault import HuggingFaceVault; import os; v=HuggingFaceVault(os.environ['HF_DATASET_REPO'], os.environ['HF_TOKEN']); v.ensure_private(); print('Private Hugging Face Dataset verified.')"
git add .
git commit -m 'feat: initialize Mentora intelligence factory' || true
git branch -M main
git push -u origin main
gh workflow run intelligence_factory.yml
echo "Launch complete: GitHub Actions has been triggered."
