"""Build the audited, minimal AutoDL package for the P2 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = "EPISTEMIC_COMMITMENT_P2_PILOT"
FILES = (
    "algorithms/__init__.py",
    "algorithms/epistemic_commitment.py",
    "algorithms/epistemic_commitment_objective.py",
    "envs/__init__.py",
    "envs/uav_intercept_3d_env.py",
    "envs/epistemic_commitment_uav_shadow_env.py",
    "envs/epistemic_commitment_trainable_env.py",
    "scripts/run_epistemic_commitment_p1g_smoke.py",
    "scripts/run_epistemic_commitment_p2_pilot.py",
    "scripts/verify_epistemic_commitment_p2_preflight.py",
    "scripts/launch_epistemic_commitment_p2_pilot_autodl.sh",
    "configs/epistemic_commitment_p2_pilot_freeze_20260909.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1B_ANALYTIC_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1C_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1D_KERNEL_AUDIT_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1E_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1F_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1G_RESULT.json",
    "docs/strong_q2_clean_sheet_p0_20260909/P1H_P2_EXECUTION_CONTRACT.md",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "cloud_packages" / "EPISTEMIC_COMMITMENT_P2_PILOT_V1.zip",
    )
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(args.output.suffix + ".sha256").exists():
        raise FileExistsError(f"refusing to overwrite package: {args.output}")
    payloads = {name: (ROOT / name).read_bytes() for name in FILES}
    # The repository-level envs initializer imports unrelated legacy
    # environments.  A minimal cloud package must keep package initialization
    # side-effect free rather than silently pulling in those dependencies.
    payloads["envs/__init__.py"] = b'"""Minimal P2 pilot environment package."""\n'
    manifest = {
        "protocol": "EPISTEMIC-COMMITMENT-P2-PILOT-PACKAGE-V1",
        "package_root": PACKAGE_ROOT,
        "files": {name: digest(data) for name, data in payloads.items()},
        "formal_training_started": False,
        "automatic_continuation": False,
    }
    readme = """# Epistemic Commitment P2 pilot

This package runs six CPU-bound frozen pilot trajectories (two methods x three seeds),
then fixed-endpoint evaluation and seed-level aggregation. It does not select checkpoints,
revise hyperparameters, add seeds, or continue automatically after the pilot verdict.

From the extracted package root:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \\
OUTPUT_ROOT=results/development/epistemic_commitment_p2_pilot \\
MAX_PARALLEL=6 PYTHON_BIN=python \\
bash scripts/launch_epistemic_commitment_p2_pilot_autodl.sh
```
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payloads.items():
            archive.writestr(f"{PACKAGE_ROOT}/{name}", data)
        archive.writestr(
            f"{PACKAGE_ROOT}/PACKAGE_MANIFEST.json",
            json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8") + b"\n",
        )
        archive.writestr(f"{PACKAGE_ROOT}/README_CLOUD.md", readme.encode("utf-8"))
    package_hash = digest(args.output.read_bytes())
    checksum = args.output.with_suffix(args.output.suffix + ".sha256")
    checksum.write_text(f"{package_hash}  {args.output.name}\n", encoding="ascii")
    print(json.dumps({"package": str(args.output), "sha256": package_hash}, indent=2))


if __name__ == "__main__":
    main()
