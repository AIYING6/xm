"""DRTP/UTR technical verification only; no development or canonical training."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ADAPT_INTERVAL,
    ALL_GROUPS,
    DIFFICULTY_MAX,
    DRTPSelection,
    DRTPTopologySampler,
    EMA_KAPPA,
    EPSILON,
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    NOMINAL_MASS,
    Q_MAX,
    Q_MIN,
    SMOOTHING_BETA,
    TEMPERATURE_ETA,
    UNIFORM_Q,
    WARMUP_UPDATES,
)
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    load_matching_state_dict,
    make_env,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


OUT = ROOT / "results" / "development" / "drtp_sg_technical_verification_v2"
TECHNICAL_SEEDS = {"utr": 9101, "drtp": 9102}


def frozen_cfg(seed: int, out_dir: Path, mode: str, logging: bool) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=4, rollout_steps=64,
        updates=1, hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False,
        target_kl=None, save_interval=1, save_snapshots=False,
        out_dir=str(out_dir), device="cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None,
        drtp_sampler_mode=mode, drtp_sampler_seed=seed,
        drtp_sampler_logging=logging,
    )


def build_sg(seed: int) -> RIGMAPPOAgent:
    env = make_env(frozen_cfg(seed, OUT / "parameter_probe", "utr", False), seed, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False,
    )


def selection(group: str) -> DRTPSelection:
    condition, onset, duration = GROUP_MEMBERS[group][0]
    return DRTPSelection(group, condition, onset, duration, -1 if group == NOMINAL_GROUP else 1)


def reference_projection(values: list[float]) -> list[float]:
    """Independent bisection used only to verify the frozen projection formula."""
    low, high = min(value - Q_MAX for value in values), max(value - Q_MIN for value in values)
    for _ in range(100):
        middle = (low + high) / 2.0
        total = sum(min(Q_MAX, max(Q_MIN, value - middle)) for value in values)
        if total > 1.0:
            low = middle
        else:
            high = middle
    result = [min(Q_MAX, max(Q_MIN, value - high)) for value in values]
    residual = 1.0 - sum(result)
    for index, value in enumerate(result):
        if abs(residual) <= 1e-12:
            break
        room = (Q_MAX - value) if residual > 0 else (value - Q_MIN)
        delta = math.copysign(min(abs(residual), max(0.0, room)), residual)
        result[index] += delta
        residual -= delta
    return result


def populate_boundary(sampler: DRTPTopologySampler, values: dict[str, float]) -> None:
    for group in ALL_GROUPS:
        sampler.record_completed_return(selection(group), values[group])


def sampler_checks() -> dict:
    checks: dict[str, bool] = {}
    checks["exact_group_set"] = tuple(GROUP_MEMBERS) == ALL_GROUPS
    checks["exact_failure_group_set"] = FAILURE_GROUPS == ("F0", "TE", "TL", "DS", "DL", "CP")
    checks["exact_member_counts"] = [len(GROUP_MEMBERS[group]) for group in ALL_GROUPS] == [1, 1, 2, 2, 2, 2, 2]
    checks["frozen_constants"] = (
        NOMINAL_MASS == 0.5 and UNIFORM_Q == 1.0 / 6.0 and WARMUP_UPDATES == 128
        and ADAPT_INTERVAL == 32 and EMA_KAPPA == 0.2 and TEMPERATURE_ETA == 1.0
        and SMOOTHING_BETA == 0.5 and DIFFICULTY_MAX == 2.0 and EPSILON == 1e-8
        and Q_MIN == 0.05 and Q_MAX == 0.35
    )

    utr = DRTPTopologySampler("utr", 9101, 3907)
    samples = [utr.select(0, index, 0) for index in range(60000)]
    counts = {group: sum(item.group == group for item in samples) for group in ALL_GROUPS}
    frequencies = {group: count / len(samples) for group, count in counts.items()}
    checks["utr_nominal_anchor_sampling"] = abs(frequencies[NOMINAL_GROUP] - 0.50) <= 0.015
    checks["utr_uniform_failure_sampling"] = all(abs(frequencies[group] - 1.0 / 12.0) <= 0.012 for group in FAILURE_GROUPS)
    checks["utr_weights_exact"] = all(abs(utr.q[group] - UNIFORM_Q) <= 1e-15 for group in FAILURE_GROUPS)

    replay_left, replay_right = DRTPTopologySampler("drtp", 9102, 3907), DRTPTopologySampler("drtp", 9102, 3907)
    coordinates = [(0, 0, 0), (32, 1, 2), (160, 2, 4), (256, 3, 5)]
    left_rows = [asdict(replay_left.select(*entry)) for entry in coordinates]
    right_rows = [asdict(replay_right.select(*entry)) for entry in coordinates]
    checks["deterministic_selection_replay"] = left_rows == right_rows

    values = {NOMINAL_GROUP: 100.0, "F0": -200.0, "TE": 90.0, "TL": 80.0, "DS": 70.0, "DL": 60.0, "CP": 50.0}
    drtp = DRTPTopologySampler("drtp", 9102, 3907)
    boundary_rows = []
    for update in (32, 64, 96, 128, 160):
        populate_boundary(drtp, values)
        row = drtp.maybe_update(update)
        assert row is not None
        boundary_rows.append(row)
    expected_difficulty = {
        group: min(DIFFICULTY_MAX, max(0.0, (values[NOMINAL_GROUP] - values[group]) / abs(values[NOMINAL_GROUP])))
        for group in FAILURE_GROUPS
    }
    mean_difficulty = sum(expected_difficulty.values()) / len(FAILURE_GROUPS)
    logits = [UNIFORM_Q * math.exp(TEMPERATURE_ETA * (expected_difficulty[group] - mean_difficulty)) for group in FAILURE_GROUPS]
    candidate = [value / sum(logits) for value in logits]
    expected_q = reference_projection([
        (1.0 - SMOOTHING_BETA) * UNIFORM_Q + SMOOTHING_BETA * value for value in candidate
    ])
    checks["warmup_is_uniform"] = all(not row["adapted"] and row["reason"] == "warmup" for row in boundary_rows[:-1])
    checks["bounded_exponential_update_triggered"] = boundary_rows[-1]["adapted"] and boundary_rows[-1]["reason"] == "bounded_exponentiated_gradient"
    checks["weight_update_matches_equation"] = all(abs(drtp.q[group] - expected_q[index]) <= 1e-10 for index, group in enumerate(FAILURE_GROUPS))
    checks["weight_bounds_and_mass"] = math.isclose(sum(drtp.q.values()), 1.0, abs_tol=1e-10) and all(Q_MIN <= value <= Q_MAX for value in drtp.q.values())
    checks["hardest_group_upweighted"] = drtp.q["F0"] == max(drtp.q.values()) and drtp.last_difficulty["F0"] == DIFFICULTY_MAX

    logging_left, logging_right = DRTPTopologySampler("drtp", 9111, 3907), DRTPTopologySampler("drtp", 9111, 3907)
    for update in (32, 64, 96, 128, 160):
        for sampler in (logging_left, logging_right):
            populate_boundary(sampler, values)
        # Calling the logging-only row constructor must not mutate the sampler.
        _ = logging_left.selection_row(update, 0, 0, logging_left.select(update, 0, 0))
        left = logging_left.maybe_update(update)
        right = logging_right.maybe_update(update)
        checks[f"logging_invariance_boundary_{update}"] = left == right and logging_left.q == logging_right.q
    return {**checks, "observed_utr_frequencies": frequencies, "adaptive_q": drtp.q,
            "adaptive_difficulty": drtp.last_difficulty, "boundary_rows": boundary_rows}


def failure_semantics_checks() -> dict:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=9101, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        max_steps=260, min_success_step=260,
    ))
    env.reset()
    baseline = asdict(env.config)
    sampler = DRTPTopologySampler("utr", 9101, 1)
    f0 = selection("F0")
    sampler.apply(env, f0)
    f0_config = asdict(env.config)
    long = selection("DL")
    sampler.apply(env, long)
    long_config = asdict(env.config)
    nominal = selection("N")
    sampler.apply(env, nominal)
    nominal_config = asdict(env.config)
    changed_f0 = {key for key in baseline if baseline[key] != f0_config[key]}
    changed_long = {key for key in f0_config if f0_config[key] != long_config[key]}
    changed_nominal = {key for key in long_config if long_config[key] != nominal_config[key]}
    sampler.apply(env, f0)
    env.step_count = 43; before = env._is_comm_failed(1)
    env.step_count = 44; start = env._is_comm_failed(1)
    env.step_count = 123; last = env._is_comm_failed(1)
    env.step_count = 124; after = env._is_comm_failed(1)
    return {
        "f0_changes_only_failure_fields": changed_f0 == {"failed_blue_agent", "node_failure_start_step", "node_failure_duration_steps"},
        "group_member_changes_only_frozen_failure_fields": changed_long.issubset({"failed_blue_agent", "node_failure_start_step", "node_failure_duration_steps"}),
        "nominal_restores_only_failure_fields": changed_nominal == {"failed_blue_agent", "node_failure_start_step", "node_failure_duration_steps"},
        "f0_timing_44_for_80": (not before) and start and last and (not after),
    }


def architecture_and_boundary_checks() -> dict:
    torch.manual_seed(7100); utr = build_sg(9101)
    torch.manual_seed(7100); drtp = build_sg(9101)
    utr_count = sum(parameter.numel() for parameter in utr.parameters() if parameter.requires_grad)
    drtp_count = sum(parameter.numel() for parameter in drtp.parameters() if parameter.requires_grad)
    sampler_manifest = DRTPTopologySampler("drtp", 9102, 3907).manifest()
    return {
        "utr_parameter_count": utr_count,
        "drtp_parameter_count": drtp_count,
        "matched_116728_parameters": utr_count == 116728 and drtp_count == 116728,
        "state_dict_keys_identical": set(utr.state_dict()) == set(drtp.state_dict()),
        "state_dict_values_identical_at_init": all(torch.equal(utr.state_dict()[key], drtp.state_dict()[key]) for key in utr.state_dict()),
        "single_graph_only": utr.actor.graph_encoder == "single" and drtp.actor.graph_encoder == "single",
        "no_sampler_policy_parameter": not any("drtp" in name.lower() or "utr" in name.lower() for name, _ in drtp.named_parameters()),
        "sampler_manifest_declares_no_policy_input": sampler_manifest["actor_or_critic_condition_input"] is False,
    }


def subprocess_check(command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {"pass": completed.returncode == 0, "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-1000:], "stderr_tail": completed.stderr[-1000:]}


def run_one_update(mode: str, seed: int, suffix: str, logging: bool) -> dict:
    out = OUT / suffix
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite smoke output: {out}")
    cfg = frozen_cfg(seed, out, mode, logging)
    train_ri_gmappo(cfg)
    checkpoint = out / "actor_critic_latest.pt"
    manifest = out / "drtp_topology_sampler_manifest.json"
    log = out / "drtp_topology_sampler_log.csv"
    reloaded = build_sg(seed)
    load_matching_state_dict(reloaded, str(checkpoint), torch.device("cpu"))
    return {
        "output": str(out), "mode": mode, "seed": seed,
        "train_log_exists": (out / "train_log.csv").exists(),
        "exactly_one_update": len((out / "train_log.csv").read_text(encoding="utf-8").splitlines()) == 2,
        "checkpoint_exists": checkpoint.exists() and checkpoint.stat().st_size > 0,
        "checkpoint_reload": checkpoint.exists(),
        "sampler_manifest_exists": manifest.exists(),
        "sampler_log_exists": (log.exists() and log.stat().st_size > 0) if logging else not log.exists(),
        "sampler_manifest": json.loads(manifest.read_text(encoding="utf-8")),
        "checkpoint_path": str(checkpoint),
    }


def smoke_checks() -> dict:
    utr = run_one_update("utr", TECHNICAL_SEEDS["utr"], "utr_one_update", True)
    drtp_on = run_one_update("drtp", TECHNICAL_SEEDS["drtp"], "drtp_one_update_logging_on", True)
    drtp_off = run_one_update("drtp", TECHNICAL_SEEDS["drtp"], "drtp_one_update_logging_off", False)
    state_on = torch.load(drtp_on["checkpoint_path"], map_location="cpu", weights_only=True)
    state_off = torch.load(drtp_off["checkpoint_path"], map_location="cpu", weights_only=True)
    return {
        "utr": utr, "drtp_logging_on": drtp_on, "drtp_logging_off": drtp_off,
        "logging_invariance_checkpoint_exact": set(state_on) == set(state_off) and all(torch.equal(state_on[key], state_off[key]) for key in state_on),
        "long_training_started": False,
        "canonical_seeds_used": False,
        "reserved_tapes_generated": False,
    }


def all_true(mapping: dict, ignored: set[str] | None = None) -> bool:
    ignored = ignored or set()
    return all(value is True for key, value in mapping.items() if key not in ignored)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT / "DRTP_TECHNICAL_VERIFICATION.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    OUT.mkdir(parents=True, exist_ok=True)
    sampler = sampler_checks()
    failure = failure_semantics_checks()
    architecture = architecture_and_boundary_checks()
    result = {
        "protocol": "DRTP-SG-MAPPO-TECHNICAL-VERIFICATION-V1",
        "training_started": False,
        "long_training_started": False,
        "canonical_seeds_used": False,
        "reserved_tapes_generated": False,
        "sampler": sampler,
        "failure_semantics": failure,
        "architecture_information_boundary": architecture,
        "information_boundary_regression": subprocess_check([sys.executable, "-m", "pytest", "-q", "tests/test_phase2h_information_boundary.py"]),
        "graph_legality": subprocess_check([sys.executable, "scripts/verify_phase_s2_graph_legality.py"]),
        "s2_logging_invariance": subprocess_check([sys.executable, "scripts/verify_phase_s2_logging_invariance.py", "--output", str(OUT / "s2_logging_invariance.json")]),
    }
    result["one_update_smoke"] = smoke_checks()
    result["all_checks_pass"] = (
        all_true(sampler, {"observed_utr_frequencies", "adaptive_q", "adaptive_difficulty", "boundary_rows"})
        and all_true(failure)
        and all_true(architecture, {"utr_parameter_count", "drtp_parameter_count"})
        and result["information_boundary_regression"]["pass"]
        and result["graph_legality"]["pass"]
        and result["s2_logging_invariance"]["pass"]
        and all_true(result["one_update_smoke"], {"utr", "drtp_logging_on", "drtp_logging_off", "long_training_started", "canonical_seeds_used", "reserved_tapes_generated"})
        and not result["one_update_smoke"]["long_training_started"]
        and not result["one_update_smoke"]["canonical_seeds_used"]
        and not result["one_update_smoke"]["reserved_tapes_generated"]
        and all_true(result["one_update_smoke"]["utr"], {"output", "mode", "seed", "sampler_manifest", "checkpoint_path"})
        and all_true(result["one_update_smoke"]["drtp_logging_on"], {"output", "mode", "seed", "sampler_manifest", "checkpoint_path"})
        and all_true(result["one_update_smoke"]["drtp_logging_off"], {"output", "mode", "seed", "sampler_manifest", "checkpoint_path"})
    )
    result["status"] = "PASS" if result["all_checks_pass"] else "NO-GO"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output)}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
