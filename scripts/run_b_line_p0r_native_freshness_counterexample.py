"""Native-freshness paired-state audit for B-line P0R.

This is a small deterministic environment harness, not a solver or an
evaluation.  It uses the existing six-UAV environment without altering its
configuration, action interface, reward, cache threshold, or failure rules.
Two legal action histories are advanced to the same physical snapshot; only
the native cache freshness is allowed to differ.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config


FREEZE_PATH = ROOT / "configs" / "b_line_p0r_native_freshness_counterexample_freeze.json"


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_lf(path: Path, payload: str) -> None:
    path.write_bytes(payload.replace("\r\n", "\n").encode("utf-8"))


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_freeze() -> dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def action_vector(env: RedundantTopologyUAVEnv, *, scout_action: int) -> np.ndarray:
    actions = np.zeros(env.n, dtype=np.int64)
    actions[env.scout_ids] = int(scout_action)
    return actions


def cache_summary(env: RedundantTopologyUAVEnv) -> dict[str, Any]:
    terminals: dict[str, Any] = {}
    for terminal in env.terminal_ids:
        token = env.caches[int(terminal)].get(0)
        terminals[str(int(terminal))] = {
            "has_token": token is not None,
            "age": None if token is None else int(env.step_count - int(token["t_sense"])),
            "t_sense": None if token is None else int(token["t_sense"]),
            "valid_under_native_tau_max": bool(env._fresh_token(int(terminal), 0) is not None),
        }
    return {"tau_max": int(env.config.tau_max), "terminal_objective_zero": terminals}


def physical_snapshot(env: RedundantTopologyUAVEnv) -> dict[str, Any]:
    return {
        "step_count": int(env.step_count),
        "positions": env.positions.tolist(),
        "objective_positions": env.objective_positions.tolist(),
        "task_adjacency": env.task_adjacency(True).tolist(),
        "active_adjacency": env.last_active.tolist(),
        "objective_progress": env.objective_progress.tolist(),
        "completed": env.completed.astype(int).tolist(),
        "roles": env.roles.tolist(),
        "scout_assignment": {str(key): int(value) for key, value in sorted(env.scout_assignment.items())},
        "terminal_assignment": {str(key): int(value) for key, value in sorted(env.terminal_assignment.items())},
    }


def construct_history(name: str, freeze: dict[str, Any]) -> RedundantTopologyUAVEnv:
    env = RedundantTopologyUAVEnv(scale_config(str(freeze["environment"]["scale"])))
    horizon = int(freeze["fixed_horizon_steps"])
    objective_action = int(freeze["objective_action"])
    sensing_step = horizon if name == "fresh" else 1
    for step in range(1, horizon + 1):
        _, _, _, _, dones, _ = env.step(action_vector(env, scout_action=objective_action if step == sensing_step else 0))
        if bool(np.any(dones)):
            raise RuntimeError(f"{name} history ended early at step {step}")
    return env


def analyze() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    freeze = load_freeze()
    fresh = construct_history("fresh", freeze)
    stale = construct_history("stale", freeze)
    fresh_physical = physical_snapshot(fresh)
    stale_physical = physical_snapshot(stale)
    fresh_cache = cache_summary(fresh)
    stale_cache = cache_summary(stale)
    fresh_masks = {str(int(terminal)): fresh.support_action_mask(int(terminal)).astype(int).tolist() for terminal in fresh.terminal_ids}
    stale_masks = {str(int(terminal)): stale.support_action_mask(int(terminal)).astype(int).tolist() for terminal in stale.terminal_ids}

    same_physical = fresh_physical == stale_physical
    same_snapshot_hash = sha256_payload(fresh_physical) == sha256_payload(stale_physical)
    mask_changed = fresh_masks != stale_masks
    fresh_has_objective_action = all(mask[1] == 1 for mask in fresh_masks.values())
    stale_lacks_objective_action = all(mask[1] == 0 for mask in stale_masks.values())
    native_freshness_only = fresh_cache != stale_cache and same_physical

    if same_physical and same_snapshot_hash and native_freshness_only and mask_changed and fresh_has_objective_action and stale_lacks_objective_action:
        verdict = freeze["verdicts"]["go"]
    elif same_physical and native_freshness_only:
        verdict = freeze["verdicts"]["conditional"]
    else:
        verdict = freeze["verdicts"]["no_go"]

    rows: list[dict[str, Any]] = []
    for terminal in sorted(fresh_masks, key=int):
        rows.append({
            "terminal": int(terminal),
            "fresh_cache_age": fresh_cache["terminal_objective_zero"][terminal]["age"],
            "stale_cache_age": stale_cache["terminal_objective_zero"][terminal]["age"],
            "native_tau_max": fresh_cache["tau_max"],
            "fresh_action_mask": json.dumps(fresh_masks[terminal], separators=(",", ":")),
            "stale_action_mask": json.dumps(stale_masks[terminal], separators=(",", ":")),
            "objective_zero_legal_when_fresh": bool(fresh_masks[terminal][1]),
            "objective_zero_legal_when_stale": bool(stale_masks[terminal][1]),
        })
    result = {
        "protocol": freeze["protocol"],
        "verdict": verdict,
        "environment": "RedundantTopologyUAVEnv(scale_config('main')) with unmodified native defaults",
        "source_sha256": {
            "environment": hashlib.sha256((ROOT / "envs/redundant_topology_uav_env.py").read_bytes()).hexdigest(),
            "freeze": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        },
        "physical_snapshot_sha256": sha256_payload(fresh_physical),
        "freshness_state_sha256": {
            "fresh": sha256_payload(fresh_cache),
            "stale": sha256_payload(stale_cache),
        },
        "action_mask_sha256": {
            "fresh": sha256_payload(fresh_masks),
            "stale": sha256_payload(stale_masks),
        },
        "checks": {
            "same_current_physical_snapshot": same_physical,
            "same_current_physical_snapshot_hash": same_snapshot_hash,
            "same_remaining_mission": fresh_physical["objective_progress"] == stale_physical["objective_progress"] and fresh_physical["completed"] == stale_physical["completed"],
            "same_role_assignment": fresh_physical["roles"] == stale_physical["roles"] and fresh_physical["scout_assignment"] == stale_physical["scout_assignment"] and fresh_physical["terminal_assignment"] == stale_physical["terminal_assignment"],
            "only_native_freshness_differs": native_freshness_only,
            "native_action_masks_differ": mask_changed,
            "fresh_objective_action_legal": fresh_has_objective_action,
            "stale_objective_action_illegal": stale_lacks_objective_action,
            "cache_threshold_overridden": False,
            "environment_modified": False,
            "new_action_added": False,
        },
        "interpretation": (
            "The current physical topology is not sufficient to determine the native terminal feasible-action set. "
            "The same physical snapshot admits objective action 1 when the routed cache is fresh and masks it when the cache is stale."
        ),
        "environment_steps_for_state_construction": 2 * int(freeze["fixed_horizon_steps"]),
        "evaluation_episodes": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
        "automatic_p1_authorized": False,
    }
    return result, rows


def render_report(result: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# B-line P0R native-freshness paired counterexample",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "This CPU-only deterministic harness uses the unmodified six-UAV environment. It does not train a policy, evaluate a checkpoint, read an evaluation tape, tune a threshold, add an action, or change reward/termination/failure semantics.",
        "",
        "## Paired construction",
        "",
        "Both histories run for seven environment transitions with the default native `tau_max=5`. In the fresh history, scouts sense objective 0 at step 7. In the stale history, they sense that same objective at step 1. All terminal actions remain idle. Thus the final step count, geometry, active physical topology, task progress, role state, and assignments are identical; cache age is the only decision-relevant difference.",
        "",
        f"- Physical snapshot SHA-256: `{result['physical_snapshot_sha256']}`.",
        f"- Fresh action-mask SHA-256: `{result['action_mask_sha256']['fresh']}`.",
        f"- Stale action-mask SHA-256: `{result['action_mask_sha256']['stale']}`.",
        "",
        "## Native feasible-action distinction",
        "",
        "| Terminal | Fresh cache age | Stale cache age | Native action-1 legal when fresh | Native action-1 legal when stale |",
        "| ---: | ---: | ---: | :---: | :---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['terminal']} | {row['fresh_cache_age']} | {row['stale_cache_age']} | "
            f"{row['objective_zero_legal_when_fresh']} | {row['objective_zero_legal_when_stale']} |"
        )
    lines += [
        "",
        "The action difference is generated by the existing `_fresh_token` rule and `support_action_mask`; it is not a new score, penalty, action, or task constraint. Therefore a map based only on the current physical snapshot cannot reproduce both native feasible-action sets.",
        "",
        "## Boundary after GO",
        "",
        "This establishes the B-line scientific premise, not a solver or a method claim. A separate authorization is required before P1 formalization, novelty audit, algorithm naming, solver design, or benchmark work.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(output_dir: Path, result: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_lf(output_dir / "B_P0R_NATIVE_FRESHNESS_RESULT.json", canonical_json(result))
    fields = (
        "terminal", "fresh_cache_age", "stale_cache_age", "native_tau_max", "fresh_action_mask",
        "stale_action_mask", "objective_zero_legal_when_fresh", "objective_zero_legal_when_stale",
    )
    with (output_dir / "B_P0R_NATIVE_FRESHNESS_ACTION_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_lf(output_dir / "B_LINE_P0R_NATIVE_FRESHNESS_REPORT.md", render_report(result, rows))
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.iterdir()) if path.is_file()
    }
    write_lf(output_dir / "B_P0R_NATIVE_FRESHNESS_ARTIFACTS.json", canonical_json(hashes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run P0R without --execute")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output_dir}")
    result, rows = analyze()
    write_outputs(output_dir, result, rows)


if __name__ == "__main__":
    main()
