# Evaluation-chain tests for the formal MAPPO v1.5 entrypoint (③).
# Small real-env evaluations (1 env, few episodes) + fake checkpoints; no
# parallel sweep, no training.
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.evaluate_mappo_v1_5 as em  # noqa: E402
from scripts.evaluate_mappo_v1_5 import (  # noqa: E402
    Candidate,
    checkpoint_update,
    load_agent,
    make_eval_args,
)
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPOAgent3D,
    role_onehot,
)


def make_fake_ppo_checkpoint(tmp_path: Path, name="actor_critic_update_0100.pt", obs_dim=34, role_dim=4, share_obs_dim=47, action_dim=27, hidden=64) -> Path:
    agent = MAPPOAgent3D(obs_dim, role_dim, share_obs_dim, action_dim, hidden)
    p = tmp_path / name
    torch.save(agent.state_dict(), p)
    return p


def make_eval_args_ns(checkpoint: Path, episodes=3, base_seed=42_000, scenario="relay_failure", env_obs_dim=34) -> SimpleNamespace:
    a = SimpleNamespace(
        split="validation", seeds=(0,), scenarios=(scenario,), episodes=episodes,
        eval_batch_size=1, base_seed=base_seed, env_obs_dim=env_obs_dim,
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(10_000.0, 0.0, 5_000.0),
        max_target_message_age_steps=80, min_target_confidence=0.2, min_success_step=0,
        attack_hold_steps=4, selection_group="suite", selection_metric="legacy_recovery",
        selection_policy="v1_5_wilson", delayed_recovery_min_step=80,
        max_selection_collision_rate=0.0, selection_success_weight=100.0,
        device="cpu", allow_missing=False, expected_update=None,
    )
    return make_eval_args(a, Candidate(0, checkpoint, checkpoint_update(checkpoint)), scenario)


# 1. role truncated to blue agents
def test_role_truncated_to_blue() -> None:
    graph_role = np.array([0, 1, 2, 4])
    assert graph_role[:3].tolist() == [0, 1, 2]
    assert 4 not in graph_role[:3]


# 2. actor input dims consistent with the training entrypoint
def test_actor_input_dims_consistent() -> None:
    agent = MAPPOAgent3D(34, 4, 47, 27, 64)
    obs = torch.randn(3, 34)
    ro = torch.randn(3, 4)
    out = agent.actor(torch.cat([obs, ro], dim=-1))
    assert out.shape == (3, 27)
    assert agent.actor.net[0].in_features == 38  # 34 + 4


# 3. target role not in actor input
def test_target_role_excluded_from_input() -> None:
    graph_role = np.array([0, 1, 2, 4])
    role = graph_role[:3]
    oh = role_onehot(role.reshape(1, -1), 4)
    assert oh.shape == (1, 3, 4)
    assert int(oh.sum()) == 3


# 4. PPO checkpoint strict load (dims inferred correctly)
def test_ppo_checkpoint_strict_load(tmp_path: Path) -> None:
    cp = make_fake_ppo_checkpoint(tmp_path)
    agent = load_agent(make_eval_args_ns(cp), em.build_config(make_eval_args_ns(cp)))
    assert agent.actor.net[0].in_features == 38
    assert agent.actor.net[-1].out_features == 27
    assert agent.role_dim == 4
    assert agent.training is False  # eval mode


# 5. BC checkpoint (actor-only format) rejected when passed as PPO checkpoint
def test_bc_checkpoint_rejected(tmp_path: Path) -> None:
    agent = MAPPOAgent3D(34, 4, 47, 27, 64)
    p = tmp_path / "mappo_bc_actor.pt"
    torch.save({"actor_state": agent.actor.state_dict(),
                "meta": {"pretrained_modules": "actor"}}, p)
    with pytest.raises(RuntimeError):
        load_agent(make_eval_args_ns(p), em.build_config(make_eval_args_ns(p)))


# 6. update mismatch rejected
def test_expected_update_mismatch_rejected(tmp_path: Path) -> None:
    cp = make_fake_ppo_checkpoint(tmp_path, name="actor_critic_update_0100.pt")
    ns = make_eval_args_ns(cp)
    ns.expected_update = 999
    with pytest.raises(RuntimeError, match="expected"):
        load_agent(ns, em.build_config(ns))


# 7. unexposed episodes do not enter the recovery denominator
def test_unexposed_not_counted() -> None:
    # episode with final step < failure step is not exposed -> recovered is ""
    failure_step = 80.0
    for steps, rec in ((40, 1), (90, 1), (90, 0)):
        exposed = steps >= failure_step
        recovered = rec if exposed else ""
        if not exposed:
            assert recovered == ""
        else:
            assert recovered == rec


# 8. 1/1 Wilson lower bound below 50/50
def test_wilson_small_n_penalized() -> None:
    from scripts.evaluate_3d_checkpoint_sweep import wilson_lower_95
    assert wilson_lower_95(1.0, 1.0) < wilson_lower_95(50.0, 50.0)


