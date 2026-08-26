"""Static lint for the frozen S1-R v2 protocol; no environment/checkpoint use."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "drtp_s1r_protocol_v2"
REL = ROOT / "artifacts" / "drtp_reliability_a0"
DOC = ROOT / "docs" / "DRTP_S1R_PROTOCOL_V2_FROZEN.md"
REQUIRED = (
    "frozen_contract.json", "gb_selection.json", "rng_tuples.json",
    "eval_manifest.json", "tp50_manifest.json",
)
VAGUE = ("TBD", "reasonable", "meaningful", "significant improvement",
         "clear improvement", "substantial", "approximately", "if needed")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    for name in REQUIRED:
        checks.append((f"artifact exists: {name}", (ART / name).is_file(), ""))
    contract = json.loads((ART / "frozen_contract.json").read_text(encoding="utf-8"))
    selection = json.loads((ART / "gb_selection.json").read_text(encoding="utf-8"))
    rng = json.loads((ART / "rng_tuples.json").read_text(encoding="utf-8"))
    evaluation = json.loads((ART / "eval_manifest.json").read_text(encoding="utf-8"))
    tp50 = json.loads((ART / "tp50_manifest.json").read_text(encoding="utf-8"))
    checks.extend([
        ("historical v1 preserved", contract["history"]["v1_preserved"] and not contract["history"]["v1_overwritten"], ""),
        ("machine-generated G/B", selection["selection_is_machine_generated"], ""),
        ("selected G/B distinct", selection["selected"]["G"] != selection["selected"]["B"], ""),
        ("selected G eligible", next(c for c in selection["candidates"] if c["seed"] == selection["selected"]["G"])["G_eligible"], ""),
        ("selected B eligible", next(c for c in selection["candidates"] if c["seed"] == selection["selected"]["B"])["B_eligible"], ""),
        ("selected G is 2001", selection["selected"]["G"] == 2001, ""),
        ("selected B is 2002", selection["selected"]["B"] == 2002, ""),
        ("12 scientific runs", contract["scientific_runs"]["total_runs"] == 12, ""),
        ("budget arithmetic", contract["scientific_runs"]["max_scientific_env_steps"] == 12 * 1000192, ""),
        ("milestone alignment", contract["scientific_runs"]["milestones"] == [250048, 500096, 750144, 1000192], ""),
        ("six RNG streams", rng["streams"] == ["init", "env", "action", "minibatch", "topology", "eval"], ""),
        ("G RNG tuple complete", set(rng["tuples"]["G"]) == {"master_seed", "init_seed", "env_seed", "action_seed", "minibatch_seed", "topology_seed", "eval_seed"}, ""),
        ("B RNG tuple complete", set(rng["tuples"]["B"]) == {"master_seed", "init_seed", "env_seed", "action_seed", "minibatch_seed", "topology_seed", "eval_seed"}, ""),
        ("evaluation imports five tapes", len(evaluation["tapes"]) == 5, ""),
        ("TP50 count", tp50["count"] == 50 and len(tp50["episodes"]) == 50, ""),
        ("training disabled", contract["training_started"] is False and rng["training_started"] is False, ""),
        ("evaluation disabled", contract["evaluation_started"] is False and evaluation["evaluation_started"] is False, ""),
    ])
    for tape in evaluation["tapes"]:
        src = ROOT / tape["source"]
        checks.append((f"tape hash {tape['label']}", src.is_file() and sha(src) == tape["source_sha256"], ""))
    text = DOC.read_text(encoding="utf-8")
    for term in VAGUE:
        checks.append((f"no undefined vague gate term: {term}", term.lower() not in text.lower(), ""))
    passed = sum(ok for _, ok, _ in checks)
    status = "PASS" if passed == len(checks) else "FAIL"
    lines = [
        "# DRTP S1-R Protocol v2 Validation Report", "", f"## Status: `{status}`", "",
        "This is static protocol validation only. No evaluator, environment, checkpoint, telemetry smoke, or training process was started.", "",
        f"Checks: `{passed}/{len(checks)}` passed.", "", "| Check | Result |", "|---|---|",
    ]
    for name, ok, _ in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    lines += ["", "`TRAINING STARTED = NO`", "", "`EVALUATION STARTED = NO`", ""]
    (ROOT / "docs" / "DRTP_S1R_PROTOCOL_V2_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(status)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
