"""Method-independent L5 relay-failure onset calibration (no learning)."""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, ROLE_RELAY
from scripts import audit_relay_path_redesign_identifiability as path_audit
from scripts import run_l4_delay_development as l4
from scripts import run_new_project_l0_single_interceptor as l0

OUT = ROOT / "results" / "l5_relay_failure_onset_calibration"
SEEDS = tuple(range(920_000, 920_008))
CANDIDATE_ONSETS = (20, 24, 28)
HORIZON = 180
PROTOCOL = "L5_RELAY_FAILURE_ONSET_CALIBRATION_V1"


def cfg(seed: int, onset: int | None):
    base = path_audit.cfg(seed, OUT / "template")
    # `None` selects the environment's frozen Scout/Relay/Attacker ordering.
    relay = 1 if base.blue_types is None else next(i for i, typ in enumerate(base.blue_types) if typ.role == ROLE_RELAY)
    return replace(
        base, failed_blue_agent=relay if onset is not None else -1,
        node_failure_start_step=onset or 0,
        node_failure_duration_steps=HORIZON if onset is not None else 0,
        protocol_version=PROTOCOL,
        run_id=f"l5_onset_{onset if onset is not None else 'normal'}_seed{seed}",
    )


def legal_scripted_action(env, obs: np.ndarray) -> np.ndarray:
    legacy = np.zeros(env.config.num_blue, dtype=np.int64)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            legacy[i] = int(l0.heuristic_action(obs[i : i + 1])[0])
    out = l4._continuous_from_legacy(env, legacy, already_guidance=True)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            out[i, 2] = -1.0
    return out


def episode(seed: int, onset: int | None, controller: str):
    env = l0.make_env(cfg(seed, onset), seed, training=False)
    relay = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_RELAY)
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_ATTACKER)
    obs, share, graph = env.reset()
    pre_evidence = False; post_stop = True; cache_generation_at_onset = None
    action_trace, states = [], []
    while True:
        command = path_audit.action(env) if controller == "oracle" else legal_scripted_action(env, obs)
        action_trace.append(command.copy())
        obs, share, graph, _reward, dones, info = env.step(command)
        path = list(env.target_cache_path[attacker])
        relay_only = env._has_fresh_target_cache(attacker) and relay in path and env.detected_by[attacker] < 0.5
        if onset is not None and env.step_count < onset:
            pre_evidence = pre_evidence or relay_only
        if onset is not None and env.step_count >= onset:
            post_stop = post_stop and bool(env.comm_adj[attacker, relay] == 0.0)
            if cache_generation_at_onset is None:
                cache_generation_at_onset = int(env.target_cache_generation_step[attacker])
        states.append((env.blue_pos.copy(), env.red_pos.copy()))
        if bool(np.all(dones)):
            return {
                "seed": seed, "onset": onset, "controller": controller,
                "outcome": l0.outcome(info), "steps": int(info["step"]),
                "relay_evidence_before_failure": int(pre_evidence),
                "relay_outbound_stopped_after_failure": int(post_stop),
                "remaining_steps_after_onset": HORIZON - onset if onset is not None else None,
                "cache_generation_at_onset": cache_generation_at_onset,
                "actions": action_trace, "states": states,
            }


def fixed_action_physics(seed: int, onset: int) -> bool:
    normal = episode(seed, None, "oracle")
    failed = episode(seed, onset, "oracle")
    n = min(len(normal["states"]), len(failed["states"]))
    return all(np.array_equal(normal["states"][i][0], failed["states"][i][0]) and np.array_equal(normal["states"][i][1], failed["states"][i][1]) for i in range(n))


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite calibration output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    normal_legal = {seed: episode(seed, None, "legal_scripted") for seed in SEEDS}
    for onset in CANDIDATE_ONSETS:
        for seed in SEEDS:
            oracle = episode(seed, onset, "oracle")
            legal = episode(seed, onset, "legal_scripted")
            rows.extend([{k: v for k, v in item.items() if k not in {"actions", "states"}} for item in (oracle, legal)])
            legal["normal_legal_outcome"] = normal_legal[seed]["outcome"]
            legal["physical_dynamics_unchanged_under_fixed_oracle_actions"] = int(fixed_action_physics(seed, onset))
            rows.append({k: v for k, v in legal.items() if k not in {"actions", "states"}})
    # Deduplicate the legal controller row before and after paired annotations.
    rows = [row for row in rows if not (row["controller"] == "legal_scripted" and "normal_legal_outcome" not in row)]
    with (OUT / "l5_onset_calibration_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in rows for key in row})); writer.writeheader(); writer.writerows(rows)
    candidates = []
    for onset in CANDIDATE_ONSETS:
        oracle_rows = [r for r in rows if r["onset"] == onset and r["controller"] == "oracle"]
        legal_rows = [r for r in rows if r["onset"] == onset and r["controller"] == "legal_scripted"]
        normal_success = float(np.mean([normal_legal[s]["outcome"] == "NEUTRALIZED" for s in SEEDS]))
        legal_success = float(np.mean([r["outcome"] == "NEUTRALIZED" for r in legal_rows]))
        candidate = {
            "onset": onset, "relay_evidence_before_failure_all": all(r["relay_evidence_before_failure"] for r in oracle_rows),
            "relay_outbound_stops_all": all(r["relay_outbound_stopped_after_failure"] for r in oracle_rows),
            "oracle_feasible_all": all(r["outcome"] == "NEUTRALIZED" for r in oracle_rows),
            "fixed_action_physics_unchanged_all": all(r["physical_dynamics_unchanged_under_fixed_oracle_actions"] for r in legal_rows),
            "legal_scripted_normal_success": normal_success, "legal_scripted_failure_success": legal_success,
            "failure_has_nontrivial_legal_effect": legal_success < normal_success and legal_success > 0.0,
        }
        candidates.append(candidate)
    eligible = [c for c in candidates if all(c[k] for k in ("relay_evidence_before_failure_all", "relay_outbound_stops_all", "oracle_feasible_all", "fixed_action_physics_unchanged_all", "failure_has_nontrivial_legal_effect"))]
    payload = {
        "protocol": PROTOCOL, "performance_use_prohibited": True, "candidate_onsets": list(CANDIDATE_ONSETS), "seeds": list(SEEDS),
        "selection_rule": "earliest onset satisfying pre-failure relay evidence, real relay shutdown, unchanged fixed-action physics, oracle feasibility, and nontrivial-but-not-total legal-scripted degradation",
        "candidates": candidates,
        "selected_onset": eligible[0]["onset"] if eligible else None,
        "verdict": "L5_FAILURE_ONSET_FROZEN__READY_FOR_L5_DEVELOPMENT_AUTHORIZATION" if eligible else "L5_FAILURE_ONSET_NO_GO__RELAY_FAILURE_TASK_NOT_IDENTIFIABLE",
        "no_l5_training_authorized": True,
    }
    (OUT / "L5_FAILURE_ONSET_CALIBRATION.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