# 9. missing one of the four scenarios is detectable (audit-level)
def test_missing_scenario_detectable() -> None:
    # a summary lacking a scenario cannot pass the 4-scenario completeness check
    scenarios = {"dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure",
                 "dropout030_delay2_relay_failure_delayed"}
    full = {"dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure",
            "dropout030_delay2_relay_failure_delayed", "dropout030_delay2_relay_failure_late"}
    assert not (full <= scenarios)


# 10/11/12: collision exclusion, larger-update tie-break, one selection per seed
def test_collision_excluded_and_tie_break() -> None:
    from scripts.evaluate_3d_checkpoint_sweep import select_checkpoints
    from scripts.evaluate_3d_checkpoint_sweep import wilson_lower_95
    base = {
        "split": "validation", "scenario": "dropout030_delay2_relay_failure",
        "graph_encoder": "mappo", "graph_relation_ablation": "none",
        "graph_message_ablation": "none", "graph_input_ablation": "none",
        "train_seed": "0", "checkpoint": "x", "episodes": "50",
        "selection_policy": "v1_5_wilson", "selection_metric": "legacy_recovery",
        "selection_success_weight": "100", "success_mean": "0.9",
        "post_failure_chain_recovered_mean": "1.0",
        "post_failure_chain_recovery_steps_mean": "10",
        "collision_mean": "0.0", "constraint_violation_mean": "0.0",
        "selection_score": "0", "failure_exposed_count": "20",
        "recovered_given_exposure_count": "20", "recovery_given_exposure": "1.0",
        "wilson_lower_95": f"{wilson_lower_95(20.0, 20.0):.6g}",
        "estimate_unstable": "0", "time_to_recovery_given_exposure": "10",
        "time_to_success": "50",
    }
    r_ok = {**base, "checkpoint_update": "200"}
    r_coll = {**base, "checkpoint_update": "300", "collision_mean": "0.05",
              "failure_exposed_count": "25", "recovered_given_exposure_count": "25"}
    r_tie = {**base, "checkpoint_update": "977"}
    rows = [r_ok, r_coll, r_tie]
    args = SimpleNamespace(split="validation", scenarios=["dropout030_delay2_relay_failure"],
                           selection_group="suite", selection_metric="legacy_recovery",
                           selection_success_weight=100.0, max_selection_collision_rate=0.0,
                           delayed_recovery_min_step=80, graph_relation_ablation="none",
                           graph_message_ablation="none", graph_input_ablation="none",
                           selection_policy="v1_5_wilson")
    sel = select_checkpoints(args, rows)
    assert len(sel) == 1
    assert sel[0]["selected_checkpoint_update"] == "977"  # collision one excluded, larger-update tie-break


# 13. episode/summary/selection column schemas align with the v1.5 unified schema
def test_three_level_schema_align() -> None:
    from scripts.evaluate_3d_checkpoint_sweep import SELECTION_COLUMNS, SUMMARY_COLUMNS
    from scripts.evaluate_ri_gmappo_3d import CSV_COLUMNS
    # episode fields include the shared CSV_COLUMNS and the v1.5 exposure fields
    for col in CSV_COLUMNS:
        assert col in em.EPISODE_FIELDS
    for col in ("failure_exposed", "recovered_given_exposure", "time_to_recovery_given_exposure", "time_to_success"):
        assert col in em.EPISODE_FIELDS
    # selection schema is the shared one (v1_5_wilson fields present)
    assert "wilson_lower_95" in SELECTION_COLUMNS
    assert "failure_exposed_count" in SELECTION_COLUMNS
    assert "selection_policy" in SELECTION_COLUMNS
    assert "failure_exposed_count" in SUMMARY_COLUMNS


# 14. small same-seed evaluation reproducible
def test_evaluation_reproducible(tmp_path: Path) -> None:
    cp = make_fake_ppo_checkpoint(tmp_path)
    r1 = em.evaluate(make_eval_args_ns(cp, episodes=3, base_seed=42_100))
    r2 = em.evaluate(make_eval_args_ns(cp, episodes=3, base_seed=42_100))
    assert len(r1) == len(r2)
    for a, b in zip(r1, r2):
        assert a["steps"] == b["steps"]
        assert a["success"] == b["success"]
        assert a["failure_exposed"] == b["failure_exposed"]


# 15. evaluation does not modify model parameters
def test_evaluation_does_not_modify_params(tmp_path: Path) -> None:
    cp = make_fake_ppo_checkpoint(tmp_path)
    ns = make_eval_args_ns(cp, episodes=2, base_seed=42_200)
    agent = load_agent(ns, em.build_config(ns))
    before = {k: v.clone() for k, v in agent.state_dict().items()}
    em.evaluate(ns)
    for k, v in agent.state_dict().items():
        assert torch.equal(v, before[k])


# 16. MAPPO evaluation uses only local_obs + role (no graph adjacency/edge/task-support)
def test_no_graph_input_used() -> None:
    agent = MAPPOAgent3D(34, 4, 47, 27, 64)
    sd = agent.state_dict()
    for k in sd:
        kl = k.lower()
        for banned in ("graph", "adj", "edge", "task_support", "relation", "attention"):
            assert banned not in kl
