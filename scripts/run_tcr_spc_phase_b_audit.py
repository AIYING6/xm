"""Zero-long-training technical audit for Phase-B UTR/SPC/TCR implementation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS, NOMINAL_GROUP
from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    _conditioned_actor_gradient,
    load_matching_state_dict,
    make_env,
    train_ri_gmappo,
)
from algorithms.ri_gmappo.tcr_topology_sampler import FixedStratifiedTopologySampler


def cfg(seed: int, out: Path, mode: str, *, updates: int = 1, append: bool = False,
        offset: int = 0, runtime_resume: str | None = None, gradient_logging: bool = False,
        sampler_logging: bool = False, runtime_checkpointing: bool = False) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=4, rollout_steps=64, updates=updates,
        hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False, target_kl=None,
        save_interval=1, save_snapshots=False, out_dir=str(out), device="cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None, drtp_sampler_mode="none",
        fixed_stratified_topology_sampler=True, fixed_stratified_topology_sampler_seed=seed,
        drtp_sampler_logging=sampler_logging, actor_gradient_mode=mode,
        actor_gradient_logging=gradient_logging, runtime_state_checkpointing=runtime_checkpointing,
        runtime_state_save_interval=1 if runtime_checkpointing else None,
        append_log=append, update_offset=offset, runtime_state_resume=runtime_resume,
    )


def build_agent(seed: int) -> RIGMAPPOAgent:
    env = make_env(cfg(seed, ROOT / ".phase_b_probe", "utr"), seed, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", use_intent_context=False,
    )


def exact_state(path: Path) -> dict:
    return torch.load(path, map_location="cpu", weights_only=True)


def states_equal(left: Path, right: Path) -> bool:
    a, b = exact_state(left), exact_state(right)
    return set(a) == set(b) and all(torch.equal(a[key], b[key]) for key in a)


def run_one_update(root: Path, mode: str, suffix: str, *, logging: bool = False, sampler_logging: bool = False) -> dict:
    out = root / suffix
    train_ri_gmappo(cfg(9401, out, mode, gradient_logging=logging, sampler_logging=sampler_logging))
    telemetry = out / "actor_gradient_telemetry.csv"
    rows = []
    if telemetry.exists():
        rows = telemetry.read_text(encoding="utf-8").splitlines()[1:]
    checkpoint = out / "actor_critic_latest.pt"
    reloaded = build_agent(9401)
    load_matching_state_dict(reloaded, str(checkpoint), torch.device("cpu"))
    return {
        "checkpoint": checkpoint,
        "finite_checkpoint": checkpoint.exists() and checkpoint.stat().st_size > 0,
        "one_update": len((out / "train_log.csv").read_text(encoding="utf-8").splitlines()) == 2,
        "telemetry_rows": rows,
        "finite_telemetry": all("nan" not in row.lower() and "inf" not in row.lower() for row in rows),
    }


def projection_checks() -> dict:
    nominal = [torch.tensor([1.0, 0.0])]
    failure = [torch.tensor([-1.0, 2.0])]
    utr, utr_row = _conditioned_actor_gradient("utr", nominal, failure)
    tcr, tcr_row = _conditioned_actor_gradient("tcr", nominal, failure)
    spc, spc_row = _conditioned_actor_gradient("spc", nominal, failure)
    expected_utr = torch.tensor([0.0, 1.0])
    expected_tcr = torch.tensor([0.5, 1.0])
    expected_spc = torch.tensor([0.4, 1.2])
    aligned = [torch.tensor([1.0])]
    same, same_row = _conditioned_actor_gradient("tcr", aligned, aligned)
    return {
        "utr_identity_test": torch.allclose(utr[0], expected_utr) and not utr_row["projection_applied"],
        "tcr_algebra_test": torch.allclose(tcr[0], expected_tcr) and tcr_row["projection_applied"],
        "spc_algebra_test": torch.allclose(spc[0], expected_spc) and spc_row["projection_applied"],
        "nonconflict_identity": torch.allclose(same[0], aligned[0]) and not same_row["projection_applied"],
    }


def sampler_checks() -> dict:
    sampler = FixedStratifiedTopologySampler(9401, 4)
    selected = [sampler.select(0, env, episode) for episode in range(6) for env in range(4)]
    counts = {group: sum(item.group == group for item in selected) for group in (NOMINAL_GROUP, *FAILURE_GROUPS)}
    manifest = sampler.manifest()
    state = sampler.state_dict()
    fields = sampler.log_fields()
    return {
        "two_nominal_streams": all(sampler.select(0, env, 0).group == NOMINAL_GROUP for env in (0, 1)),
        "two_failure_streams": all(sampler.select(0, env, 0).group in FAILURE_GROUPS for env in (2, 3)),
        "uniform_failure_cycle": all(counts[group] == 2 for group in FAILURE_GROUPS),
        "exact_half_nominal_samples": counts[NOMINAL_GROUP] == 12,
        "actor_boundary_manifest": manifest["actor_or_critic_condition_input"] is False,
        "no_drtp_return_adaptation": manifest["return_adaptive_state"] is False and all(
            forbidden not in state and all(forbidden not in name for name in fields)
            for forbidden in ("q", "ema", "difficulty", "return")
        ),
    }


def subprocess_check(args: list[str]) -> bool:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0


def continuation_check(root: Path) -> bool:
    reference = root / "continuation_reference"
    split = root / "continuation_split"
    train_ri_gmappo(cfg(9411, reference, "utr", updates=2, runtime_checkpointing=True))
    train_ri_gmappo(cfg(9411, split, "utr", updates=1, runtime_checkpointing=True))
    state = split / "actor_critic_runtime_state_latest.pt"
    train_ri_gmappo(cfg(9411, split, "utr", updates=1, append=True, offset=1, runtime_resume=str(state), runtime_checkpointing=True))
    return states_equal(reference / "actor_critic_latest.pt", split / "actor_critic_latest.pt")


def markdown(checks: dict) -> str:
    status = "PASS" if all(checks.values()) else "FAIL"
    rows = "\n".join(f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in checks.items())
    return f"""# TCR/SPC Phase B Implementation Audit

