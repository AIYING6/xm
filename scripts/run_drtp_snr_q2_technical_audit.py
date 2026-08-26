"""Technical-only audit for the frozen UTR/SNR/DRTP mechanism comparator.

The script uses short CPU trajectories with dedicated technical seeds.  It
never creates the prospective 500k tape or a 10M development/formal run.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS, DRTPSelection, DRTPTopologySampler, FAILURE_GROUPS, GROUP_MEMBERS, NOMINAL_GROUP, NOMINAL_MASS,
)
from algorithms.ri_gmappo.snr_topology_sampler import STATIC_NONUNIFORM_Q, StaticNonuniformTopologySampler  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent, RIGMAPPOConfig, load_runtime_training_checkpoint, make_env, train_ri_gmappo,
)


PROTOCOL = "DRTP-SNR-Q2-MECHANISM-COMPARATOR-TECHNICAL-AUDIT-V1"
TECHNICAL_SEEDS = {"utr": 99161, "snr": 99162, "drtp": 99163}


def cfg(mode: str, seed: int, out_dir: Path, updates: int, *, total_updates: int, logging: bool = True, **changes: Any) -> RIGMAPPOConfig:
    values = {
        "env_name": "3d_intercept", "seed": seed, "num_envs": 4, "rollout_steps": 64,
        "updates": updates, "hidden_dim": 115, "role_dim": 8, "intent_dim": 8,
        "graph_encoder": "single", "role_gate_mode": "none", "target_policy": "straight",
        "strict_target_sensing": True, "agent_target_info_bottleneck": True,
        "relay_dependent_task": True, "business_grounded_geometry": True,
        "communication_range_scale": 1.0, "communication_dropout_prob": 0.0,
        "message_delay_steps": 0, "radar_dropout_prob": 0.0, "min_success_step": 260,
        "failed_blue_agent": -1, "node_failure_start_step": 0, "node_failure_duration_steps": 0,
        "evaluation_enabled": False, "target_kl": None, "save_interval": 1, "save_snapshots": False,
        "out_dir": str(out_dir), "device": "cpu", "topology_curriculum_schedule": "none",
        "fixed_f0_probability": None, "drtp_sampler_mode": mode, "drtp_sampler_seed": seed,
        "drtp_sampler_logging": logging, "drtp_sampler_total_updates": total_updates,
        "runtime_state_checkpointing": True, "runtime_state_save_interval": 1,
    }
    values.update(changes)
    return RIGMAPPOConfig(**values)


def sampler_log_name(mode: str) -> str:
    return "snr_static_nonuniform_topology_sampler_log.csv" if mode == "snr" else "drtp_topology_sampler_log.csv"


def exact_equal(left: Any, right: Any, path: str = "root") -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and left.dtype == right.dtype and left.shape == right.shape, path
        assert torch.equal(left, right), path
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray) and left.dtype == right.dtype and left.shape == right.shape, path
        assert np.array_equal(left, right, equal_nan=True), path
    elif isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right), path
        for key in left: exact_equal(left[key], right[key], f"{path}.{key}")
    elif isinstance(left, (list, tuple)):
        assert isinstance(right, type(left)) and len(left) == len(right), path
        for index, (a, b) in enumerate(zip(left, right)): exact_equal(a, b, f"{path}[{index}]")
    else:
        assert left == right, path


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_sg(seed: int) -> RIGMAPPOAgent:
    probe = cfg("utr", seed, ROOT / "tmp" / "snr_parameter_probe", 1, total_updates=1, logging=False)
    env = make_env(probe, seed, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", use_intent_context=False,
    )


def sampler_checks() -> dict:
    snr = StaticNonuniformTopologySampler(99171, 39063)
    replay = StaticNonuniformTopologySampler(99171, 39063)
    coordinates = [(update, index % 4, index) for index, update in enumerate(range(0, 100000))]
    left = [asdict(snr.select(*item)) for item in coordinates]
    right = [asdict(replay.select(*item)) for item in coordinates]
    samples = [DRTPSelection(**item) for item in left]
    groups = {group: sum(item.group == group for item in samples) / len(samples) for group in ALL_GROUPS}
    members = {}
    for group in ALL_GROUPS:
        group_rows = [item for item in samples if item.group == group]
        members[group] = {member[0]: sum(item.condition == member[0] for item in group_rows) / len(group_rows) for member in GROUP_MEMBERS[group]}
    state = snr.state_dict(); restored = StaticNonuniformTopologySampler(99171, 39063); restored.load_state_dict(state)
    no_feedback_rejected = False
    try:
        snr.record_completed_return(samples[0], 1.0)
    except AssertionError:
        no_feedback_rejected = True
    return {
        "fixed_group_universe": tuple(GROUP_MEMBERS) == ALL_GROUPS and FAILURE_GROUPS == ("F0", "TE", "TL", "DS", "DL", "CP"),
        "fixed_nominal_anchor": NOMINAL_MASS == 0.50,
        "fixed_static_weights": snr.q == STATIC_NONUNIFORM_Q and math.isclose(sum(snr.q.values()), 1.0, abs_tol=1e-12),
        "conditional_weight_sampling": all(abs(groups[group] - (0.5 * STATIC_NONUNIFORM_Q[group])) < 0.005 for group in FAILURE_GROUPS),
        "nominal_weight_sampling": abs(groups["N"] - 0.50) < 0.005,
        "within_group_uniform_members": all(all(abs(value - 1 / len(GROUP_MEMBERS[group])) < 0.015 for value in frequencies.values()) for group, frequencies in members.items()),
        "deterministic_selection_replay": left == right,
        "sampler_state_roundtrip_exact": state == restored.state_dict(),
        "no_completed_return_feedback": no_feedback_rejected and snr.uses_completed_return_feedback is False,
        "no_ema_difficulty_or_update_state": state["ema_state"] is None and state["difficulty_state"] is None and state["adaptation_window"] is None and snr.maybe_update(32) is None,
        "observed_unconditional_frequencies": groups,
        "observed_member_frequencies": members,
    }


def config_and_boundary_checks() -> dict:
    configs = {mode: cfg(mode, TECHNICAL_SEEDS[mode], ROOT / "unused" / mode, 1, total_updates=1, logging=True)
               for mode in TECHNICAL_SEEDS}
    normalized = {mode: asdict(config) for mode, config in configs.items()}
    for data in normalized.values():
        for key in ("drtp_sampler_mode", "seed", "drtp_sampler_seed", "out_dir", "device"):
            data.pop(key, None)
    torch.manual_seed(99181); agents = {mode: build_sg(99181) for mode in TECHNICAL_SEEDS}
    counts = {mode: sum(parameter.numel() for parameter in agent.parameters() if parameter.requires_grad) for mode, agent in agents.items()}
    keys = {mode: set(agent.state_dict()) for mode, agent in agents.items()}
    snr_manifest = StaticNonuniformTopologySampler(99162, 1).manifest()
    return {
        "parameter_counts": counts,
        "matched_116728_parameters": all(count == 116728 for count in counts.values()),
        "same_non_sampler_config": len({json.dumps(item, sort_keys=True, default=str) for item in normalized.values()}) == 1,
        "identical_actor_critic_state_keys": len({tuple(sorted(value)) for value in keys.values()}) == 1,
        "single_graph_only": all(agent.actor.graph_encoder == "single" for agent in agents.values()),
        "sampler_outside_policy_parameters": all(not any(token in name.lower() for token in ("drtp", "snr", "sampler")) for agent in agents.values() for name, _ in agent.named_parameters()),
        "actor_boundary_declared": snr_manifest["actor_or_critic_condition_input"] is False,
    }


def subprocess_check(command: list[str]) -> dict:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {"pass": completed.returncode == 0, "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-1000:], "stderr_tail": completed.stderr[-1000:]}


def one_update(mode: str, root: Path, suffix: str, *, logging: bool) -> dict:
    out = root / suffix
    train_ri_gmappo(cfg(mode, TECHNICAL_SEEDS[mode], out, 1, total_updates=1, logging=logging))
    checkpoint = out / "actor_critic_latest.pt"
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    finite = all(torch.isfinite(value).all() for value in state.values() if isinstance(value, torch.Tensor))
    manifest_name = "snr_static_nonuniform_topology_sampler_manifest.json" if mode == "snr" else "drtp_topology_sampler_manifest.json"
    log = out / sampler_log_name(mode)
    return {
        "one_update_logged": len((out / "train_log.csv").read_text(encoding="utf-8").splitlines()) == 2,
        "finite_checkpoint": finite,
        "checkpoint_exists": checkpoint.exists(),
        "runtime_state_exists": (out / "actor_critic_runtime_state_latest.pt").exists(),
        "sampler_manifest_exists": (out / manifest_name).exists(),
        "sampler_log_semantics": (log.exists() and log.stat().st_size > 0) if logging else not log.exists(),
        "checkpoint": checkpoint,
    }


def continuation(mode: str, root: Path) -> bool:
    uninterrupted, segmented = root / f"{mode}_uninterrupted", root / f"{mode}_segmented"
    train_ri_gmappo(cfg(mode, TECHNICAL_SEEDS[mode], uninterrupted, 2, total_updates=2, logging=True))
    train_ri_gmappo(cfg(mode, TECHNICAL_SEEDS[mode], segmented, 1, total_updates=2, logging=True))
    boundary = segmented / "actor_critic_runtime_state_latest.pt"
    train_ri_gmappo(cfg(mode, TECHNICAL_SEEDS[mode], segmented, 1, total_updates=2, logging=True,
                       update_offset=1, append_log=True, runtime_state_resume=str(boundary)))
    left = load_runtime_training_checkpoint(uninterrupted / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    right = load_runtime_training_checkpoint(segmented / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    exact_equal(left, right)
    exact_equal(csv_rows(uninterrupted / "train_log.csv"), csv_rows(segmented / "train_log.csv"))
    exact_equal(csv_rows(uninterrupted / sampler_log_name(mode)), csv_rows(segmented / sampler_log_name(mode)))
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, default=ROOT / "docs" / "DRTP_SNR_Q2_IMPLEMENTATION_AUDIT.md")
    args = parser.parse_args()
    root = args.output_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite technical output: {root}")
    root.mkdir(parents=True, exist_ok=False)
    sampler, boundary = sampler_checks(), config_and_boundary_checks()
    smoke = {mode: one_update(mode, root, f"{mode}_one_update", logging=True) for mode in TECHNICAL_SEEDS}
    log_on = one_update("snr", root, "snr_logging_on", logging=True)
    log_off = one_update("snr", root, "snr_logging_off", logging=False)
    on_state = torch.load(log_on["checkpoint"], map_location="cpu", weights_only=True)
    off_state = torch.load(log_off["checkpoint"], map_location="cpu", weights_only=True)
    continuation_checks = {mode: continuation(mode, root) for mode in TECHNICAL_SEEDS}
    result = {
        "protocol": PROTOCOL, "long_training_started": False, "new_evaluation_tape_generated": False,
        "canonical_seeds_used": False, "sampler": sampler, "config_boundary": boundary,
        "information_boundary_regression": subprocess_check([sys.executable, "-m", "pytest", "-q", "tests/test_phase2h_information_boundary.py"]),
        "graph_legality_regression": subprocess_check([sys.executable, "scripts/verify_phase_s2_graph_legality.py"]),
        "one_update_finite_value_smoke": {mode: {key: value for key, value in item.items() if key != "checkpoint"} for mode, item in smoke.items()},
        "logging_invariance": set(on_state) == set(off_state) and all(torch.equal(on_state[key], off_state[key]) for key in on_state),
        "runtime_save_reload_next_update_exact": continuation_checks,
    }
    scalar_sampler = {key: value for key, value in sampler.items() if isinstance(value, bool)}
    scalar_boundary = {key: value for key, value in boundary.items() if isinstance(value, bool)}
    smoke_pass = all(all(value for key, value in item.items() if key != "checkpoint") for item in smoke.values())
    result["all_checks_pass"] = (
        all(scalar_sampler.values()) and all(scalar_boundary.values())
        and result["information_boundary_regression"]["pass"] and result["graph_legality_regression"]["pass"]
        and smoke_pass and result["logging_invariance"] and all(continuation_checks.values())
    )
    result["status"] = "PASS" if result["all_checks_pass"] else "FAIL"
    (root / "DRTP_SNR_Q2_TECHNICAL_AUDIT.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    lines = ["# DRTP/SNR Q2 Implementation Audit", "", f"**Status:** `{result['status']}`", "",
             "This audit uses dedicated CPU technical seeds and short one/two-update trajectories only. It creates neither the prospective 500000–500099 evaluation tape nor any 10M comparator trajectory.", "",
             "## Required checks", ""]
    for name, passed in {**scalar_sampler, **scalar_boundary, "information_boundary_regression": result["information_boundary_regression"]["pass"], "graph_legality_regression": result["graph_legality_regression"]["pass"], "logging_invariance": result["logging_invariance"], **{f"runtime_exact_{key}": value for key, value in continuation_checks.items()}}.items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines += ["", "SNR samples only the frozen static conditional weights (F0 0.15, TE 0.20, TL 0.10, DS 0.10, DL 0.20, CP 0.25) under the fixed 50% nominal anchor. It carries no return-feedback, EMA, difficulty, or weight-update state.", ""]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(root / "DRTP_SNR_Q2_TECHNICAL_AUDIT.json"), "report": str(args.report_path)}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
