# Mentora Teaching Intelligence — Operating Contract

## 1. Mission
Produce governed, teacher-ready and runtime-ready JEE/NEET teaching packages from founder-authorized Drive material.

## 2. Founder operating limit
All setup commands are documented verbatim; cloud processing continues independently after setup.

## 3. Artifact namespaces
`K`, `E`, `S`, `D`, and `P` remain physically and logically separated. `UNKNOWN` is retained whenever evidence is insufficient.

## 4. Rights policy
The 13 registered founder Drive roots, including recursively resolved shortcuts, are `FOUNDER_LICENSED_COMMERCIAL` unless a file override applies. Unverified external web sources are `UNKNOWN`.

## 5. Drive access
Use read-only user OAuth with parent-scoped queries, Shared Drive flags, recursive shortcut resolution, and content hashes.

## 6. Extraction policy
Never trust legacy PDF text for STEM symbols. Render at 300 DPI and use the cloud Vision path on every run; private Kaggle is an optional batch accelerator.

## 7. Kaggle privacy
The notebook metadata is private. Secrets must be Kaggle private secrets; source material and crops move only through the private HF dataset.

## 8. Chapter fusion
Map all files to the 82-chapter canonical spine. Compile each chapter from theory, reference, handbook, exercise, and test evidence where available.

## 9. Priority policy
Process all eligible files for the highest-priority incomplete chapter before lower-tier work.

## 10. Assurance gates
Promotion is monotonic from Source-ready to Efficacy-validated. Missing, conflicting, or clipped material is quarantined.

## 11. Verification policy
Use cross-family blind solving plus SymPy/RDKit checks; unkeyed drills require three-way consensus.

## 12. Assessment safety
Role locking prevents mock-test items from appearing in class material.

## 13. Package contract
Teacher/runtime packages contain all 18 capabilities, the nine-point concept standard, five-phase reasoning, hints, board recipes, and persona-safe scripts.

## 14. Cloud resilience
Free-tier capacity exhaustion becomes `PENDING_QUOTA`; the immutable ledger resumes next run without reducing quality.

## 15. Concurrent execution
GitHub Actions uses one non-cancelling concurrency group to serialize ledger checkpoints and status commits.

## 16. Founder launch commands
Expected success output: `14 passed`, `Private Hugging Face Dataset verified.`, then `Launch complete: GitHub Actions has been triggered.`

```powershell
Copy-Item .env.keys.example .env.keys
python scripts/auth_google_drive.py --scopes https://www.googleapis.com/auth/drive.readonly
powershell -ExecutionPolicy Bypass -File scripts/launch_cloud_factory.ps1
```
