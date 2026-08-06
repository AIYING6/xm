# Structure-level assertions for the formal MAPPO v1.5 entrypoint.
# Pure functions / small fake objects only; does NOT start parallel envs.
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    effective_config_sha256,
    role_onehot,
    snapshot_nodes,
    strict_bc_load,
)


def make_agent(obs_dim=10, role_dim=4, share_obs_dim=20, action_dim=5, hidden=16) -> MAPPOAgent3D:
    return MAPPOAgent3D(obs_dim, role_dim, share_obs_dim, action_dim, hidden)


# ---- actor/critic dimensions ----
def test_actor_input_is_obs_plus_role_onehot() -> None:
    agent = make_agent(obs_dim=10, role_dim=4)
    obs = torch.randn(3, 10)
    role = torch.randn(3, 4)
    out = agent.actor(torch.cat([obs, role], dim=-1))
    assert out.shape == (3, 5)


def test_critic_input_matches_centralized_obs() -> None:
    agent = make_agent(share_obs_dim=20)
    share = torch.randn(3, 20)
    v = agent.critic(share)
    assert v.shape == (3, 1)


def test_get_action_value_shapes() -> None:
    agent = make_agent(obs_dim=10, role_dim=4, share_obs_dim=20, action_dim=5)
    actor_in = torch.randn(3, 14)
    share = torch.randn(3, 20)
    a, lp, ent, v = agent.get_action_and_value(actor_in, share)
    assert a.shape == (3,)
    assert lp.shape == (3,)
    assert ent.shape == (3,)
    assert v.shape == (3,)


# ---- role one-hot encoding ----
def test_role_onehot_encodes_roles() -> None:
    role = np.array([[0, 1, 2], [1, 2, 0]])
    oh = role_onehot(role, 4)
    assert oh.shape == (2, 3, 4)
    assert oh[0, 0].tolist() == [1, 0, 0, 0]
    assert oh[0, 1].tolist() == [0, 1, 0, 0]
    assert oh[0, 2].tolist() == [0, 0, 1, 0]
    assert oh[1, 2].tolist() == [1, 0, 0, 0]
    assert oh.sum(axis=-1).tolist() == [[1, 1, 1], [1, 1, 1]]


# ---- state dict contains no graph/gate/EA-RG modules ----
def test_state_dict_has_only_actor_critic_no_graph_modules() -> None:
    sd = make_agent().state_dict()
    banned = ("graph", "attention", "edge", "role_pair_gate", "task_support", "relation")
    for k in sd:
        kl = k.lower()
        for b in banned:
            assert b not in kl, f"unexpected key {k} contains '{b}'"
    # must have actor.* and critic.*
    assert any(k.startswith("actor.") for k in sd)
    assert any(k.startswith("critic.") for k in sd)
    assert not any(k.startswith("multi_relation") for k in sd)


# ---- strict BC load ----
def test_strict_bc_load_ok(tmp_path: Path) -> None:
    agent = make_agent()
    path = tmp_path / "bc.pt"
    torch.save({"model_state": agent.state_dict()}, path)
    sha = strict_bc_load(agent, str(path), torch.device("cpu"))
    assert len(sha) == 64


def test_strict_bc_load_missing_key_fails(tmp_path: Path) -> None:
    agent = make_agent()
    bad = {k: v for i, (k, v) in enumerate(agent.state_dict().items()) if i != 0}
    path = tmp_path / "bc_missing.pt"
    torch.save({"model_state": bad}, path)
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(agent, str(path), torch.device("cpu"))


def test_strict_bc_load_extra_key_fails(tmp_path: Path) -> None:
    agent = make_agent()
    extra = dict(agent.state_dict())
    extra["bogus.weight"] = torch.zeros(1, 1)
    path = tmp_path / "bc_extra.pt"
    torch.save({"model_state": extra}, path)
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(agent, str(path), torch.device("cpu"))


def test_strict_bc_load_shape_mismatch_fails(tmp_path: Path) -> None:
    agent = make_agent()
    bad = dict(agent.state_dict())
    first = next(iter(bad))
    bad[first] = torch.zeros(3, 3)
    path = tmp_path / "bc_shape.pt"
    torch.save({"model_state": bad}, path)
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(agent, str(path), torch.device("cpu"))


# ---- snapshot nodes ----
def test_snapshot_nodes_exact_set() -> None:
    nodes = snapshot_nodes(100, 977)
    assert nodes == [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]
    assert nodes[-1] == 977


# ---- effective config sha ----
def test_effective_config_sha_deterministic_and_sensitive() -> None:
    cfg1 = MAPPO3DConfig(env=MAPPO3DConfig.__dataclass_fields__["env"].default)  # placeholder
    # Build two distinct configs via a helper-free approach:
    import dataclasses
    from algorithms.ri_gmappo import RIGMAPPOConfig

    e1 = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=8, rollout_steps=128, updates=977, hidden_dim=64)
    e2 = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=8, rollout_steps=128, updates=977, hidden_dim=96)
    c1 = MAPPO3DConfig(env=e1)
    c2 = MAPPO3DConfig(env=e2)
    c1b = MAPPO3DConfig(env=e1)
    s1 = effective_config_sha256(c1)
    s1b = effective_config_sha256(c1b)
    s2 = effective_config_sha256(c2)
    assert s1 == s1b
    assert s1 != s2
