# BC semantics + integrity tests for the formal MAPPO v1.5 warm-start (②).
# Pure tensors / minimal MAPPO actor only; no parallel envs.
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pretrain_mappo_3d_bc import demo_fingerprint_sha256  # noqa: E402
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    effective_config_sha256,
    role_onehot,
    strict_bc_load,
)
from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402


def make_agent(obs_dim=34, role_dim=4, share_obs_dim=47, action_dim=27, hidden=64) -> MAPPOAgent3D:
    return MAPPOAgent3D(obs_dim, role_dim, share_obs_dim, action_dim, hidden)


def make_demo(n=32, num_agents=3, obs_dim=34, action_dim=27, num_roles=4, seed=0) -> dict:
    rng = np.random.default_rng(seed)
    return {
        "obs": rng.normal(size=(n, num_agents, obs_dim)).astype(np.float32),
        "role": np.tile(np.array([0, 1, 2]), (n, 1)),
        "action": rng.integers(0, action_dim, size=(n, num_agents)),
    }


def make_bc_payload(agent: MAPPOAgent3D, meta: dict | None = None) -> dict:
    return {
        "actor_state": agent.actor.state_dict(),
        "meta": meta
        or {
            "pretrained_modules": "actor",
            "obs_dim": agent.actor.net[0].in_features - agent.role_dim,
            "role_dim": agent.role_dim,
            "action_dim": agent.actor.net[-1].out_features,
            "hidden_dim": agent.actor.net[0].out_features,
        },
    }


# ---- data / input semantics ----
def test_demo_only_blue_agents() -> None:
    data = make_demo()
    assert data["obs"].shape[1] == 3
    assert data["role"].shape[1] == 3


def test_role_truncated_from_graph() -> None:
    graph_role = np.array([0, 1, 2, 4])  # 3 blue + red(target) role=4
    role = graph_role[:3]
    assert role.tolist() == [0, 1, 2]
    assert 4 not in role


def test_actor_input_is_obs_plus_role_onehot() -> None:
    agent = make_agent()
    data = make_demo()
    obs = torch.as_tensor(data["obs"][0].reshape(-1, data["obs"].shape[-1]))
    oh = role_onehot(data["role"][0].reshape(1, -1), agent.role_dim)[0]  # (3, role_dim)
    ro = torch.as_tensor(oh.reshape(-1, agent.role_dim))
    actor_in = torch.cat([obs, ro], dim=-1)
    assert actor_in.shape[-1] == agent.actor.net[0].in_features
    assert actor_in.shape[-1] == data["obs"].shape[-1] + agent.role_dim


def test_red_target_role_excluded() -> None:
    graph_role = np.array([0, 1, 2, 4])
    role = graph_role[:3]
    assert 4 not in role.tolist()
    oh = role_onehot(role.reshape(1, -1), 4)
    assert oh.shape == (1, 3, 4)
    # every blue agent has a valid one-hot of length 4 (no column beyond 3)
    assert int(oh.sum()) == 3


def test_action_shape_dtype_for_ce() -> None:
    data = make_demo()
    a = torch.as_tensor(data["action"].reshape(-1), dtype=torch.long)
    assert a.dtype == torch.long
    assert a.dim() == 1


def test_actor_output_matches_action_space() -> None:
    agent = make_agent(action_dim=27)
    assert agent.actor.net[-1].out_features == 27


# ---- actor-only BC semantics ----
def test_checkpoint_contains_only_actor_state() -> None:
    agent = make_agent()
    payload = make_bc_payload(agent)
    assert "actor_state" in payload
    assert all(k.startswith("net.") for k in payload["actor_state"])  # MLP submodule keys
    assert "critic" not in str(list(payload["actor_state"].keys()))


def test_pretrained_modules_marked_actor() -> None:
    payload = make_bc_payload(make_agent())
    assert payload["meta"]["pretrained_modules"] == "actor"


def test_strict_load_actor_matches_critic_unchanged(tmp_path: Path) -> None:
    agent = make_agent()
    payload = make_bc_payload(agent)
    p = tmp_path / "bc.pt"
    torch.save(payload, p)
    agent2 = make_agent()
    critic_before = {k: v.clone() for k, v in agent2.critic.state_dict().items()}
    strict_bc_load(agent2, str(p), torch.device("cpu"))
    # actor matches BC exactly
    for k, v in agent2.actor.state_dict().items():
        assert torch.equal(v, payload["actor_state"][k]), k
    # critic untouched
    for k, v in agent2.critic.state_dict().items():
        assert torch.equal(v, critic_before[k]), k


def test_strict_load_missing_actor_key_fails(tmp_path: Path) -> None:
    agent = make_agent()
    bad = {k: v for i, (k, v) in enumerate(agent.actor.state_dict().items()) if i != 0}
    torch.save({"actor_state": bad, "meta": make_bc_payload(agent)["meta"]}, tmp_path / "b.pt")
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(make_agent(), str(tmp_path / "b.pt"), torch.device("cpu"))


def test_strict_load_extra_actor_key_fails(tmp_path: Path) -> None:
    agent = make_agent()
    extra = dict(agent.actor.state_dict())
    extra["net.bogus"] = torch.zeros(1)
    torch.save({"actor_state": extra, "meta": make_bc_payload(agent)["meta"]}, tmp_path / "b.pt")
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(make_agent(), str(tmp_path / "b.pt"), torch.device("cpu"))


def test_strict_load_shape_mismatch_fails(tmp_path: Path) -> None:
    agent = make_agent()
    bad = dict(agent.actor.state_dict())
    first = next(iter(bad))
    bad[first] = torch.zeros(2, 2)
    torch.save({"actor_state": bad, "meta": make_bc_payload(agent)["meta"]}, tmp_path / "b.pt")
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(make_agent(), str(tmp_path / "b.pt"), torch.device("cpu"))


