"""Freeze S1-R protocol v2 from already archived REL-A0 assets.

This script reads JSON artifacts only.  It does not load checkpoints, create an
environment, run an evaluator, or start a training process.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "drtp_s1r_protocol_v2"
REL = ROOT / "artifacts" / "drtp_reliability_a0"
RNG_ARTIFACT = ROOT / "artifacts" / "drtp_seed_s1" / "rng_stream_regression.json"
RNG_SOURCE = ROOT / "algorithms" / "ri_gmappo" / "rng_streams.py"
METRICS = ("f0", "timing", "duration", "compound")
FAILURE_METRICS = ("F0", "TIMING", "DURATION", "COMPOUND")
TAPES = ("T0", "T1", "T2", "T3", "T4")
SEEDS = (1901, 1902, 2001, 2002, 2003)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_cells() -> dict[tuple[int, str, str, str], dict]:
    decision = json.loads((REL / "rel_a0_decision.json").read_text(encoding="utf-8"))
    cells = {}
    for row in decision["cell_summary"]:
        cells[(int(row["training_seed"]), row["method"], row["tape"], row["condition"])] = row
    expected = len(SEEDS) * 2 * len(TAPES) * 5
    if len(cells) != expected:
        raise RuntimeError(f"REL-A0 cell count {len(cells)} != {expected}")
    return cells


def tape_summary(cells: dict, seed: int, tape: str, method: str) -> dict:
    rows = {r["condition"]: cells[(seed, method, tape, r["condition"])] for r in []}
    # The explicit condition loop keeps the imported REL-A0 cell contract visible.
    rows = {
        condition: cells[(seed, method, tape, condition)]
        for condition in ("nominal", *METRICS)
    }
    return {
        "returns": {m: rows[m]["J"] for m in METRICS},
        "timeouts": {m: rows[m]["timeout"] for m in METRICS},
        "timeout_mean_failure": sum(rows[m]["timeout"] for m in METRICS) / 4.0,
        "nominal_return": rows["nominal"]["J"],
    }


def build_candidates(cells: dict) -> list[dict]:
    candidates = []
    for seed in SEEDS:
        per_tape = {}
        for tape in TAPES:
            drtp = tape_summary(cells, seed, tape, "drtp_sg")
            utr = tape_summary(cells, seed, tape, "utr_sg")
            per_tape[tape] = {
                "D": {m.upper(): drtp["returns"][m] - utr["returns"][m] for m in METRICS},
                "D_timeout": utr["timeout_mean_failure"] - drtp["timeout_mean_failure"],
                "DRTP_timeout_mean_failure": drtp["timeout_mean_failure"],
                "UTR_timeout_mean_failure": utr["timeout_mean_failure"],
            }
        means = {
            m: sum(per_tape[t]["D"][m] for t in TAPES) / len(TAPES)
            for m in FAILURE_METRICS
        }
        medians = {m: median(per_tape[t]["D"][m] for t in TAPES) for m in FAILURE_METRICS}
        positive_counts = {m: sum(per_tape[t]["D"][m] > 0 for t in TAPES) for m in FAILURE_METRICS}
        negative_counts = {m: sum(per_tape[t]["D"][m] < 0 for t in TAPES) for m in FAILURE_METRICS}
        candidate = {
            "seed": seed,
            "per_tape": per_tape,
            "mean_D": means,
            "median_D": medians,
            "positive_tape_counts": positive_counts,
            "negative_tape_counts": negative_counts,
            "mean_D_timeout": sum(per_tape[t]["D_timeout"] for t in TAPES) / len(TAPES),
            "median_D_timeout": median(per_tape[t]["D_timeout"] for t in TAPES),
        }
        candidate["G_eligible"] = all(means[m] > 0 for m in FAILURE_METRICS) and sum(
            positive_counts[m] >= 4 for m in FAILURE_METRICS
        ) >= 3
        candidate["B_eligible"] = all(means[m] < 0 for m in FAILURE_METRICS) and sum(
            negative_counts[m] >= 4 for m in FAILURE_METRICS
        ) >= 3
        candidate["G_tie_break"] = [
            sum(positive_counts[m] == 5 for m in FAILURE_METRICS),
            min(medians.values()),
            sum(medians.values()) / 4.0,
            candidate["median_D_timeout"],
            -seed,
        ]
        candidate["B_tie_break"] = [
            sum(negative_counts[m] == 5 for m in FAILURE_METRICS),
            max(medians.values()),
            sum(medians.values()) / 4.0,
            candidate["median_D_timeout"],
            -seed,
        ]
        candidates.append(candidate)
    return candidates


def load_rng_stream_class():
    namespace: dict = {}
    source = RNG_SOURCE.read_text(encoding="utf-8")
    exec(compile(source, str(RNG_SOURCE), "exec"), namespace)
    return namespace["RNGStreams"]


def make_eval_manifest() -> dict:
    tape_manifests = []
    for tape in TAPES:
        path = REL / "tapes" / f"{tape}_manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        tape_manifests.append({
            "label": tape,
            "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": sha256(path),
            "tape_hash": data["tape_hash"],
            "episode_ids": data["episode_ids"],
            "conditions": data["conditions"],
            "episodes_per_condition": data["episodes_per_condition"],
        })
    condition_payload = json.dumps(
        {"conditions": tape_manifests[0]["conditions"], "episodes_per_condition": 100},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "protocol": "DRTP-S1R-EVALUATION-V2",
        "source": "REL-A0 frozen tape manifests; no tape regenerated",
        "tapes": tape_manifests,
        "condition_definition_sha256": hashlib.sha256(condition_payload).hexdigest(),
        "method_seeds": {"methods": ["utr_sg", "drtp_sg"], "seeds": list(SEEDS)},
        "same_tape_for_all_runs": True,
        "evaluation_started": False,
    }


def make_tp50(eval_manifest: dict) -> dict:
    rows = []
    for tape in eval_manifest["tapes"]:
        for episode_id in tape["episode_ids"][:10]:
            rows.append({"tape": tape["label"], "episode_id": episode_id})
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "protocol": "DRTP-S1R-TP50-V2",
        "rule": "first 10 episode IDs from each imported REL-A0 tape",
        "episodes": rows,
        "count": len(rows),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cells = load_cells()
    candidates = build_candidates(cells)
    g_eligible = [c for c in candidates if c["G_eligible"]]
    b_eligible = [c for c in candidates if c["B_eligible"]]
    if not g_eligible or not b_eligible:
        raise RuntimeError("Cannot freeze S1-R: G or B eligible set is empty")
    g = max(g_eligible, key=lambda c: tuple(c["G_tie_break"]))
    b = max(b_eligible, key=lambda c: tuple(c["B_tie_break"]))
    if g["seed"] == b["seed"]:
        raise RuntimeError("G and B must be distinct seeds")

    rng_class = load_rng_stream_class()
    rng = {
        "protocol": "DRTP-S1R-RNG-V2",
        "source_file": str(RNG_SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha256(RNG_SOURCE),
        "source_regression_artifact": str(RNG_ARTIFACT.relative_to(ROOT)).replace("\\", "/"),
        "source_regression_sha256": sha256(RNG_ARTIFACT),
        "derivation": "RNGStreams.from_master(master_seed); blake2b(base_seed, stream_name, components) -> signed-31-bit seed",
        "streams": ["init", "env", "action", "minibatch", "topology", "eval"],
        "tuples": {
            "G": {"master_seed": g["seed"], **rng_class.from_master(g["seed"]).manifest()["seeds"]},
            "B": {"master_seed": b["seed"], **rng_class.from_master(b["seed"]).manifest()["seeds"]},
        },
        "intervention_rule": "replace exactly one named stream from B with G while retaining the other five B streams; evaluation stream is fixed",
        "training_started": False,
    }
    eval_manifest = make_eval_manifest()
    tp50 = make_tp50(eval_manifest)
    write_json(OUT / "gb_selection.json", {
        "protocol": "DRTP-S1R-GB-SELECTION-V2",
        "source": "artifacts/drtp_reliability_a0/rel_a0_decision.json",
        "source_sha256": sha256(REL / "rel_a0_decision.json"),
        "rules": {
            "G": "all four mean D > 0 and at least three metrics have D > 0 on >=4/5 tapes",
            "B": "all four mean D < 0 and at least three metrics have D < 0 on >=4/5 tapes",
            "timeout_orientation": "D_timeout = timeout_UTR - timeout_DRTP; tape value is mean of four failure conditions",
        },
        "candidates": candidates,
        "selected": {"G": g["seed"], "B": b["seed"]},
        "selection_is_machine_generated": True,
    })
    write_json(OUT / "eval_manifest.json", eval_manifest)
    write_json(OUT / "tp50_manifest.json", tp50)
    write_json(OUT / "rng_tuples.json", rng)
    write_json(OUT / "frozen_contract.json", {
        "protocol": "DRTP-S1R-PROTOCOL-V2",
        "status": "FROZEN_PROTOCOL_ONLY",
        "history": {
            "v1_execution_audit": "F_PROTOCOL_UNDERSPECIFIED",
            "v1_preserved": True,
            "v1_overwritten": False,
        },
        "selected_G_seed": g["seed"],
        "selected_B_seed": b["seed"],
        "seed_pool": list(SEEDS),
        "methods": ["utr_sg", "drtp_sg"],
        "scientific_runs": {
            "reference_runs": 2,
            "intervention_runs": 10,
            "total_runs": 12,
            "steps_per_run": 1000192,
            "max_scientific_env_steps": 12002304,
            "technical_smoke_max_env_steps": 20000,
            "milestones": [250048, 500096, 750144, 1000192],
            "checkpoint_policy": "milestones are diagnostic only; no promotion",
        },
        "rng": rng,
        "evaluation": {
            "manifest": "artifacts/drtp_s1r_protocol_v2/eval_manifest.json",
            "tp50_manifest": "artifacts/drtp_s1r_protocol_v2/tp50_manifest.json",
            "conditions": ["nominal", "f0", "timing", "duration", "compound"],
            "risk_set": "episodes alive immediately before scheduled failure onset",
            "pre_onset_termination": "retained in overall metrics and reported separately",
        },
        "telemetry_schema": [
            "episode_id", "env_step", "failure_relative_step", "agent_role", "position", "velocity",
            "sampled_action", "executed_action", "task_stage", "task_progress", "stagnation",
            "graph_state", "active_edges", "failure_state", "terminal_reason", "timeout", "collision",
            "constraint_violation", "actor_loss", "critic_loss", "entropy", "KL", "clip_fraction",
            "gradient_norm", "DRTP_group_weights", "DRTP_group_signal", "probe_id",
            "probe_policy_output", "milestone",
        ],
        "reference_gate": {
            "R1": "mean_t Gap_m > 0 for all four return metrics",
            "R2": ">=3/4 return metrics with G_REF > B_REF on >=4/5 tapes",
            "R3": "mean timeout quality G > B and G favorable on >=3/5 tapes",
            "failure_action": "F_REFERENCE_NOT_REPRODUCED; stop before interventions",
        },
        "rescue_and_reverse": {
            "per_metric_threshold": 0.35,
            "tape_pass_count": 4,
            "overall_dimensions": 5,
            "overall_pass_count": 4,
            "return_dimension_pass_count": 3,
            "median_coefficient_threshold": 0.40,
            "minimum_coefficient": -0.20,
            "dimensions": ["F0", "TIMING", "DURATION", "COMPOUND", "TIMEOUT"],
        },
        "precursor": {
            "confirmatory_milestone": 500096,
            "window_steps": 40,
            "risk_set": "alive at scheduled failure onset",
            "metrics": {
                "P1": "(task_progress[39]-task_progress[0])/40; higher is better",
                "P2": "count(stagnation == 1)/40; quality is negative fraction",
                "P3": "1 if task_stage[39] > task_stage[0], else 0",
            },
            "eligibility": ">=2/3 precursor metrics and reference gap > 0 with >=3/4 failure families separated",
            "coefficient_threshold": 0.30,
            "direction_families": 3,
            "passing_precursors": 2,
        },
        "outcome_labels": ["A_ACTIONABLE_SINGLE", "B_MULTIPLE_ACTIONABLE", "C_ONE_WAY_ONLY", "D_NO_SOURCE", "E_TRAJECTORY_NO_SOURCE", "F_REFERENCE_NOT_REPRODUCED", "G_TECHNICAL_INVALID"],
        "training_started": False,
        "evaluation_started": False,
        "stop_after_protocol_validation": True,
    })
    print(json.dumps({"selected_G": g["seed"], "selected_B": b["seed"], "out": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
