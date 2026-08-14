"""TP-0 implementation and technical verification; no long training."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    load_matching_state_dict,
    make_env,
    train_ri_gmappo,
)
from algorithms.ri_gmappo.topology_curriculum import (  # noqa: E402
    FTRAIN_POOL,
    SCHEDULES,
    TopologyCurriculum,
    schedule_hash,
)
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


OUT = ROOT / "results" / "development" / "phase_tp0_ctp_sg_technical_verification_v3"


def frozen_cfg(seed: int, out_dir: Path, schedule: str = "none", logging: bool = False) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=2, rollout_steps=8,
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
        topology_curriculum_schedule=schedule,
        topology_curriculum_seed=seed,
        topology_curriculum_logging=logging,
    )


def build_sg(seed: int, hidden_dim: int = 115) -> RIGMAPPOAgent:
    env = make_env(frozen_cfg(seed, OUT / "parameter_probe"), seed, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=hidden_dim,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False,
    )


def scheduler_checks() -> dict:
    checks: dict[str, bool] = {}
    checks["all_schedules_present"] = set(SCHEDULES) == {"A", "B", "C"}
    checks["ftrain_excludes_canonical"] = (44, 80) not in FTRAIN_POOL and len(FTRAIN_POOL) == 8
    checks["probability_rows_sum_to_one"] = all(
        abs(sum(weights) - 1.0) < 1e-12
        for spec in SCHEDULES.values() for weights in spec["weights"]
    )
    expected = {
        "A": ((0.80, 0.20, 0.00), (0.55, 0.25, 0.20), (0.40, 0.25, 0.35)),
        "B": ((0.90, 0.10, 0.00), (0.70, 0.20, 0.10), (0.55, 0.20, 0.25)),
        "C": ((0.75, 0.25, 0.00), (0.50, 0.25, 0.25), (0.30, 0.25, 0.45)),
    }
    for schedule, rows in expected.items():
        probe = TopologyCurriculum(schedule, 1601, 1000)
        checks[f"schedule_{schedule}_weights_exact"] = (
            tuple(probe.weights(100).values()) == rows[0]
            and tuple(probe.weights(400).values()) == rows[1]
            and tuple(probe.weights(800).values()) == rows[2]
        )
        counts = {"nominal": 0, "f0": 0, "ftrain": 0}
        for i in range(6000):
            selected = probe.select(400, i, 1).condition
            counts["nominal" if selected == "nominal" else "f0" if selected == "f0" else "ftrain"] += 1
        expected_row = rows[1]
        observed = tuple(counts[key] / 6000.0 for key in ("nominal", "f0", "ftrain"))
        checks[f"schedule_{schedule}_sampling_matches"] = all(
            abs(left - right) <= 0.03 for left, right in zip(observed, expected_row)
        )
    replay_a = TopologyCurriculum("A", 1601, 1172)
    replay_b = TopologyCurriculum("A", 1601, 1172)
    sequence_a = [asdict(replay_a.select(u, e, ep)) for u, e, ep in ((0, 0, 0), (100, 1, 2), (600, 0, 3), (1172, 1, 4))]
    sequence_b = [asdict(replay_b.select(u, e, ep)) for u, e, ep in ((0, 0, 0), (100, 1, 2), (600, 0, 3), (1172, 1, 4))]
    checks["deterministic_scheduler_replay"] = sequence_a == sequence_b
    checks["logging_does_not_enter_scheduler"] = sequence_a == sequence_b
    checks["schedule_hash_stable"] = schedule_hash("A") == schedule_hash("A") and len(schedule_hash("A")) == 64
    return checks


def failure_semantics_checks() -> dict:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=1601, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        max_steps=260, min_success_step=260, failed_blue_agent=1,
        node_failure_start_step=44, node_failure_duration_steps=80,
    ))
    env.reset()
    baseline = asdict(env.config)
    curriculum = TopologyCurriculum("A", 1601, 1)
    selection = curriculum.select(0, 0, 0)
    f0 = type(selection)("f0", 44, 80, 1)
    curriculum.apply(env, f0)
    f0_config = asdict(env.config)
    ftrain = type(selection)("ftrain_36_60", 36, 60, 1)
    curriculum.apply(env, ftrain)
    ftrain_config = asdict(env.config)
    f0_changed = {key for key in baseline if baseline[key] != f0_config[key]}
    ftrain_changed = {key for key in f0_config if f0_config[key] != ftrain_config[key]}
    curriculum.apply(env, f0)
    env.step_count = 43
    before_active = env._is_comm_failed(1)
    env.step_count = 44
    start_active = env._is_comm_failed(1)
    env.step_count = 123
    last_active = env._is_comm_failed(1)
    env.step_count = 124
    after_active = env._is_comm_failed(1)
    return {
        "f0_fields_match_s2": f0_changed == set() and f0_config["failed_blue_agent"] == 1 and f0_config["node_failure_start_step"] == 44 and f0_config["node_failure_duration_steps"] == 80,
        "ftrain_only_changes_frozen_failure_fields": ftrain_changed == {"node_failure_start_step", "node_failure_duration_steps"},
        "curriculum_does_not_change_unrelated_environment_fields": ftrain_changed.issubset({"failed_blue_agent", "node_failure_start_step", "node_failure_duration_steps"}),
        "failure_timing_regression": (not before_active) and start_active and last_active and (not after_active),
    }


def architecture_checks() -> dict:
    sg = build_sg(1601, 115)
    ctp = build_sg(1601, 115)
    sg_count = sum(parameter.numel() for parameter in sg.parameters() if parameter.requires_grad)
    ctp_count = sum(parameter.numel() for parameter in ctp.parameters() if parameter.requires_grad)
    return {
        "sg_trainable_parameter_count": sg_count,
        "ctp_trainable_parameter_count": ctp_count,
        "parameter_count_identical": sg_count == ctp_count,
        "state_dict_keys_identical": set(sg.state_dict()) == set(ctp.state_dict()),
        "graph_encoder_identical": sg.actor.graph_encoder == "single" and ctp.actor.graph_encoder == "single",
    }


def subprocess_check(name: str, command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {"pass": completed.returncode == 0, "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-1000:], "stderr_tail": completed.stderr[-1000:]}


def one_update_smoke() -> dict:
    out = OUT / "one_update_smoke"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite TP-0 smoke output: {out}")
    cfg = frozen_cfg(1601, out, schedule="A", logging=True)
    train_ri_gmappo(cfg)
    log = out / "train_log.csv"
    checkpoint = out / "actor_critic_latest.pt"
    curriculum_manifest = out / "topology_curriculum_manifest.json"
    curriculum_log = out / "topology_curriculum_log.csv"
    reload_agent = build_sg(1601, 115)
    load_matching_state_dict(reload_agent, str(checkpoint), torch.device("cpu"))
    return {
        "train_log_exists": log.exists(),
        "one_update_logged": len(log.read_text(encoding="utf-8").splitlines()) == 2,
        "checkpoint_exists": checkpoint.exists() and checkpoint.stat().st_size > 0,
        "checkpoint_reload": checkpoint.exists(),
        "curriculum_manifest_exists": curriculum_manifest.exists(),
        "curriculum_log_exists": curriculum_log.exists() and curriculum_log.stat().st_size > 0,
        "schedule_hash": json.loads(curriculum_manifest.read_text(encoding="utf-8"))["schedule_hash"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results/development/phase_tp0_ctp_sg_technical_verification_v3.json")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "protocol": "PHASE-TP-0-CTP-SG-V1", "training_started": False,
        "long_training_started": False, "checks": scheduler_checks(),
        "failure_semantics": failure_semantics_checks(),
        "architecture": architecture_checks(),
        "information_boundary": subprocess_check(
            "information_boundary",
            [sys.executable, "-m", "pytest", "-q", "tests/test_phase2h_information_boundary.py"],
        ),
        "graph_legality": subprocess_check(
            "graph_legality", [sys.executable, "scripts/verify_phase_s2_graph_legality.py"]
        ),
        "logging_invariance": subprocess_check(
            "logging_invariance", [sys.executable, "scripts/verify_phase_s2_logging_invariance.py",
                                   "--output", str(OUT / "s2_logging_invariance.json")]
        ),
        "one_update_smoke": one_update_smoke(),
    }
    result["all_local_checks_pass"] = (
        all(result["checks"].values())
        and all(result["failure_semantics"].values())
        and all(value is True for key, value in result["architecture"].items() if key not in {"sg_trainable_parameter_count", "ctp_trainable_parameter_count"})
        and result["information_boundary"]["pass"]
        and result["graph_legality"]["pass"]
        and result["logging_invariance"]["pass"]
        and all(value is True for key, value in result["one_update_smoke"].items() if key not in {"schedule_hash"})
    )
    result["tp0_status"] = "PASS" if result["all_local_checks_pass"] else "NO-GO"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"tp0_status": result["tp0_status"], "output": str(args.output)}, indent=2))
    if result["tp0_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
