"""Read-only audit of formal-training checkpoint-selection recoverability."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "formal_v1_8"

RUNS = (
    ("EA-RG", "ea_rg", "multi_relation"),
    ("wider single-graph", "single", "single"),
    ("matched non-graph", "matched_nongraph", "matched_nongraph"),
)


def read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    diagnostic_lines = [
        "# VALIDATION_TRAJECTORY_SELECTION_AUDIT_V1_8", "",
        "Read-only reconstruction from training-time `train_log.csv` files. No validation was rerun.", "",
        "RMST80, RMST220, and censoring-aware endpoint values were not written at training-time; they are shown as `UNAVAILABLE`. The logged timeout rate is reported separately and is not substituted as censoring.", "",
    ]
    audit_lines = [
        "# CHECKPOINT_SELECTION_RECOVERABILITY_AUDIT_V1_8", "",
        "**Decision: CHECKPOINT_SELECTION_NOT_RECOVERABLE.** This is a read-only audit; no training, validation rerun, held-out evaluation, architecture/protocol change, or paper edit was performed.", "",
        "## Frozen selector inputs required", "",
        "The prespecified selector requires RMST80, establishment probability with censoring, RMST220, and earlier-update tie-break at every validation point. The immutable formal training logs contain only `eval_success_rate`, `eval_timeout_rate`, `eval_avg_steps`, and `eval_avg_distance`; RMST80/RMST220 and censoring-aware event times are absent.", "",
        "Therefore the counterfactual prespecified winner update cannot be computed from existing logs. Update 300 cannot be accepted as a post-hoc terminal rule.", "",
        "## Run-level result", "",
        "| method | seed | prespecified winner update | update300 rank | winner metrics | update300 metrics | category |", "|---|---:|---:|---|---|---|---|",
    ]
    artifact_lines = ["", "## Artifact provenance", "", "Only final/latest artifacts and the final training state are present. The `actor_critic_update_0300.pt` files were copied after training for validation and are not immutable periodic snapshots. No earlier update artifact is present.", ""]
    for method, prefix, _encoder in RUNS:
        for seed in range(3):
            run = RESULTS / f"{prefix}_seed{seed}"
            rows = read_rows(run / "train_log.csv")
            points = [r for r in rows if str(r.get("eval_success_rate", "")).strip() != ""]
            diagnostic_lines += [f"## {method} — seed {seed}", "", "| update | RMST80 | establishment probability (logged) | censoring-aware rate | RMST220 | logged timeout rate |", "|---:|---:|---:|---:|---:|---:|"]
            for r in points:
                diagnostic_lines.append(f"| {r['update']} | UNAVAILABLE | {r['eval_success_rate']} | UNAVAILABLE | UNAVAILABLE | {r['eval_timeout_rate']} |")
            diagnostic_lines += ["", "Interpretation: the logged establishment and timeout columns are engineering validation outputs; they do not reconstruct the frozen RMST selector.", ""]

            files = sorted(run.glob("actor_critic*.pt"))
            inv = []
            for path in files:
                inv.append(f"`{path.name}` sha256=`{digest(path)[:16]}…` size={path.stat().st_size}")
            artifact_lines.append(f"### {method} — seed {seed}")
            artifact_lines.extend([f"- {x}" for x in inv] if inv else ["- no actor artifact found"])
            artifact_lines.append("- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`")
            audit_lines.append(f"| {method} | {seed} | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |")
    audit_lines.extend(artifact_lines)
    audit_lines += [
        "## Overall decision", "",
        "Because RMST trajectory values are missing, all 9 runs are conservatively classified as category C. The audit cannot determine whether snapshot omission was outcome-neutral.", "",
        "Protocol-repair proposal (not executed): rerun the same frozen training matrix with `--save-snapshots`, preserve validation endpoint logs including RMST/censoring fields at every 10-update point, then apply the unchanged selector. Do not accept update 300 as a new terminal rule.",
    ]
    (ROOT / "docs" / "VALIDATION_TRAJECTORY_SELECTION_AUDIT_V1_8.md").write_text("\n".join(diagnostic_lines), encoding="utf-8")
    (ROOT / "docs" / "CHECKPOINT_SELECTION_RECOVERABILITY_AUDIT_V1_8.md").write_text("\n".join(audit_lines), encoding="utf-8")
    print("CHECKPOINT_SELECTION_RECOVERABILITY_AUDIT_V1_8: CHECKPOINT_SELECTION_NOT_RECOVERABLE")
    print("immutable validation points audited:", sum(sum(1 for r in read_rows(RESULTS / f"{prefix}_seed{seed}" / "train_log.csv") if str(r.get("eval_success_rate", "")).strip()) for _, prefix, _ in RUNS for seed in range(3)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