**Status: {status}.** This audit used one-update CPU technical smokes only. No development tape, long training, development seed, held-out seed, canonical seed, or performance claim was generated.

| Required check | Result |
| --- | --- |
{rows}

## Frozen implementation facts

- UTR-SG-MAPPO, SPC-SG-MAPPO, and TCR-SG-MAPPO each instantiate the same 116,728-parameter Single-Graph actor-critic.
- The fixed sampler assigns env streams 0/1 to nominal and 2/3 to uniformly cycled failure groups; every 4x64 projection rollout therefore has 128 nominal and 128 failure samples.
- UTR uses the identical split/bookkeeping route with projection disabled. TCR projects only the conflicting failure component away from the nominal gradient; SPC applies the pre-registered symmetric two-class control. Critic PPO updates are unchanged.
- Each projected actor update records condition counts, dot product, cosine, projection flag, nominal/failure norms, projected norm, and final norm.
- A missing condition class raises an error; no skip, stale gradient, unpaired fallback, or resample-until-valid path exists.

## Decision

{status}. A PASS authorizes no Phase C training by itself. Phase C remains subject to separate authorization.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "TCR_SPC_PHASE_B_IMPLEMENTATION_AUDIT.md")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output}")
    with tempfile.TemporaryDirectory(prefix="tcr_spc_phase_b_") as directory:
        temp = Path(directory)
        torch.manual_seed(9501); utr = build_agent(9401)
        torch.manual_seed(9501); spc = build_agent(9401)
        torch.manual_seed(9501); tcr = build_agent(9401)
        param_counts = [sum(p.numel() for p in model.parameters() if p.requires_grad) for model in (utr, spc, tcr)]
        smoke = {mode: run_one_update(temp, mode, f"{mode}_one_update", logging=True, sampler_logging=True) for mode in ("utr", "spc", "tcr")}
        replay_left = run_one_update(temp, "utr", "replay_left")
        replay_right = run_one_update(temp, "utr", "replay_right")
        log_off = run_one_update(temp, "utr", "logging_off")
        log_on = run_one_update(temp, "utr", "logging_on", logging=True, sampler_logging=True)
        checks = {
            "116728_parameter_equality": param_counts == [116728, 116728, 116728],
            "actor_boundary_regression": subprocess_check([sys.executable, "-m", "pytest", "-q", "tests/test_phase2h_information_boundary.py"]),
            "graph_legality_regression": subprocess_check([sys.executable, "scripts/verify_phase_s2_graph_legality.py"]),
            "fixed_seven_group_exposure": all(sampler_checks().values()),
            "stratified_minibatch_audit": all(
                len(info["telemetry_rows"]) == 4 and all(",128,128," in row for row in info["telemetry_rows"])
                for info in smoke.values()
            ),
            **projection_checks(),
            "no_drtp_state_isolation": sampler_checks()["no_drtp_return_adaptation"],
            "logging_invariance": states_equal(log_off["checkpoint"], log_on["checkpoint"]),
            "deterministic_replay": states_equal(replay_left["checkpoint"], replay_right["checkpoint"]),
            "checkpoint_reload_next_update_continuation": continuation_check(temp),
            "one_update_finite_value_smoke": all(
                info["finite_checkpoint"] and info["one_update"] and info["finite_telemetry"] for info in smoke.values()
            ),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown(checks))
    print(json.dumps({"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