def test_meta_dim_mismatch_fails(tmp_path: Path) -> None:
    agent = make_agent()
    meta = make_bc_payload(agent)["meta"]
    meta = {**meta, "action_dim": meta["action_dim"] + 1}
    torch.save({"actor_state": agent.actor.state_dict(), "meta": meta}, tmp_path / "b.pt")
    with pytest.raises(RuntimeError, match="metadata dims mismatch"):
        strict_bc_load(make_agent(), str(tmp_path / "b.pt"), torch.device("cpu"))


def test_graph_gate_keys_rejected(tmp_path: Path) -> None:
    agent = make_agent()
    actor_state = dict(agent.actor.state_dict())
    actor_state["graph.attn.weight"] = torch.zeros(1, 1)
    torch.save({"actor_state": actor_state, "meta": make_bc_payload(agent)["meta"]}, tmp_path / "b.pt")
    with pytest.raises(RuntimeError, match="STRICT BC load FAILED"):
        strict_bc_load(make_agent(), str(tmp_path / "b.pt"), torch.device("cpu"))


# ---- training & reproducibility (small fixed data, no env) ----
def test_single_batch_loss_finite_and_bp_changes_actor() -> None:
    agent = make_agent()
    data = make_demo(n=16)
    opt = torch.optim.Adam(agent.actor.parameters(), lr=1e-3)
    loss_fn = torch.nn.CrossEntropyLoss()
    obs = torch.as_tensor(data["obs"].reshape(-1, data["obs"].shape[-1]), dtype=torch.float32)
    ro = torch.as_tensor(role_onehot(data["role"], agent.role_dim).reshape(-1, agent.role_dim), dtype=torch.float32)
    acts = torch.as_tensor(data["action"].reshape(-1), dtype=torch.long)
    before = {k: v.clone() for k, v in agent.actor.state_dict().items()}
    logits = agent.actor(torch.cat([obs, ro], dim=-1))
    loss = loss_fn(logits, acts)
    assert torch.isfinite(loss)
    opt.zero_grad()
    loss.backward()
    total_norm = torch.cat([p.grad.flatten() for p in agent.actor.parameters() if p.grad is not None]).norm()
    assert torch.isfinite(total_norm)
    opt.step()
    changed = any(not torch.equal(v, before[k]) for k, v in agent.actor.state_dict().items())
    assert changed


def test_loss_decreases_on_fixed_data() -> None:
    agent = make_agent()
    data = make_demo(n=64, seed=7)
    opt = torch.optim.Adam(agent.actor.parameters(), lr=5e-3)
    loss_fn = torch.nn.CrossEntropyLoss()
    obs = torch.as_tensor(data["obs"].reshape(-1, data["obs"].shape[-1]), dtype=torch.float32)
    ro = torch.as_tensor(role_onehot(data["role"], agent.role_dim).reshape(-1, agent.role_dim), dtype=torch.float32)
    acts = torch.as_tensor(data["action"].reshape(-1), dtype=torch.long)
    losses = []
    for _ in range(20):
        opt.zero_grad()
        loss = loss_fn(agent.actor(torch.cat([obs, ro], dim=-1)), acts)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    assert losses[-1] < losses[0] - 1e-3


def test_reproducible_same_seed_fixed_data() -> None:
    def run() -> list[float]:
        torch.manual_seed(0)
        np.random.seed(0)
        agent = make_agent()
        data = make_demo(n=32, seed=3)
        opt = torch.optim.Adam(agent.actor.parameters(), lr=1e-3)
        loss_fn = torch.nn.CrossEntropyLoss()
        obs = torch.as_tensor(data["obs"].reshape(-1, data["obs"].shape[-1]), dtype=torch.float32)
        ro = torch.as_tensor(role_onehot(data["role"], agent.role_dim).reshape(-1, agent.role_dim), dtype=torch.float32)
        acts = torch.as_tensor(data["action"].reshape(-1), dtype=torch.long)
        outs = []
        for _ in range(5):
            opt.zero_grad()
            loss = loss_fn(agent.actor(torch.cat([obs, ro], dim=-1)), acts)
            loss.backward()
            opt.step()
            outs.append(round(float(loss.item()), 8))
        return outs

    assert run() == run()


# ---- fingerprints / sha / round-trip ----
def test_demo_sha_deterministic_and_sensitive() -> None:
    d1 = make_demo(seed=1)
    d2 = make_demo(seed=1)
    d3 = make_demo(seed=2)
    assert demo_fingerprint_sha256(d1) == demo_fingerprint_sha256(d2)
    assert demo_fingerprint_sha256(d1) != demo_fingerprint_sha256(d3)


def test_effective_config_sha_deterministic() -> None:
    e = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=8, rollout_steps=128, updates=977, hidden_dim=64)
    c1 = MAPPO3DConfig(env=e)
    c2 = MAPPO3DConfig(env=e)
    assert effective_config_sha256(c1) == effective_config_sha256(c2)


def test_bc_checkpoint_roundtrip(tmp_path: Path) -> None:
    agent = make_agent()
    payload = make_bc_payload(agent)
    p = tmp_path / "mappo_bc_actor.pt"
    torch.save(payload, p)
    loaded = torch.load(p, map_location="cpu", weights_only=False)
    assert set(loaded["actor_state"].keys()) == set(agent.actor.state_dict().keys())
    assert loaded["meta"]["pretrained_modules"] == "actor"
    for k, v in loaded["actor_state"].items():
        assert torch.equal(v, agent.actor.state_dict()[k])
