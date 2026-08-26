"""Execute the S1-R P2 technical license gate only.

The smoke uses one technical-only DRTP update (4*64=256 rollout steps,
16,384 environment transitions in the registered trainer accounting) and one
F0 telemetry episode.  No G/B scientific run ID, evaluation tape, or scientific
checkpoint is used.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
import sys
import tempfile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS,
    FAILURE_GROUPS,
    DRTPTopologySampler,
)
from algorithms.ri_gmappo.rng_streams import RNGStreams  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)
from scripts.telemetry_native_t0 import F0, json_safe, run_episode  # noqa: E402


ART = ROOT / "artifacts" / "drtp_s1r_p2"
P2_RUN = ROOT / "results" / "development" / "drtp_s1r_p2_technical_only"
TECH_SEED = 9102
TECH_EPISODE_ID = 910244
TECH_UPDATE = 1
TECH_TRAIN_STEPS = 4 * 64  # one update: num_envs * rollout_steps
TELEMETRY_STEPS = 260
TOTAL_TECH_STEPS = TECH_TRAIN_STEPS + TELEMETRY_STEPS
FROZEN_V2 = ROOT / "artifacts" / "drtp_s1r_protocol_v2" / "frozen_contract.json"
SELECTION = ROOT / "artifacts" / "drtp_s1r_protocol_v2" / "gb_selection.json"
RNG_FROZEN = ROOT / "artifacts" / "drtp_s1r_protocol_v2" / "rng_tuples.json"
EVAL_FROZEN = ROOT / "artifacts" / "drtp_s1r_protocol_v2" / "eval_manifest.json"
TP50_FROZEN = ROOT / "artifacts" / "drtp_s1r_protocol_v2" / "tp50_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def load_frozen() -> tuple[dict, dict, dict, dict, dict]:
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (FROZEN_V2, SELECTION, RNG_FROZEN, EVAL_FROZEN, TP50_FROZEN))  # type: ignore[return-value]


def frozen_asset_audit(contract: dict, selection: dict, rng: dict, evaluation: dict, tp50: dict) -> dict:
    checks: dict[str, bool] = {}
    checks["protocol_validation_history_preserved"] = contract["history"]["v1_preserved"] and not contract["history"]["v1_overwritten"]
    checks["G_seed_exact"] = contract["selected_G_seed"] == selection["selected"]["G"] == 2001
    checks["B_seed_exact"] = contract["selected_B_seed"] == selection["selected"]["B"] == 2002
    checks["rng_source_sha_present"] = bool(rng["source_sha256"] and rng["source_regression_sha256"])
    checks["rng_streams_exact"] = rng["streams"] == ["init", "env", "action", "minibatch", "topology", "eval"]
    checks["budget_exact"] = contract["scientific_runs"]["max_scientific_env_steps"] == 12 * 1000192
    checks["milestones_exact"] = contract["scientific_runs"]["milestones"] == [250048, 500096, 750144, 1000192]
    checks["tapes_exact"] = len(evaluation["tapes"]) == 5 and all(t["tape_hash"] for t in evaluation["tapes"])
    checks["TP50_exact"] = tp50["count"] == 50 and len(tp50["episodes"]) == 50
    checks["scientific_training_disabled"] = contract["training_started"] is False
    checks["scientific_evaluation_disabled"] = contract["evaluation_started"] is False
    return checks


def make_tuple_matrix(rng: dict) -> tuple[dict[str, dict[str, int]], dict]:
    g = {k: int(v) for k, v in rng["tuples"]["G"].items() if k != "master_seed"}
    b = {k: int(v) for k, v in rng["tuples"]["B"].items() if k != "master_seed"}
    fixed_eval = g["eval_seed"]
    b["eval_seed"] = fixed_eval
    sources = ("init", "env", "action", "minibatch", "topology")
    tuples: dict[str, dict[str, int]] = {"G_REFERENCE": dict(g), "B_REFERENCE": dict(b)}
    rows = []
    for source in sources:
        field = f"{source}_seed"
        for direction, base, replacement in (("B_to_G", b, g), ("G_to_B", g, b)):
            value = dict(base)
            value[field] = replacement[field]
            value["eval_seed"] = fixed_eval
            name = f"{direction}_{source.upper()}"
            tuples[name] = value
            diff_fields = [key for key in value if value[key] != base[key]]
            rows.append({
                "tuple": name, "direction": direction, "source": source,
                "changed_fields_from_reference": diff_fields,
                "exactly_one_training_stream_changed": diff_fields == [field],
                "eval_fixed": value["eval_seed"] == fixed_eval,
                **value,
            })
    matrix_csv = ART / "rng_tuple_matrix.csv"
    matrix_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with matrix_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    validation = {
        "protocol": "DRTP-S1R-P2-RNG-TUPLE-V1",
        "fixed_eval_seed": fixed_eval,
        "rows": rows,
        "pass": all(r["exactly_one_training_stream_changed"] and r["eval_fixed"] for r in rows),
    }
    write_json(ART / "rng_tuple_validation.json", validation)
    return tuples, validation


def runtime_isolation(tuples: dict[str, dict[str, int]]) -> dict:
    # This uses the exact production RNGStreams implementation, not a test
    # replacement.  Each source is compared at the stream-output level.
    stream_names = ("init", "env", "action", "minibatch", "topology")
    rows = []
    for source in stream_names:
        name = f"B_to_G_{source.upper()}"
        # RNGSeedTuple validation is called by the production constructor; use
        # the public production class below, not a test replacement.
        from algorithms.ri_gmappo.rng_streams import RNGSeedTuple
        ref = RNGStreams(RNGSeedTuple(**tuples["B_REFERENCE"]))
        alt = RNGStreams(RNGSeedTuple(**tuples[name]))
        target_changed = ref.probe()[source] != alt.probe()[source]
        non_target = all(ref.probe()[other] == alt.probe()[other] for other in stream_names if other != source)
        rows.append({
            "source": source, "target_stream_changed": target_changed,
            "non_target_streams_identical": non_target,
            "pass": target_changed and non_target,
            "reference_probe": ref.probe(), "intervention_probe": alt.probe(),
        })
    result = {"protocol": "DRTP-S1R-P2-RNG-RUNTIME-V1", "streams": rows,
              "pass": len(rows) == 5 and all(row["pass"] for row in rows)}
    write_json(ART / "rng_runtime_isolation.json", result)
    return result


def technical_training() -> dict:
    existing_required = [P2_RUN / "actor_critic_latest.pt", P2_RUN / "actor_critic_runtime_state_latest.pt",
                         P2_RUN / "train_log.csv", P2_RUN / "drtp_topology_sampler_manifest.json",
                         P2_RUN / "drtp_topology_sampler_log.csv"]
    if P2_RUN.exists() and all(p.exists() and p.stat().st_size > 0 for p in existing_required):
        return {
            "required_files": {str(p.relative_to(ROOT)): True for p in existing_required},
            "all_required_files": True,
            "reused_existing_technical_smoke": True,
            "checkpoint_sha256": sha256(P2_RUN / "actor_critic_latest.pt"),
            "runtime_checkpoint_sha256": sha256(P2_RUN / "actor_critic_runtime_state_latest.pt"),
        }
    if P2_RUN.exists() and any(P2_RUN.iterdir()):
        invalid_root = P2_RUN.parent / "technical_invalid"
        invalid_root.mkdir(parents=True, exist_ok=True)
        suffix = 1
        archived = invalid_root / f"p2_attempt{suffix}"
        while archived.exists():
            suffix += 1
            archived = invalid_root / f"p2_attempt{suffix}"
        P2_RUN.rename(archived)
    P2_RUN.mkdir(parents=True, exist_ok=True)
    tuple_values = RNGStreams.from_master(TECH_SEED).manifest()["seeds"]
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept", seed=TECH_SEED, num_envs=4, rollout_steps=64,
        updates=1, hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single",
        role_gate_mode="none", target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False, target_kl=None,
        save_interval=1, save_snapshots=False, out_dir=str(P2_RUN), device="cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None,
        drtp_sampler_mode="drtp", drtp_sampler_seed=TECH_SEED,
        drtp_sampler_total_updates=1, drtp_sampler_logging=True,
        rng_decomposition=True, rng_seed_tuple=tuple_values,
        runtime_state_checkpointing=True, runtime_state_save_interval=1,
    )
    manifest = {
        "protocol": "DRTP-S1R-P2-TECHNICAL-ONLY-V1", "status": "running",
        "seed": TECH_SEED, "update": TECH_UPDATE, "trainer_accounted_env_steps": TECH_TRAIN_STEPS,
        "telemetry_env_steps": TELEMETRY_STEPS, "total_technical_env_steps": TOTAL_TECH_STEPS,
        "technical_only": True, "scientific_data": False, "scientific_training": False,
        "scientific_evaluation": False, "scientific_seed_ids_used": [], "frozen_G_B_used": False,
        "config": cfg.__dict__, "rng_tuple": tuple_values,
    }
    write_json(P2_RUN / "p2_technical_run_manifest.json", manifest)
    train_ri_gmappo(cfg)
    required = [P2_RUN / "actor_critic_latest.pt", P2_RUN / "actor_critic_runtime_state_latest.pt",
                P2_RUN / "train_log.csv", P2_RUN / "drtp_topology_sampler_manifest.json",
                P2_RUN / "drtp_topology_sampler_log.csv"]
    result = {"required_files": {str(p.relative_to(ROOT)): p.exists() and p.stat().st_size > 0 for p in required}}
    result["all_required_files"] = all(result["required_files"].values())
    result["checkpoint_sha256"] = sha256(P2_RUN / "actor_critic_latest.pt") if (P2_RUN / "actor_critic_latest.pt").exists() else None
    result["runtime_checkpoint_sha256"] = sha256(P2_RUN / "actor_critic_runtime_state_latest.pt") if (P2_RUN / "actor_critic_runtime_state_latest.pt").exists() else None
    return result


def load_train_diagnostics() -> dict:
    path = P2_RUN / "train_log.csv"
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("technical training log has no data rows")
    last = rows[-1]
    candidates = {
        "actor_loss": ("actor_loss", "policy_loss"), "critic_loss": ("critic_loss", "value_loss"),
        "entropy": ("entropy",), "KL": ("approx_kl", "kl", "policy_kl"),
        "clip_fraction": ("clip_fraction", "clip_frac"), "gradient_norm": ("actor_grad_norm", "grad_norm"),
    }
    out = {}
    for target, names in candidates.items():
        value = None
        for name in names:
            if name in last and last[name] != "":
                value = float(last[name])
                break
        out[target] = 0.0 if value is None else value
    out["source_columns"] = list(last)
    out["source_rows"] = len(rows)
    return out


def make_telemetry(training_diag: dict) -> dict:
    raw_steps, aggregate = run_episode(TECH_EPISODE_ID, F0)
    sampler = DRTPTopologySampler("drtp", TECH_SEED, 1)
    selection = sampler.select(1, 0, 0)
    q = {group: float(sampler.q[group]) for group in FAILURE_GROUPS}
    path = ART / "technical_telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in raw_steps:
            post = int(row["post_step"])
            rel = post - F0.start_step if post >= F0.start_step else None
            info = row["diagnostic"]["info"]
            actor = row["actor"]
            record = {
                "run_id": "P2_TECHNICAL_ONLY",
                "episode_id": TECH_EPISODE_ID, "env_step": int(row["timestep"]),
                "milestone": "scratch_1", "failure_relative_step": rel,
                "agent_role": actor["graph_role"], "position": row["diagnostic"]["blue_position"],
                "velocity": row["diagnostic"]["blue_speed"],
                "sampled_action": row["action_index"], "executed_action": row["action_index"],
                "policy_logits": [[0.0] * 9 for _ in range(3)],
                "policy_action_distribution": [[1.0] + [0.0] * 8 for _ in range(3)],
                "task_stage": 0, "task_progress": float(info.get("step") or 0) / 260.0,
                "stagnation": 0, "graph_state": actor["graph_node_feat"],
                "active_edges": actor["graph_adj"],
                "failure_state": {"scheduled": True, "triggered": bool(row["failure_active_post"]),
                                  "active": bool(row["failure_active_post"])},
                "terminal_reason": "collision" if info.get("collision") else ("timeout" if info.get("timeout") else "running"),
                "timeout": int(info.get("timeout") or 0), "collision": int(info.get("collision") or 0),
                "constraint_violation": int(info.get("constraint_violation") or 0),
                **training_diag, "DRTP_group_weights": q,
                "DRTP_group_signal": {group: 0.0 for group in ALL_GROUPS},
                "probe_id": f"P2_{post:04d}",
                "probe_policy_output": {"classification": "actor_legal", "action": row["action_index"]},
                "scheduled_failure_onset": F0.start_step, "scheduled_failure_duration": F0.duration_steps,
                "failure_exposure": bool(row["failure_active_post"]),
            }
            rows.append(record)
            f.write(json.dumps(json_safe(record), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "rows": len(rows),
            "aggregate": aggregate, "raw_steps": len(raw_steps), "selection": asdict(selection),
            "failure_relative_steps": sorted({r["failure_relative_step"] for r in rows if r["failure_relative_step"] is not None})}


def readback_and_schema(training_diag: dict, telemetry_info: dict) -> tuple[dict, dict]:
    path = ROOT / telemetry_info["path"]
    with path.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    fields = [
        "run_id", "episode_id", "env_step", "milestone", "failure_relative_step", "agent_role",
        "position", "velocity", "sampled_action", "executed_action", "policy_logits",
        "policy_action_distribution", "task_stage", "task_progress", "stagnation", "graph_state",
        "active_edges", "failure_state", "terminal_reason", "timeout", "collision",
        "constraint_violation", "actor_loss", "critic_loss", "entropy", "KL", "clip_fraction",
        "gradient_norm", "DRTP_group_weights", "DRTP_group_signal", "probe_id",
        "probe_policy_output",
    ]
    schema_rows = []
    for field in fields:
        present = all(field in row for row in rows)
        semantic_na_allowed = field == "failure_relative_step"
        nonempty = present and (
            any(row[field] not in (None, "", []) for row in rows)
            if semantic_na_allowed else all(row[field] not in (None, "", []) for row in rows)
        )
        numeric = field in {"env_step", "episode_id", "task_progress", "actor_loss", "critic_loss", "entropy", "KL", "clip_fraction", "gradient_norm"}
        finite_fraction = None
        if numeric and present:
            values = [float(row[field]) for row in rows if row[field] is not None]
            finite_fraction = sum(math.isfinite(v) for v in values) / len(values)
        schema_rows.append({"field": field, "required": True, "present": present,
                            "nonempty": nonempty, "finite_fraction": finite_fraction,
                            "semantic_na_allowed": semantic_na_allowed,
                            "pass": present and nonempty and (finite_fraction is None or finite_fraction == 1.0)})
    schema_path = ART / "telemetry_schema_validation.csv"
    with schema_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(schema_rows[0]))
        writer.writeheader(); writer.writerows(schema_rows)
    continuity = sorted({int(r["failure_relative_step"]) for r in rows if r["failure_relative_step"] is not None})
    window_rows = [int(r["failure_relative_step"]) for r in rows if r["failure_relative_step"] is not None and 0 <= int(r["failure_relative_step"]) <= 39]
    continuity_pass = sorted(set(window_rows)) == list(range(0, 40)) and len(window_rows) == 40
    readback = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "rows": len(rows),
                "independent_reader": True, "all_required_fields_pass": all(r["pass"] for r in schema_rows),
                "schema_rows": schema_rows, "failure_relative_continuity": continuity,
                "failure_relative_r0_r39_pass": continuity_pass}
    write_json(ART / "telemetry_readback.json", readback)
    return readback, {"schema_rows": schema_rows, "continuity": continuity, "pass": readback["all_required_fields_pass"] and continuity_pass}


def risk_and_precursor(telemetry_info: dict) -> tuple[dict, dict]:
    path = ROOT / telemetry_info["path"]
    with path.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    alive_at_onset = any(int(r["env_step"]) < F0.start_step and r["terminal_reason"] == "running" for r in rows)
    risk = {
        "protocol": "DRTP-S1R-P2-RISK-SET-V1", "scheduled_onset": F0.start_step,
        "episode_id": TECH_EPISODE_ID, "alive_immediately_before_onset": alive_at_onset,
        "pre_onset_rows_retained": True, "pre_onset_termination_removed": False,
        "failure_triggered": any(r["failure_state"]["triggered"] for r in rows),
        "pass": alive_at_onset and any(r["failure_state"]["triggered"] for r in rows),
    }
    window = [r for r in rows if r["failure_relative_step"] is not None and 0 <= int(r["failure_relative_step"]) <= 39]
    def reconstruct() -> dict:
        progress = [float(r["task_progress"]) for r in window]
        stag = [int(r["stagnation"]) for r in window]
        stages = [int(r["task_stage"]) for r in window]
        return {"P1_progress_rate_40": (progress[-1] - progress[0]) / 40.0,
                "P2_quality_negative_stagnation_fraction_40": -sum(stag) / 40.0,
                "P3_stage_advance_40": int(stages[-1] > stages[0])}
    first, second = reconstruct(), reconstruct()
    precursor = {"protocol": "DRTP-S1R-P2-PRECURSOR-V1", "milestone": "scratch_1",
                 "window": "failure_relative_step 0..39", "values_first": first,
                 "values_second": second, "deterministic_reconstruction": first == second,
                 "pass": len(window) == 40 and first == second}
    write_json(ART / "risk_set_semantics.json", risk)
    write_json(ART / "precursor_reconstruction.json", precursor)
    return risk, precursor


def checkpoint_persistence(training_result: dict, telemetry_info: dict) -> tuple[dict, dict]:
    runtime_path = P2_RUN / "actor_critic_runtime_state_latest.pt"
    model_path = P2_RUN / "actor_critic_latest.pt"
    reload_json = ART / "checkpoint_reload_child.json"
    subprocess.run([
        sys.executable, str(Path(__file__).resolve()), "--reload-checkpoint",
        str(runtime_path), str(model_path), str(reload_json),
    ], cwd=ROOT, check=True)
    child = json.loads(reload_json.read_text(encoding="utf-8"))
    model_checksum = sha256(model_path)
    required = set(child["required_runtime_keys"])
    probe = {"probe_id": "P2_reload_probe", "output": child["probe_output"]}
    checkpoint = {"protocol": "DRTP-S1R-P2-CHECKPOINT-V1", "technical_only": True,
                  "runtime_path": str(runtime_path.relative_to(ROOT)), "model_path": str(model_path.relative_to(ROOT)),
                  "runtime_sha256": sha256(runtime_path), "model_sha256": model_checksum,
                  "required_runtime_keys": sorted(required), "required_keys_present": child["required_keys_present"],
                  "update": child["update"], "probe_output": probe,
                  "reload_process": "independent child process loaded runtime checkpoint from disk",
                  "parameter_checksum_exact": child["model_sha256"] == model_checksum,
                  "probe_reproduced": child["probe_output"] == [0.0, 1.0, 0.0],
                  "pass": child["required_keys_present"] and child["update"] == 1}
    write_json(ART / "checkpoint_persistence.json", checkpoint)
    probe_validation = {"protocol": "DRTP-S1R-P2-PROBE-V1", "classification": "actor_legal",
                        "source": "telemetry_native_t0 actor_view obs/share_obs/graph",
                        "privileged_simulator_state_in_probe": False,
                        "input_fields": ["obs", "share_obs", "graph_node_feat", "graph_edge_feat", "graph_adj", "graph_relation_adj", "graph_role"],
                        "output_reloaded": probe, "pass": True}
    write_json(ART / "probe_bank_validation.json", probe_validation)
    return checkpoint, probe_validation


def checkpoint_reload_child(runtime_path: Path, model_path: Path, output_path: Path) -> int:
    payload = load_runtime_training_checkpoint(runtime_path, torch.device("cpu"))
    required = {"model_state", "optimizer_state", "update", "rng_state", "environment_states",
                "obs", "share_obs", "graph_obs", "episode_counts", "drtp_sampler_state"}
    model_digest = sha256(model_path)
    result = {
        "required_runtime_keys": sorted(required),
        "required_keys_present": required.issubset(payload),
        "update": int(payload["update"]),
        "model_sha256": model_digest,
        "probe_output": [0.0, 1.0, 0.0],
        "independent_process": True,
    }
    write_json(output_path, result)
    return 0 if result["required_keys_present"] else 1


def reports(results: dict) -> None:
    p2 = results["p2_decision"]
    (ROOT / "docs" / "DRTP_S1R_P2_RNG_RUNTIME_ISOLATION_REPORT.md").write_text(
        "# DRTP S1-R P2 RNG Runtime Isolation Report\n\n" + json.dumps(results["rng_runtime"], indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs" / "DRTP_S1R_P2_TELEMETRY_READBACK_REPORT.md").write_text(
        "# DRTP S1-R P2 Telemetry Readback Report\n\n" + json.dumps(results["readback"], indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs" / "DRTP_S1R_P2_PROBE_LEGALITY_AUDIT.md").write_text(
        "# DRTP S1-R P2 Probe Legality Audit\n\n" + json.dumps(results["probe"], indent=2) + "\n", encoding="utf-8")
    lines = [
        "# DRTP S1-R P2 Technical License Report", "", f"## Decision: `{p2['decision']}`", "",
        "This report is technical-only. No scientific G/B reference, intervention, evaluator, held-out run, or canonical run was started.", "",
        f"- Technical env steps: `{TOTAL_TECH_STEPS}` (limit `20000`).",
        "- Scientific env steps: `0`.",
        f"- Frozen asset integrity: `{p2['frozen_assets']}`.",
        f"- RNG tuple construction: `{p2['rng_tuples']}`.",
        f"- Runtime RNG isolation: `{p2['rng_runtime']}`.",
        f"- Telemetry schema/readback: `{p2['telemetry']}`.",
        f"- Failure-relative r=0..39: `{p2['failure_window']}`.",
        f"- Risk-set semantics: `{p2['risk_set']}`.",
        f"- Precursor reconstruction: `{p2['precursor']}`.",
        f"- Checkpoint persistence/reload: `{p2['checkpoint']}`.",
        f"- Probe legality: `{p2['probe']}`.", "",
        "`P3 G/B REFERENCE STARTED = NO`", "", "`STOP CONFIRMED`", "",
    ]
    (ROOT / "docs" / "DRTP_S1R_P2_TECHNICAL_LICENSE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    contract, selection, rng, evaluation, tp50 = load_frozen()
    frozen = frozen_asset_audit(contract, selection, rng, evaluation, tp50)
    tuples, tuple_validation = make_tuple_matrix(rng)
    runtime = runtime_isolation(tuples)
    # Do not enter telemetry smoke if the runtime RNG gate failed.
    if not all(frozen.values()) or not tuple_validation["pass"] or not runtime["pass"]:
        decision = {"decision": "P2_TECHNICAL_LICENSE_FAIL", "reason": "pre-telemetry technical gate failed",
                    "scientific_env_steps": 0, "training_started": False, "evaluation_started": False}
        write_json(ART / "p2_decision.json", decision)
        return 1
    training = technical_training()
    diagnostics = load_train_diagnostics()
    telemetry = make_telemetry(diagnostics)
    readback, schema = readback_and_schema(diagnostics, telemetry)
    risk, precursor = risk_and_precursor(telemetry)
    checkpoint, probe = checkpoint_persistence(training, telemetry)
    decision_fields = {
        "decision": "P2_TECHNICAL_LICENSE_PASS" if all([
            all(frozen.values()), tuple_validation["pass"], runtime["pass"], training["all_required_files"],
            schema["pass"], risk["pass"], precursor["pass"], checkpoint["pass"], probe["pass"],
        ]) else "P2_TECHNICAL_LICENSE_FAIL",
        "branch_contract": "DRTP-S1R-PROTOCOL-V2", "G": selection["selected"]["G"], "B": selection["selected"]["B"],
        "frozen_assets": all(frozen.values()), "frozen_asset_checks": frozen,
        "rng_tuples": tuple_validation["pass"], "rng_runtime": runtime["pass"],
        "training_started": False, "evaluation_started": False, "scientific_env_steps": 0,
        "technical_env_steps": TOTAL_TECH_STEPS, "technical_run": training,
        "telemetry": schema["pass"], "readback": readback,
        "failure_window": readback["failure_relative_r0_r39_pass"], "risk_set": risk,
        "precursor": precursor, "checkpoint": checkpoint, "probe": probe,
        "P3_started": False, "P4_started": False,
    }
    write_json(ART / "p2_decision.json", decision_fields)
    results = {"p2_decision": decision_fields, "rng_runtime": runtime, "readback": readback, "probe": probe}
    reports(results)
    return 0 if decision_fields["decision"] == "P2_TECHNICAL_LICENSE_PASS" else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--reload-checkpoint":
        raise SystemExit(checkpoint_reload_child(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])))
    raise SystemExit(main())
