from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = (
    "configs/paper/main_gate1.yaml",
    "configs/paper/mappo.yaml",
    "configs/paper/single_graph.yaml",
    "configs/paper/ea_rg_mappo.yaml",
    "configs/paper/param_matched_single.yaml",
    "configs/paper/happo.yaml",
    "configs/paper/ippo.yaml",
    "configs/paper/ablation_no_role_pair.yaml",
    "configs/paper/ablation_no_task_support.yaml",
    "configs/paper/ablation_no_role_identity.yaml",
    "configs/paper/checkpoint_selection_schema.yaml",
    "envs/uav_intercept_3d_env.py",
    "envs/__init__.py",
    "algorithms/ri_gmappo/simple_ri_gmappo.py",
    "scripts/train_ri_gmappo.py",
    "scripts/train_happo_baseline.py",
    "scripts/evaluate_happo_3d.py",
    "scripts/evaluate_happo_checkpoint_sweep.py",
    "scripts/evaluate_ri_gmappo_3d.py",
    "scripts/evaluate_3d_checkpoint_sweep.py",
    "scripts/audit_paper_configs.py",
    "scripts/audit_checkpoint_selection_schema.py",
    "scripts/generate_paper_commands.py",
    "scripts/audit_paper_manifest.py",
    "scripts/audit_training_outputs.py",
    "scripts/run_paper_manifest.py",
    "scripts/start_paper_manifest_job.py",
    "scripts/check_paper_manifest_jobs.py",
    "scripts/check_training_progress.py",
    "scripts/summarize_training_logs.py",
    "scripts/gate_validation_readiness.py",
    "scripts/run_manifest_training_chunk.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(args: list[str]) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    except Exception as exc:  # pragma: no cover - defensive provenance fallback
        return f"unavailable: {exc}"
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write paper-run provenance hashes for configs and critical code.")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "paper_run_provenance.csv")
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "paper_run_provenance.md")
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for rel in args.files:
        path = ROOT / rel
        rows.append(
            {
                "path": rel,
                "exists": str(path.exists()),
                "sha256": sha256_file(path) if path.exists() else "",
                "bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("path", "exists", "sha256", "bytes"))
        writer.writeheader()
        writer.writerows(rows)

    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_value(["rev-parse", "HEAD"]),
        "git_status_short": git_value(["status", "--short"]),
    }
    lines = [
        "# Paper Run Provenance",
        "",
        "```json",
        json.dumps(meta, ensure_ascii=False, indent=2),
        "```",
        "",
        "| Path | Exists | SHA256 | Bytes |",
        "|---|---:|---|---:|",
    ]
    for row in rows:
        lines.append(f"| `{row['path']}` | {row['exists']} | `{row['sha256']}` | {row['bytes']} |")
    lines.append("")
    args.out_md.write_text("\n".join(lines), encoding="utf-8")

    print(args.out_csv)
    print(args.out_md)
    print(f"hashed files: {len(rows)}")


if __name__ == "__main__":
    main()
