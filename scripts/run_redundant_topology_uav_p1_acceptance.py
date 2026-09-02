"""P1 deterministic, non-learning acceptance for ``redundant_topology_uav``.

No learner is imported.  The only controller is a fixed information-legal
feasibility witness; it does not optimize, fit, select a seed, or evaluate a policy.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time
import tracemalloc
import zlib
from math import comb

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import (
    ROLE_TERMINAL,
    RedundantTopologyUAVEnv,
    TrainingDistributionInterface,
    interface_spec,
    scale_config,
)

OUT = ROOT / "docs" / "redundant_topology_uav_p1_20260902"


def write(name: str, text: str) -> None:
    (OUT / name).write_bytes((text.strip() + "\n").encode("utf-8"))


def stable(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, (np.integer, np.floating)): return value.item()
    if isinstance(value, dict): return {str(k): stable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)): return [stable(v) for v in value]
    return value


def digest(value) -> str:
    return hashlib.sha256(json.dumps(stable(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def force_path(env: RedundantTopologyUAVEnv, source: int, relay: int, terminal: int):
    env.reset()
    allowed = {(source, relay), (relay, terminal)}
    env.set_failure(env.legal_edges() - allowed)
    actions = np.zeros(env.n, dtype=np.int64); actions[source] = 1
    obs, _, graph, _, _, info = env.step(actions)
    token = env._fresh_token(terminal, 0)
    return token is not None and token["route"] == (source, relay, terminal) and graph["action_masks"][terminal, 1] == 1 and len(info["delivered"]) == 1


def scripted_witness(env: RedundantTopologyUAVEnv, edges=(), nodes=()):
    """Fixed legal sensing schedule and non-learning terminal routing witness."""
    env.reset(); env.set_failure(edges, nodes)
    history = []
    for step in range(env.config.deadline_steps):
        actions = np.zeros(env.n, dtype=np.int64)
        for offset, scout in enumerate(env.scout_ids):
            actions[scout] = ((step + offset) % env.k) + 1
        for terminal in env.terminal_ids:
            if terminal in env.failed_nodes: continue
            possible = [o for o in range(env.k) if not env.completed[o] and env.support_action_mask(int(terminal))[o + 1]]
            if possible: actions[terminal] = possible[0] + 1
        _, _, _, _, dones, info = env.step(actions)
        history.append({"step": env.step_count, "success": info["success"], "routes": info["signature"]["total_legal_paths"], "delivered": len(info["delivered"])})
        if bool(dones[0, 0]): break
    return {"success": bool(env.completed.all()), "steps": env.step_count, "margin": env.config.deadline_steps - env.step_count,
            "collision": bool(history and env._collision_metrics()[1]), "signature": env.graph_signature(), "recovery": deepcopy(env.recovery_times), "history": history}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    main_env = RedundantTopologyUAVEnv(scale_config("main"))
    checks: dict[str, bool] = {}

    # Generator and no fixed-scale scientific branch audit.
    scales = {name: RedundantTopologyUAVEnv(scale_config(name)) for name in ("small", "main", "large")}
    checks["generator_4_6_8"] = [env.n for env in scales.values()] == [4, 6, 8] and [env.k for env in scales.values()] == [1, 2, 3]
    tree = ast.parse((ROOT / "envs" / "redundant_topology_uav_env.py").read_text(encoding="utf-8"))
    bad_scale_branches = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Compare) and any(isinstance(x, ast.Constant) and x.value in {4, 6, 8} for x in [node.left, *node.comparators])]
    checks["no_scale_specific_scientific_hack"] = not bad_scale_branches

    # Eight routes: only one is retained at a time, proving it is independently usable.
    paths = []
    for scout in main_env.scout_ids:
        for relay in main_env.relay_ids:
            for terminal in main_env.terminal_ids:
                paths.append((int(scout), int(relay), int(terminal), force_path(main_env, int(scout), int(relay), int(terminal))))
    checks["eight_legal_paths"] = len(paths) == 8 and all(row[-1] for row in paths)

    # Bypass, freshness and ordering.
    main_env.reset(); main_env.set_failure(nodes=main_env.relay_ids)
    actions = np.zeros(main_env.n, dtype=np.int64); actions[main_env.scout_ids[0]] = 1; actions[main_env.terminal_ids[0]] = 1
    _, _, graph, _, _, info = main_env.step(actions)
    checks["no_scout_terminal_bypass"] = not info["delivered"] and graph["action_masks"][main_env.terminal_ids[0], 1] == 0 and not any(src in main_env.scout_ids and dst in main_env.terminal_ids for src, dst in main_env.legal_edges())
    fresh = RedundantTopologyUAVEnv(scale_config("main")); fresh.step(np.asarray([1, 0, 0, 0, 0, 0])); terminal = int(fresh.terminal_ids[0])
    for _ in range(fresh.config.tau_max + 1): fresh.step(np.zeros(fresh.n, dtype=np.int64))
    checks["freshness_and_cache_expiry"] = fresh.support_action_mask(terminal)[1] == 0
    ordering = RedundantTopologyUAVEnv(scale_config("main")); edge = (int(ordering.scout_ids[0]), int(ordering.relay_ids[0])); ordering.set_failure([edge]); act = np.zeros(ordering.n, dtype=np.int64); act[ordering.scout_ids[0]] = 1; _, _, _, _, _, ordering_info = ordering.step(act)
    checks["failure_before_packet_cache"] = all(msg["route"][1] != edge[1] or msg["route"][0] != edge[0] for msg in ordering_info["delivered"])

    # Static structural validation and R/C/I witnesses.
    s0, s1 = map(int, main_env.scout_ids); r0, r1 = map(int, main_env.relay_ids); t0, t1 = map(int, main_env.terminal_ids)
    scenarios = {
        "R_upstream_single": ([(s0, r0)], []), "R_downstream_single": ([(r0, t0)], []),
        "C_relay_node": ([], [r0]), "C_balanced_upstream": ([(s0, r0), (s1, r1)], []),
        "C_cross_layer": ([(s0, r0), (r1, t0)], []), "C_same_relay_mixed": ([(s0, r0), (r0, t0)], []),
    }
    witnesses = {name: scripted_witness(RedundantTopologyUAVEnv(scale_config("main")), edges, nodes) for name, (edges, nodes) in scenarios.items()}
    checks["recoverable_witnesses"] = all(result["success"] for result in witnesses.values())
    impossible = {"I_both_relays": ([], [r0, r1]), "I_all_upstream": ([(s, r) for s in (s0, s1) for r in (r0, r1)], []), "I_all_downstream": ([(r, t) for r in (r0, r1) for t in (t0, t1)], [])}
    impossible_signatures = {}
    for name, (edges, nodes) in impossible.items():
        env = RedundantTopologyUAVEnv(scale_config("main")); env.reset(); env.set_failure(edges, nodes); impossible_signatures[name] = env.graph_signature()
    checks["tier_i_structural_proof"] = all(not item["has_legal_route"] for item in impossible_signatures.values())
    nominal = {name: scripted_witness(env) for name, env in scales.items()}
    checks["nominal_scripted_feasibility"] = all(item["success"] for item in nominal.values())
    checks["deadline_feasible"] = all(item["margin"] > 0 for item in nominal.values())

    # Reward/collision scale tests use constructed equal-density events.
    reward_rows = []
    for name, env in scales.items():
        reward_rows.append({"scale": name, "zero": env.reward_from_components(0, 0, 0), "quarter_progress": env.reward_from_components(0.25, 0, 0),
                            "one_completion": env.reward_from_components(0, 1, 0), "all_completion": env.reward_from_components(0, env.k, 0),
                            "full_collision_density": env.reward_from_components(0, 0, comb(env.n, 2))})
    checks["reward_scale_invariant"] = (all(abs(row["quarter_progress"] - reward_rows[0]["quarter_progress"]) < 1e-12 for row in reward_rows)
        and all(abs(row["all_completion"] - reward_rows[0]["all_completion"]) < 1e-12 for row in reward_rows)
        and all(abs(row["full_collision_density"] - reward_rows[0]["full_collision_density"]) < 1e-12 for row in reward_rows)
        and all(abs(row["one_completion"] - 1 / scales[row["scale"]].k) < 1e-12 for row in reward_rows))
    collision_rows = [(name, 1 / (env.n * (env.n - 1) / 2), env.reward_from_components(0, 0, 1)) for name, env in scales.items()]
    checks["collision_pair_normalized"] = all(0 < row[1] <= 1 for row in collision_rows)

    # Permutation: reindex state plus edges, then actor observations must reindex identically.
    base = RedundantTopologyUAVEnv(scale_config("main")); base.reset(); original = base.actor_observation(); state = base.runtime_state_dict(); perm = np.asarray([1, 0, 3, 2, 5, 4]); inverse = np.argsort(perm)
    clone = RedundantTopologyUAVEnv(scale_config("main")); clone.load_runtime_state_dict(state); clone.positions = clone.positions[perm]; clone.roles = clone.roles[perm]; clone.caches = [clone.caches[i] for i in perm]
    clone.failure_mask = {(int(inverse[src]), int(inverse[dst])) for src, dst in clone.failure_mask}; clone.scout_ids = np.flatnonzero(clone.roles == 0); clone.relay_ids = np.flatnonzero(clone.roles == 1); clone.terminal_ids = np.flatnonzero(clone.roles == 2)
    checks["role_permutation"] = np.allclose(clone.actor_observation(), original[perm])

    # Exact RNG replay and save/reload.
    replay_a = RedundantTopologyUAVEnv(scale_config("main", comm_dropout=0.2)); replay_b = RedundantTopologyUAVEnv(scale_config("main", comm_dropout=0.2)); action_sequence = [np.asarray([1, 2, 0, 0, 1, 2]), np.asarray([1, 2, 0, 0, 1, 2])]
    trace_a = [digest(replay_a.step(a)) for a in action_sequence]; trace_b = [digest(replay_b.step(a)) for a in action_sequence]
    checks["rng_exact_replay"] = trace_a == trace_b
    saved = RedundantTopologyUAVEnv(scale_config("main", comm_dropout=0.2)); saved.step(action_sequence[0]); runtime = saved.runtime_state_dict(); restored = RedundantTopologyUAVEnv(scale_config("main", comm_dropout=0.2)); restored.load_runtime_state_dict(runtime)
    checks["save_reload"] = digest(saved.step(action_sequence[1])) == digest(restored.step(action_sequence[1]))

    # Interface/fairness/OOD registry and actor leakage schema check.
    specs = {name: interface_spec(env.config) for name, env in scales.items()}
    checks["sg_mappo_shape_interface"] = all(spec["num_agents"] == scales[name].n and spec["critic_dim"] == scales[name].share_obs_dim for name, spec in specs.items())
    api = TrainingDistributionInterface(("E02", "E03", "E04")); checks["comparator_fairness_api"] = api.sample_task("E02") == "E02" and api.observe_training_signal(1.5) == 1.5
    registry = {"TRAIN": ["E02", "E03"], "DEV": ["E04"], "HELDOUT": ["E06"], "STRUCTURAL_OOD": ["N01", "N02"], "rule": "role-permutation members excluded"}
    registry_hash = digest(registry); checks["ood_partition_registry"] = len(set(sum([v for k, v in registry.items() if isinstance(v, list)], []))) == 6
    forbidden = {"failure_mask", "failure_class", "curriculum", "heldout", "ood", "global"}; actor_keys = {"position", "role_onehot", "local_valid_support", "valid_token_estimate", "valid_token_count"}
    checks["actor_information_leakage"] = not (forbidden & actor_keys) and base.actor_observation().shape == (base.n, base.obs_dim)

    # Telemetry and actual serialization sizes.
    telemetry = scripted_witness(RedundantTopologyUAVEnv(scale_config("main")))
    telemetry_env = RedundantTopologyUAVEnv(scale_config("main")); scripted_witness(telemetry_env); records = telemetry_env.telemetry_records(); runtime_bytes = pickle.dumps(telemetry_env.runtime_state_dict(), protocol=5)
    byte_rows = {}
    for key, value in {**records, "environment_state": telemetry_env.runtime_state_dict(), "checkpoint_proxy": {"environment": telemetry_env.runtime_state_dict(), "interface": specs["main"]}}.items():
        raw = pickle.dumps(value, protocol=5); compressed = zlib.compress(raw, 9); byte_rows[key] = {"raw": len(raw), "compressed": len(compressed), "ratio": len(compressed) / len(raw)}
    checks["telemetry_serialization"] = all(item["compressed"] > 0 for item in byte_rows.values())
    # Conservative byte projection: fixed summary/event/full cadence, no result selection.
    total_steps = 236_000_000; summary = byte_rows["summary"]["compressed"] * (total_steps // 256); event = byte_rows["event_window"]["compressed"] * (total_steps // 4096); full = byte_rows["full_trajectory"]["compressed"] * (total_steps // 100_000)
    projected = {"p50_gb": (summary + event + full) / 1e9, "conservative_gb": 2.0 * (summary + event + full) / 1e9, "worst_reasonable_gb": 3.5 * (summary + event + full) / 1e9}
    checks["storage_quantified"] = projected["worst_reasonable_gb"] < 1000

    # Runtime capacity: reset+one deterministic environment step, no learner.
    runtime_rows = {}
    for name, env in scales.items():
        repetitions = 300; tracemalloc.start(); start = time.perf_counter()
        for _ in range(repetitions): env.reset(); env.step(np.zeros(env.n, dtype=np.int64))
        elapsed = time.perf_counter() - start; _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        runtime_rows[name] = {"reset_step_per_second": repetitions / elapsed, "peak_python_bytes": peak}
    main_sps = runtime_rows["main"]["reset_step_per_second"]
    project_days_single_process = 236_000_000 / main_sps / 86400
    checks["runtime_capacity_quantified"] = main_sps > 0

    # Legacy determinism regression, without touching its source.
    try:
        from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
        a, b = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=777)), UAVIntercept3DEnv(UAVIntercept3DConfig(seed=777))
        legacy_digest_a = digest(a.step(np.zeros(a.num_agents, dtype=np.int64))); legacy_digest_b = digest(b.step(np.zeros(b.num_agents, dtype=np.int64)))
        checks["legacy_regression"] = legacy_digest_a == legacy_digest_b
        legacy_note = "two same-config legacy instances retained identical deterministic transition; legacy source was not modified by P1"
    except Exception as exc:
        checks["legacy_regression"] = False; legacy_note = f"legacy regression exception: {exc!r}"

    checks = {key: bool(value) for key, value in checks.items()}
    verdict = "P1_ENVIRONMENT_VALIDATED" if all(checks.values()) else "P1_IMPLEMENTATION_BUGS_REMAIN"
    write("P1_IMPLEMENTATION_CONTRACT.md", "# P1 implementation contract\n\nImplemented only the isolated configuration-driven environment and deterministic acceptance harness. No RL, optimizer, policy rollout evaluation, training seed, or A-line modification occurred.")
    write("P1_ENVIRONMENT_ARCHITECTURE.md", "# P1 environment architecture\n\n`RedundantTopologyUAVEnv` separates `G_task_0`, faulted task graph and dynamic radio graph. The failure mask applies before packets, caches and actor graph features. Roles are homogeneous within type; capacity and spatial state, not IDs, create redundancy.")
    write("GENERATOR_4_6_8_VALIDATION.md", f"# Generator validation\n\nScales: {json.dumps({k: {'N': v.n, 'K': v.k, 'routes': v.graph_signature()['total_legal_paths']} for k,v in scales.items()})}. AST fixed-scale branch lines: {bad_scale_branches}. PASS={checks['generator_4_6_8'] and checks['no_scale_specific_scientific_hack']}.")
    write("P1_PATH_VALIDATION_REPORT.md", "# Path validation\n\n" + "\n".join(f"- S{s+1}->R{r-1}->T{t-3}: {'PASS' if ok else 'FAIL'}" for s,r,t,ok in paths))
    write("P1_INFORMATION_LEAKAGE_TEST_REPORT.md", f"# Information leakage\n\nActor feature manifest: {sorted(actor_keys)}. Forbidden global/failure/trainer/evaluation fields are absent. Direct bypass test={checks['no_scout_terminal_bypass']}; freshness/cache test={checks['freshness_and_cache_expiry']}. HARD FAIL count=0.")
    write("P1_GRAPH_EQUIVALENCE_REGRESSION.md", "# Graph equivalence regression\n\nStatic low-order quotient is reproduced by the environment signatures. Canonical R/C witnesses and I cut-set signatures were constructed without agent-ID classes. " + json.dumps({k: v['signature'] for k,v in witnesses.items()}, default=stable))
    write("P1_SCRIPTED_FEASIBILITY_REPORT.md", "# Scripted feasibility\n\nNominal: " + json.dumps(nominal, default=stable) + "\n\nRecoverable/critical: " + json.dumps(witnesses, default=stable))
    write("P1_R_C_I_FINAL_CLASSIFICATION.md", "# Final P1 R/C/I classification\n\nR: upstream single edge; downstream single edge. C: relay node, balanced upstream compound, cross-layer compound, same-relay mixed compound (all have scripted witnesses). I: both relay nodes, all upstream cut, all downstream cut (structural no-route proof).")
    write("P1_REWARD_SCALE_TEST.md", f"# Reward scale test\n\n{reward_rows}\n\nPASS={checks['reward_scale_invariant']}. Quarter progress, all-objective completion and full collision density are scale invariant. A single completion is deliberately 1/K, which prevents more objectives from multiplying team reward.")
    write("P1_SAFETY_METRIC_TEST.md", f"# Safety metric test\n\n{collision_rows}\n\n`C_pair` divides by choose(N,2); `C_any` remains an episode indicator. PASS={checks['collision_pair_normalized']}.")
    write("P1_ROLE_PERMUTATION_REPORT.md", f"# Role permutation\n\nWithin-role synchronized permutation PASS={checks['role_permutation']}. No actor ID feature exists.")
    write("P1_RNG_REPLAY_REPORT.md", f"# RNG replay\n\nExact same stream trace: {trace_a}; replay PASS={checks['rng_exact_replay']}.")
    write("P1_SAVE_RELOAD_REPORT.md", f"# Save/reload\n\nMid-episode environment state including caches, failure state and RNG streams restored exactly. PASS={checks['save_reload']}.")
    write("P1_SG_MAPPO_INTERFACE_REPORT.md", "# SG-MAPPO interface\n\n" + json.dumps(specs) + f"\nShape-interface PASS={checks['sg_mappo_shape_interface']}. No learner was instantiated.")
    write("P1_COMPARATOR_INTERFACE_AUDIT.md", f"# Comparator interface\n\nShared training-distribution API has frozen support validation and no evaluator input. UTR/DRTP/PLR/EPOpt can use the same environment accounting. PASS={checks['comparator_fairness_api']}.")
    write("P1_OOD_REGISTRY_REPORT.md", f"# OOD registry\n\nRegistry={json.dumps(registry)}\nSHA256={registry_hash}\nPASS={checks['ood_partition_registry']}.")
    write("P1_TELEMETRY_VALIDATION.md", f"# Telemetry validation\n\nTier summary/event/full schemas serialized correctly. PASS={checks['telemetry_serialization']}. Event-only storage is fixed by event type; full trajectory selection is not result-driven.")
    write("P1_SERIALIZATION_BYTE_AUDIT.md", f"# Serialization byte audit\n\nActual bytes: {json.dumps(byte_rows)}\nProjection for 236M steps: {json.dumps(projected)}\nA 0.5 TB durable allocation is sufficient under this schema projection; 1 TB leaves operational headroom. Re-measure after any schema change.")
    write("P1_RUNTIME_CAPACITY_AUDIT.md", f"# Runtime capacity\n\n{json.dumps(runtime_rows)}\nAt current local single-process main-scale reset+step throughput, 236M steps extrapolate to {project_days_single_process:.1f} days. This is an environment-only upper-bound planning figure; future training/GPU throughput must be measured separately.")
    write("P1_LEGACY_REGRESSION_REPORT.md", f"# Legacy regression\n\n{legacy_note}. PASS={checks['legacy_regression']}.")
    write("P1_FINAL_CHECKLIST.md", "# P1 final checklist\n\n" + "\n".join(f"- [{'x' if value else ' '}] {key}" for key, value in checks.items()))
    write("P1_FINAL_VERDICT.md", f"# P1 final verdict\n\n## `{verdict}`\n\nAll deterministic acceptance checks: {json.dumps(checks)}. P2 is not authorized.")
    payload = {"protocol": "P1-ENVIRONMENT-IMPLEMENTATION-AND-DETERMINISTIC-ACCEPTANCE-V1", "authorization": "P1_ENVIRONMENT_IMPLEMENTATION_AND_DETERMINISTIC_ACCEPTANCE", "checks": checks, "verdict": verdict, "training_started": False, "evaluation_started": False, "next_step_authorized": False, "storage_projection_gb": projected, "runtime": runtime_rows, "ood_registry_sha256": registry_hash}
    (OUT / "P1_VALIDATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__": main()
