"""One-shot, passive step telemetry acquisition for frozen Phase-D UTR checkpoints.

This is a diagnostic replay only.  It refuses to train, continue checkpoints,
create a tape, or overwrite any historical Phase-D artifact.  The input root
must be the already completed Phase-D 2M result directory.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from envs.uav_intercept_3d_env import ACTION3D_TABLE, velocity_from_state  # noqa: E402
from run_phase_fl_single import build_agent  # noqa: E402
import run_phase_rsg1_development_smoke as historical_evaluator  # noqa: E402
from run_phase_rsg1_development_smoke import policy_action  # noqa: E402
from run_tcr_spc_phase_c_evaluation import variant_env  # noqa: E402
from scripts.utr_one_shot_telemetry_contract import (  # noqa: E402
    EPISODES_PER_CONDITION,
    EXPECTED_TAPE_HASH,
    PROTOCOL,
    SELECTED_CONDITIONS,
    UTR_SEEDS,
)


INVARIANCE_FIELDS = (
    "J", "success_at_horizon", "collision", "timeout", "constraint_violation",
    "terminal_step", "failure_exposed", "direct_path_fraction_during_failure",
    "relay_path_fraction_during_failure", "task_support_fraction_during_failure",
    "legal_information_fraction_during_failure", "mean_cache_age_during_failure",
    "path_switch_count", "traveled_distance", "control_effort",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def write_json(path: Path, value: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite diagnostic artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(handle: Any, value: dict) -> None:
    handle.write(json.dumps(json_safe(value), sort_keys=True, separators=(",", ":")) + "\n")


def termination_reason(info: dict[str, Any]) -> str:
    if float(info.get("success", 0.0)) > 0.5:
        return "success"
    if float(info.get("collision", 0.0)) > 0.5:
        return "collision"
    if float(info.get("constraint_violation", 0.0)) > 0.5:
        return "constraint_violation"
    if float(info.get("timeout", 0.0)) > 0.5:
        return "timeout"
    return "unknown_terminal"


def matrix_signature(matrix: np.ndarray) -> str:
    return "".join(str(int(value > 0.5)) for value in matrix.reshape(-1))


def relation_signature(relation_adj: np.ndarray) -> str:
    return "|".join(matrix_signature(relation_adj[index]) for index in range(relation_adj.shape[0]))


def graph_state(graph: dict[str, Any]) -> dict[str, Any]:
    adj = np.asarray(graph["adj"], dtype=np.float32)
    relation = np.asarray(graph["relation_adj"], dtype=np.float32)
    return {
        "adjacency": adj,
        "relation_adjacency": relation,
        "adjacency_signature": matrix_signature(adj),
        "relation_signature": relation_signature(relation),
        # Frozen convention: A[receiver, sender].
        "scout_to_attacker_direct": int(adj[2, 0] > 0.5),
        "scout_to_relay": int(adj[1, 0] > 0.5),
        "relay_to_attacker": int(adj[2, 1] > 0.5),
        "relay_outgoing_or_incoming": int(np.any(adj[1, :] > 0.5) or np.any(adj[:, 1] > 0.5)),
    }


def physical_state(env: Any) -> dict[str, Any]:
    blue_velocity = np.asarray([
        velocity_from_state(float(env.blue_speed[index]), float(env.blue_heading[index]), float(env.blue_gamma[index]))
        for index in range(env.config.num_blue)
    ], dtype=np.float32)
    target_distance = np.linalg.norm(env.red_pos[0][None, :] - env.blue_pos, axis=1)
    teammate_distance = np.linalg.norm(env.blue_pos[:, None, :] - env.blue_pos[None, :, :], axis=-1)
    return {
        "blue_position": env.blue_pos.copy(),
        "blue_velocity": blue_velocity,
        "blue_heading": env.blue_heading.copy(),
        "blue_gamma": env.blue_gamma.copy(),
        "blue_speed": env.blue_speed.copy(),
        "target_relative_distance": target_distance,
        "teammate_relative_distance": teammate_distance,
    }


def task_state(info: dict[str, Any], env: Any) -> dict[str, Any]:
    fields = (
        "tracking_rate", "attack_window_rate", "attack_geometry_score", "chain_support_t",
        "relay_dependency_eligible_t", "attacker_direct_target_information_t",
        "attacker_fresh_cache_information_t", "attacker_legal_target_information_t",
        "attacker_direct_recovery_path_t", "attacker_cache_paths_t", "attacker_cache_source_ids_t",
        "attacker_cache_path_includes_relay1_t", "attacker_support_path_relay1_required_t",
        "chain_closed", "target_cache_age_mean", "target_cache_confidence_mean",
        "target_cache_stale_rate", "attacker_has_fresh_target_info", "mean_range",
        "min_blue_red_distance", "min_blue_blue_distance", "comm_connectivity",
    )
    return {
        "existing_info": {field: json_safe(info.get(field)) for field in fields},
        "detected_by": env.detected_by.copy(),
        "attack_window": env.attack_window.copy(),
    }


def condition_specs(tape: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_name = {str(row["name"]): row for row in tape["conditions"]}
    missing = [name for name in SELECTED_CONDITIONS.values() if name not in by_name]
    if missing:
        raise RuntimeError(f"frozen selected conditions missing from historical tape: {missing}")
    expected = {
        "nominal": (-1, 0, 0), "f0_seen_44_80": (1, 44, 80),
        "timing_28_80": (1, 28, 80), "timing_60_80": (1, 60, 80),
        "duration_44_40": (1, 44, 40), "duration_44_120": (1, 44, 120),
        "compound_28_120": (1, 28, 120),
    }
    for name, values in expected.items():
        row = by_name[name]
        actual = (int(row["failed_blue_agent"]), int(row["start_step"]), int(row["duration_steps"]))
        if actual != values:
            raise RuntimeError(f"condition descriptor mismatch for {name}: {actual} != {values}")
    return by_name


def load_phase_d_inputs(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[tuple[int, str, int], dict[str, str]]]:
    tape_path = root / "tape_manifest.json"
    decision_path = root / "evaluations" / "final_2m" / "PHASE_D_2M_INTERIM_DECISION.json"
    raw_path = root / "evaluations" / "final_2m" / "raw_episode_metrics.csv"
    for path in (tape_path, decision_path, raw_path):
        if not path.exists():
            raise FileNotFoundError(f"missing frozen Phase-D input: {path}")
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    if tape.get("tape_hash") != EXPECTED_TAPE_HASH or tape.get("canonical") is not False:
        raise RuntimeError("Phase-D tape hash/canonical status violates the telemetry contract")
    specs = condition_specs(tape)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if decision.get("decision") != "STOP_AT_2M" or int(decision.get("interim_steps", -1)) != 2_000_128:
        raise RuntimeError("unexpected Phase-D decision/budget")
    with raw_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    expected_rows = 18_000
    if len(rows) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} historical raw rows, found {len(rows)}")
    historical: dict[tuple[int, str, int], dict[str, str]] = {}
    for row in rows:
        if row.get("method") != "utr_sg":
            continue
        key = (int(row["train_seed"]), str(row["topology_condition"]), int(row["development_episode_id"]))
        if key in historical:
            raise RuntimeError(f"duplicate historical UTR row: {key}")
        historical[key] = row
    required = len(UTR_SEEDS) * len(tape["conditions"]) * len(tape["episode_ids"])
    if len(historical) != required:
        raise RuntimeError(f"expected {required} UTR historical rows, found {len(historical)}")
    return tape, specs, historical


def validate_checkpoint(root: Path, seed: int) -> tuple[Path, dict[str, Any]]:
    run_dir = root / "runs" / "utr_sg" / f"seed{seed}"
    manifest_path = run_dir / "run_manifest.json"
    checkpoint = run_dir / "actor_critic_latest.pt"
    for path in (manifest_path, checkpoint):
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"missing frozen UTR artifact: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "status": "completed", "parameter_count": 116728, "final_checkpoint_only": True,
        "strict_continuation": True, "warm_restart_used": False,
        "final_environment_steps": 2_000_128,
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            raise RuntimeError(f"UTR seed{seed} manifest mismatch: {key}={manifest.get(key)!r}")
    expected_hash = manifest.get("final_checkpoint_sha256", manifest.get("checkpoint_sha256"))
    actual_hash = sha256(checkpoint)
    if actual_hash != expected_hash:
        raise RuntimeError(f"UTR seed{seed} checkpoint hash mismatch")
    return checkpoint, manifest


def summarize_episode(
    *, seed: int, descriptor: str, condition_name: str, episode_id: int,
    onset: int, duration: int, reward_sum: float, records: list[dict[str, Any]],
) -> dict[str, Any]:
    final = records[-1]
    active = [row for row in records if row["failure_active_post"]]
    denom = max(1, len(active))
    paths = [str(row["task_state_post"]["existing_info"].get("attacker_cache_paths_t", "")) for row in records]
    path_switch_count = sum(left != right for left, right in zip(paths, paths[1:]))
    return {
        "protocol": PROTOCOL, "checkpoint_seed": seed, "descriptor": descriptor,
        "topology_condition": condition_name, "development_episode_id": episode_id,
        "scheduled_failure_onset": onset, "scheduled_failure_duration": duration,
        "actual_failure_onset": next((row["post_step"] for row in records if row["failure_active_post"]), None),
        "J": reward_sum, "success_at_horizon": final["success_terminal"],
        "collision": final["collision_terminal"], "timeout": final["timeout_terminal"],
        "constraint_violation": final["constraint_terminal"],
        "terminal_step": final["termination_step"], "termination_reason": final["termination_reason"],
        "failure_exposed": int(bool(active)),
        "direct_path_fraction_during_failure": sum(row["path_direct_post"] for row in active) / denom,
        "relay_path_fraction_during_failure": sum(row["path_relay_post"] for row in active) / denom,
        "task_support_fraction_during_failure": sum(row["task_support_post"] for row in active) / denom,
        "legal_information_fraction_during_failure": sum(row["legal_information_post"] for row in active) / denom,
        "mean_cache_age_during_failure": (
            float(np.mean([row["cache_age_post"] for row in active])) if active else None
        ),
        "path_switch_count": path_switch_count,
        "traveled_distance": float(sum(row["movement_distance"] for row in records)),
        "control_effort": float(sum(row["control_effort"] for row in records)),
        "step_records": len(records),
    }


def compare_values(left: Any, right: Any, *, field: str) -> bool:
    def missing(value: Any) -> bool:
        if value in (None, ""):
            return True
        try:
            return math.isnan(float(value))
        except (TypeError, ValueError):
            return False

    if missing(left) or missing(right):
        return missing(left) and missing(right)
    if field in {"terminal_step", "path_switch_count"}:
        return int(left) == int(float(right))
    try:
        return abs(float(left) - float(right)) <= 1e-6
    except (TypeError, ValueError):
        return left == right


def compare_summary(summary: dict[str, Any], historical: dict[str, str]) -> list[str]:
    failures = []
    for field in INVARIANCE_FIELDS:
        if not compare_values(summary.get(field), historical.get(field), field=field):
            failures.append(f"{field}: telemetry={summary.get(field)!r}, historical={historical.get(field)!r}")
    return failures


def historical_style_episode(agent: Any, seed: int, episode_id: int, condition_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Execute the unmodified historical evaluator path for the invariance gate."""
    failure_spec = None if condition_name == "nominal" else (int(spec["start_step"]), int(spec["duration_steps"]))
    original = historical_evaluator.frozen_env
    historical_evaluator.frozen_env = lambda episode_seed, _failure: variant_env(episode_seed, failure_spec)
    try:
        row, _ = historical_evaluator.evaluate_episode(
            agent, "utr_sg", seed, episode_id, "nominal" if condition_name == "nominal" else "relay_failure"
        )
    finally:
        historical_evaluator.frozen_env = original
    return row


