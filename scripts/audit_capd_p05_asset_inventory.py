from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "capd_p05_asset_inventory.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_run_directories(search_root: Path, expected_names: set[str]) -> dict[str, list[Path]]:
    matches = {name: [] for name in expected_names}
    for directory, child_dirs, _ in os.walk(search_root):
        child_dirs[:] = [name for name in child_dirs if name not in {".git", "__pycache__"}]
        path = Path(directory)
        if path.name in expected_names and path.parent.name in {"utr_sg", "egtr_sg"}:
            matches[path.name].append(path)
    return matches


def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def audit(search_root: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    expected_names = {f"seed{seed}" for seed in contract["seeds"]}
    candidates = find_run_directories(search_root, expected_names)
    rows: list[dict[str, Any]] = []
    for arm in contract["arms"]:
        for seed in contract["seeds"]:
            name = f"seed{seed}"
            arm_candidates = [path for path in candidates[name] if path.parent.name == arm]
            complete_candidates = [
                path
                for path in arm_candidates
                if all((path / filename).is_file() for filename in contract["required_files"])
            ]
            selected = complete_candidates[0] if len(complete_candidates) == 1 else None
            rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "candidate_count": len(arm_candidates),
                    "complete_candidate_count": len(complete_candidates),
                    "selected_run_directory": str(selected.resolve()) if selected else None,
                    "required_files": {
                        filename: bool(selected and (selected / filename).is_file())
                        for filename in contract["required_files"]
                    },
                    "provenance_files": {
                        filename: bool(selected and (selected / filename).is_file())
                        for filename in contract["provenance_files_if_present"]
                    },
                    "checkpoint_sha256": sha256(selected / "actor_critic_latest.pt") if selected else None,
                    "status": "complete" if selected else ("ambiguous" if len(complete_candidates) > 1 else "missing_or_incomplete"),
                }
            )
    complete = sum(row["status"] == "complete" for row in rows)
    missing = len(rows) - complete
    verdict = "CAPD_P05_ASSETS_READY_FOR_SIGNAL_AUDIT" if missing == 0 else "CAPD_P05_BLOCKED_ASSETS_NOT_LOCAL"
    result = {
        "protocol": contract["protocol"],
        "verdict": verdict,
        "search_root": str(search_root.resolve()),
        "expected_teacher_runs": len(rows),
        "complete_teacher_runs": complete,
        "missing_or_ambiguous_teacher_runs": missing,
        "runs": rows,
        "interpretation": "Missing local assets mean archival incompleteness, not experiment failure or algorithm failure.",
        "checkpoint_loading_performed": False,
        "policy_signal_analysis_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "evaluation_started": False,
        "student_training_started": False,
        "automatic_continuation": False,
    }
    json_output = output_dir / "CAPD_P05_LOCAL_ASSET_INVENTORY.json"
    report_output = output_dir / "CAPD_P05_LOCAL_ASSET_INVENTORY.md"
    if json_output.exists() or report_output.exists():
        raise FileExistsError(f"refusing to overwrite existing P0.5 inventory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_lf(json_output, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    missing_rows = [f"- `{row['arm']}/seed{row['seed']}`" for row in rows if row["status"] != "complete"]
    report = [
        "# CAPD P0.5 local teacher-asset inventory",
        "",
        f"**Verdict:** `{verdict}`.",
        "",
        f"Found `{complete}/{len(rows)}` required UTR/EGTR teacher runs locally.",
        "",
        "A missing local checkpoint is an archival blocker only. It does not mean that the cloud experiment did not run, and it is not evidence against CAPD, EGTR or UTR.",
        "",
        "No checkpoint was loaded, no policy output was computed, and no evaluation artifact was read.",
        "",
        "## Missing or ambiguous runs",
        "",
        *(missing_rows or ["None."]),
        "",
        "## Next boundary",
        "",
        "Recover the frozen 10M run assets from the original AutoDL data disk or a previously downloaded result archive. Re-run this inventory against the extracted root. Only an all-complete inventory may proceed to architecture/hash verification and the separately frozen training-only consensus-signal audit.",
        "",
        "Student implementation, distillation, PPO training and evaluation remain unauthorized.",
    ]
    write_lf(report_output, "\n".join(report) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "capd_p05_20260904")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    result = audit(args.search_root, args.output_dir)
    print(json.dumps({key: result[key] for key in ("verdict", "expected_teacher_runs", "complete_teacher_runs")}))


if __name__ == "__main__":
    main()
