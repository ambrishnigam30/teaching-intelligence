[CmdletBinding()]
param([string]$EnvFile = ".env.keys")
$ErrorActionPreference = "Stop"
if (!(Test-Path $EnvFile)) { throw "Create $EnvFile from .env.keys.example and fill every required value." }
Get-Content $EnvFile | ForEach-Object { if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1])" -Value $matches[2] } }
$required = @("HF_TOKEN", "HF_DATASET_REPO", "KAGGLE_USERNAME", "KAGGLE_KEY")
$required += 1..5 | ForEach-Object { "GEMINI_API_KEY_$_"; "GROQ_API_KEY_$_"; "OPENROUTER_API_KEY_$_" }
$missing = $required | Where-Object { [string]::IsNullOrWhiteSpace((Get-Item "Env:$_" -ErrorAction SilentlyContinue).Value) }
if ($missing) { throw "Missing required keys: $($missing -join ', ')" }
if (!(Test-Path $env:GOOGLE_DRIVE_TOKEN_PATH)) { throw "Run scripts/auth_google_drive.py first to create $env:GOOGLE_DRIVE_TOKEN_PATH." }
python -m pip install -e ".[cloud,vision,verify,test]"
python -c "import pytest; raise SystemExit(pytest.main(['-q']))"
gh secret set -f $EnvFile
gh secret set GOOGLE_DRIVE_TOKEN_JSON --body (Get-Content -Raw $env:GOOGLE_DRIVE_TOKEN_PATH)
python -c "from src.cloud.hf_vault import HuggingFaceVault; import os; v=HuggingFaceVault(os.environ['HF_DATASET_REPO'], os.environ['HF_TOKEN']); v.ensure_private(); print('Private Hugging Face Dataset verified.')"
git add .
git commit -m "feat: initialize Mentora intelligence factory" 2>$null
git branch -M main
git push -u origin main
gh workflow run intelligence_factory.yml
Write-Output "Launch complete: GitHub Actions has been triggered."