def run_episode(
    *, agent: Any, seed: int, descriptor: str, condition_name: str, spec: dict[str, Any],
    episode_id: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    failure_spec = None if condition_name == "nominal" else (int(spec["start_step"]), int(spec["duration_steps"]))
    env = variant_env(episode_id, failure_spec)
    obs, share, graph = env.reset()
    records: list[dict[str, Any]] = []
    reward_sum = 0.0
    previous_position = env.blue_pos.copy()
    previous_post_signature: str | None = None
    while True:
        pre_step = int(env.step_count)
        pre_graph = graph_state(graph)
        pre_physical = physical_state(env)
        actions = np.asarray(policy_action(agent, obs, share, graph), dtype=np.int64)
        action_components = np.asarray(ACTION3D_TABLE[actions], dtype=np.float32)
        obs, share, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        post_graph = graph_state(graph)
        post_physical = physical_state(env)
        movement_distance = float(np.linalg.norm(env.blue_pos - previous_position, axis=1).sum())
        previous_position = env.blue_pos.copy()
        post_task = task_state(info, env)
        path_text = str(post_task["existing_info"].get("attacker_cache_paths_t", ""))
        failure_active = int(float(info.get("node_failure_active", 0.0)) > 0.5)
        terminal = bool(np.all(dones))
        record = {
            "protocol": PROTOCOL, "checkpoint_seed": seed, "descriptor": descriptor,
            "topology_condition": condition_name, "development_episode_id": episode_id,
            "timestep": pre_step, "post_step": int(info["step"]), "horizon": int(env.config.max_steps),
            "scheduled_failure_onset": int(spec["start_step"]),
            "scheduled_failure_duration": int(spec["duration_steps"]),
            "failure_active_pre": int(pre_step >= int(spec["start_step"]) and condition_name != "nominal"),
            "failure_active_post": failure_active, "alive_pre": 1, "alive_post": int(not terminal),
            "action_index": actions, "applied_action_components": action_components,
            "action_norm": np.linalg.norm(action_components, axis=1),
            "control_effort": float(np.abs(action_components[:, :2]).sum()),
            "physical_state_pre": pre_physical, "physical_state_post": post_physical,
            "movement_distance": movement_distance,
            "topology_pre": pre_graph, "topology_post": post_graph,
            "topology_changed_from_previous": int(
                previous_post_signature is not None and post_graph["adjacency_signature"] != previous_post_signature
            ),
            "task_state_post": post_task,
            "path_direct_post": int(path_text == "0-2"),
            "path_relay_post": int(path_text == "0-1-2"),
            "task_support_post": int(float(info.get("chain_support_t", 0.0)) > 0.5),
            "legal_information_post": int(float(info.get("attacker_legal_target_information_t", 0.0)) > 0.5),
            "cache_age_post": float(info.get("target_cache_age_mean", 0.0)),
            "collision_post": int(float(info.get("collision", 0.0)) > 0.5),
            "constraint_post": int(float(info.get("constraint_violation", 0.0)) > 0.5),
            "terminal": int(terminal), "termination_reason": termination_reason(info) if terminal else "",
            "termination_step": int(info["step"]) if terminal else None,
            "success_terminal": int(float(info.get("success", 0.0)) > 0.5) if terminal else 0,
            "collision_terminal": int(float(info.get("collision", 0.0)) > 0.5) if terminal else 0,
            "timeout_terminal": int(float(info.get("timeout", 0.0)) > 0.5) if terminal else 0,
            "constraint_terminal": int(float(info.get("constraint_violation", 0.0)) > 0.5) if terminal else 0,
        }
        previous_post_signature = post_graph["adjacency_signature"]
        records.append(record)
        if terminal:
            break
    return summarize_episode(
        seed=seed, descriptor=descriptor, condition_name=condition_name, episode_id=episode_id,
        onset=int(spec["start_step"]), duration=int(spec["duration_steps"]), reward_sum=reward_sum, records=records,
    ), records


def preflight(
    *, phase_d_root: Path, tape: dict[str, Any], specs: dict[str, dict[str, Any]],
    historical: dict[tuple[int, str, int], dict[str, str]], output_root: Path,
) -> dict[str, Any]:
    """Compare no-logger/logger replays with historical summaries for 35 fixed cells."""
    first_id = int(tape["episode_ids"][0])
    checks = []
    started = time.perf_counter()
    for seed in UTR_SEEDS:
        checkpoint, _ = validate_checkpoint(phase_d_root, seed)
        agent = build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
        for descriptor, condition_name in SELECTED_CONDITIONS.items():
            spec = specs[condition_name]
            plain = historical_style_episode(agent, seed, first_id, condition_name, spec)
            logged, _ = run_episode(
                agent=agent, seed=seed, descriptor=descriptor, condition_name=condition_name,
                spec=spec, episode_id=first_id,
            )
            historical_row = historical[(seed, condition_name, first_id)]
            plain_vs_logged = [field for field in INVARIANCE_FIELDS if not compare_values(plain.get(field), logged.get(field), field=field)]
            logged_vs_historical = compare_summary(logged, historical_row)
            checks.append({
                "checkpoint_seed": seed, "descriptor": descriptor, "topology_condition": condition_name,
                "development_episode_id": first_id, "plain_vs_logged_mismatch": plain_vs_logged,
                "logged_vs_historical_mismatch": logged_vs_historical,
                "pass": not plain_vs_logged and not logged_vs_historical,
            })
    result = {
        "protocol": PROTOCOL, "checks": checks, "check_count": len(checks),
        "all_pass": all(row["pass"] for row in checks),
        "wall_clock_seconds": time.perf_counter() - started,
    }
    write_json(output_root / "integrity" / "telemetry_logging_invariance.json", result)
    if not result["all_pass"]:
        raise RuntimeError("TELEMETRY_LOGGING_SEMANTICS_INVARIANT = FAIL; full acquisition forbidden")
    return result


def selection_manifest(tape: dict[str, Any], specs: dict[str, dict[str, Any]], phase_d_root: Path) -> dict[str, Any]:
    selected_ids = [int(value) for value in sorted(tape["episode_ids"])[:EPISODES_PER_CONDITION]]
    if len(selected_ids) != EPISODES_PER_CONDITION:
        raise RuntimeError("historical tape has fewer than the frozen 50 diagnostic IDs")
    checkpoints = {}
    for seed in UTR_SEEDS:
        checkpoint, manifest = validate_checkpoint(phase_d_root, seed)
        checkpoints[str(seed)] = {
            "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
            "run_manifest_sha256": sha256(checkpoint.parent / "run_manifest.json"),
            "final_environment_steps": manifest["final_environment_steps"],
        }
    return {
        "protocol": PROTOCOL, "diagnostic_only": True, "new_tape_created": False,
        "phase_d_root": str(phase_d_root), "phase_d_tape_hash": tape["tape_hash"],
        "selected_descriptors": [
            {"label": label, "historical_condition": name, "definition": specs[name]}
            for label, name in SELECTED_CONDITIONS.items()
        ],
        "episode_selection": "first_50_sorted_existing_phase_d_tape_ids",
        "selected_episode_ids": selected_ids, "checkpoint_seeds": list(UTR_SEEDS),
        "expected_diagnostic_episodes": len(UTR_SEEDS) * len(SELECTED_CONDITIONS) * len(selected_ids),
        "checkpoint_provenance": checkpoints,
        "good_weak_ranking_frozen_before_telemetry": {
            "primary": "Phase-D 2M UTR J_OOD_worst", "good": [2103, 2002],
            "weak": [2102, 2104], "intermediate": [2101],
        },
    }


def schema() -> dict[str, Any]:
    return {
        "protocol": PROTOCOL,
        "raw_format": "gzip JSON Lines; one transition row per environment step",
        "actor_legal_fields": [
            "action_index", "applied_action_components", "action_norm", "topology_pre.adjacency",
            "topology_pre.relation_adjacency", "task_state_post.existing_info.*",
        ],
        "diagnostic_only_fields": [
            "physical_state_pre", "physical_state_post", "target_relative_distance",
            "teammate_relative_distance", "topology_post", "termination_reason", "terminal flags",
        ],
        "training_only_fields": [],
        "forbidden_actor_fields": ["simulator global state", "future state", "failure label unavailable online", "ground-truth route"],
        "frozen_adjacency_convention": "A[receiver, sender]",
        "raw_file": "raw/telemetry.jsonl.gz",
        "summary_file": "raw/episode_summaries.jsonl",
    }


def write_protocol_report(docs_root: Path, selection: dict[str, Any], integrity: dict[str, Any], output_root: Path) -> None:
    text = f"""# UTR One-Shot Telemetry Protocol and Integrity\n\n**Protocol:** `{PROTOCOL}`  \n**Status:** `TELEMETRY_LOGGING_SEMANTICS_INVARIANT = PASS`\n\n## Frozen inputs\n\n- Existing Phase-D tape hash: `{selection['phase_d_tape_hash']}`\n- Checkpoints: UTR seeds {', '.join(str(seed) for seed in UTR_SEEDS)}, each at 2,000,128 steps.\n- Descriptor labels: {', '.join(SELECTED_CONDITIONS)}.\n- Episode selection: first 50 sorted historical Phase-D tape IDs, reused identically for every checkpoint.\n- New random tape: **not created**.\n\n## Logger semantics check\n\nThe gate compared a fixed first historical descriptor ID across every checkpoint and selected condition: no-logger inference versus logger inference, then logger inference versus the historical episode aggregate. It checked return, termination reason proxies, terminal step, collision, timeout, constraint, exposure, and Phase-D aggregate topology/path/control fields.\n\n- Fixed checks: {integrity['check_count']}\n- All checks passed: `{integrity['all_pass']}`\n- Invariance wall-clock seconds: {integrity['wall_clock_seconds']:.3f}\n\nThe logger observes state after existing transitions and does not modify the actor forward pass, action, environment configuration, reward, RNG, transition, or termination semantics.\n\n## Field boundary\n\n- **ACTOR_LEGAL:** action outputs and the existing legal graph/info projections.\n- **DIAGNOSTIC_ONLY:** physical positions/velocities, full topology snapshots, terminal labels, and target-relative geometry. These are not actor inputs and may not be reused by a future actor.\n- **TRAINING_ONLY:** none.\n\nRaw append-only diagnostic files are under `{output_root}`.\n"""
    path = docs_root / "UTR_ONE_SHOT_TELEMETRY_PROTOCOL_AND_INTEGRITY.md"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite report: {path}")
    path.write_text(text, encoding="utf-8")


def write_data_manifest(docs_root: Path, output_root: Path, selection: dict[str, Any], step_count: int, episode_count: int, wall_clock: float) -> None:
    raw = output_root / "raw" / "telemetry.jsonl.gz"
    summaries = output_root / "raw" / "episode_summaries.jsonl"
    manifest = {
        "protocol": PROTOCOL, "diagnostic_only": True, "episodes": episode_count, "steps": step_count,
        "wall_clock_seconds": wall_clock, "raw_files": {
            "telemetry": {"path": str(raw), "sha256": sha256(raw), "bytes": raw.stat().st_size},
            "episode_summaries": {"path": str(summaries), "sha256": sha256(summaries), "bytes": summaries.stat().st_size},
        },
        "checkpoint_seeds": list(UTR_SEEDS), "selected_descriptors": selection["selected_descriptors"],
        "episodes_per_descriptor_per_checkpoint": EPISODES_PER_CONDITION,
        "missing_fields": [], "corruption_checks": {"complete_expected_episodes": episode_count == selection["expected_diagnostic_episodes"]},
    }
    write_json(output_root / "telemetry_data_manifest.json", manifest)
    lines = ["# UTR One-Shot Telemetry Data Manifest", "", "**Status:** completed — diagnostic-only", "",
             f"- Episodes: {episode_count}", f"- Step records: {step_count}", f"- Wall-clock seconds: {wall_clock:.3f}",
             f"- Telemetry SHA-256: `{manifest['raw_files']['telemetry']['sha256']}`",
             f"- Episode-summary SHA-256: `{manifest['raw_files']['episode_summaries']['sha256']}`", "",
             "Raw files are append-only diagnostic artifacts and do not overwrite Phase-D evaluation records."]
    path = docs_root / "UTR_ONE_SHOT_TELEMETRY_DATA_MANIFEST.md"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite report: {path}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def acquire(phase_d_root: Path, output_root: Path, docs_root: Path) -> None:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to append/overwrite existing diagnostic output: {output_root}")
    tape, specs, historical = load_phase_d_inputs(phase_d_root)
    output_root.mkdir(parents=True, exist_ok=False)
    selection = selection_manifest(tape, specs, phase_d_root)
    write_json(output_root / "selection_manifest.json", selection)
    write_json(output_root / "telemetry_schema.json", schema())
    integrity = preflight(
        phase_d_root=phase_d_root, tape=tape, specs=specs, historical=historical, output_root=output_root,
    )
    started = time.perf_counter()
    step_count = episode_count = 0
    raw_dir = output_root / "raw"; raw_dir.mkdir(exist_ok=False)
    telemetry_path = raw_dir / "telemetry.jsonl.gz"
    summary_path = raw_dir / "episode_summaries.jsonl"
    with gzip.GzipFile(filename=telemetry_path, mode="wb", mtime=0) as binary, \
         io.TextIOWrapper(binary, encoding="utf-8") as telemetry, \
         summary_path.open("x", encoding="utf-8") as summaries:
        for seed in UTR_SEEDS:
            checkpoint, _ = validate_checkpoint(phase_d_root, seed)
            agent = build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
            for descriptor, condition_name in SELECTED_CONDITIONS.items():
                spec = specs[condition_name]
                for episode_id in selection["selected_episode_ids"]:
                    summary, records = run_episode(
                        agent=agent, seed=seed, descriptor=descriptor, condition_name=condition_name,
                        spec=spec, episode_id=int(episode_id),
                    )
                    historical_row = historical[(seed, condition_name, int(episode_id))]
                    mismatch = compare_summary(summary, historical_row)
                    if mismatch:
                        raise RuntimeError(
                            f"historical aggregate mismatch during acquisition for seed={seed}, "
                            f"condition={condition_name}, episode={episode_id}: {mismatch}"
                        )
                    for row in records:
                        append_jsonl(telemetry, row)
                    append_jsonl(summaries, summary)
                    step_count += len(records); episode_count += 1
    wall_clock = time.perf_counter() - started
    if episode_count != selection["expected_diagnostic_episodes"]:
        raise RuntimeError(f"incomplete telemetry acquisition: {episode_count} episodes")
    write_data_manifest(docs_root, output_root, selection, step_count, episode_count, wall_clock)
    write_protocol_report(docs_root, selection, integrity, output_root)
    print(json.dumps({
        "status": "completed", "protocol": PROTOCOL, "episodes": episode_count, "steps": step_count,
        "wall_clock_seconds": wall_clock, "output_root": str(output_root),
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-d-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/diagnostics/utr_mechanism_v2"))
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: --execute is required for diagnostic inference")
    acquire(args.phase_d_root.resolve(), args.output_root.resolve(), args.docs_root.resolve())


if __name__ == "__main__":
    main()
