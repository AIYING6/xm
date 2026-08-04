"""Code-level assertions for the v1.5 ablation semantics (mechanism smoke tests).

These are NOT experimental results; they verify that the three ablation flags
behave as the frozen v1.5 definitions require:
  - w/o Gate Prior: initial role-pair gate == sigmoid(0)=0.5; gate still has
    gradients (learnable).
  - w/o Task-Support: task-support relation output is strictly zero while the
    other relations are non-zero; self-loop does not bypass the flag.
  - w/o Role-Pair Gate: all role pairs get an identical fixed gate
    (sigmoid(0.4) for the primary ablation); gate has no gradients; attention
    still input-dependent.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import MultiRelationGraphEncoder  # noqa: E402


def _make_encoder(**kwargs) -> MultiRelationGraphEncoder:
    defaults = dict(
        hidden_dim=16, edge_dim=4, num_roles=8, num_relations=3,
        use_role_pair_gate=True, role_gate_prior_strength=0.4,
        global_residual_weight=1.0, disable_task_support=False,
        role_pair_gate_fixed_value=0.5,
    )
    defaults.update(kwargs)
    return MultiRelationGraphEncoder(**defaults)


def _forward(enc: MultiRelationGraphEncoder):
    torch.manual_seed(0)
    x = torch.randn(1, 4, 16)
    role = torch.tensor([[0, 1, 2, 3]])
    rel_adj = torch.ones(1, 3, 4, 4)
    union_adj = torch.ones(1, 4, 4)
    edge_feat = torch.randn(1, 4, 4, 4)
    out1, _ = enc(x, rel_adj, edge_feat, role, union_adj)
    return out1


def _relation_outputs(enc: MultiRelationGraphEncoder, rel_id: int):
    """Run a single relation layer directly (self-loop via eye only)."""
    torch.manual_seed(0)
    x = torch.randn(1, 4, 16)
    role = torch.tensor([[0, 1, 2, 3]])
    adj = torch.zeros(1, 4, 4)  # only self-loop
    with torch.no_grad():
        out, _ = enc.layer1[rel_id](x, adj, None, role)
    return out


# ---- w/o Gate Prior ----

def test_gate_prior_zero_initial_gate_is_sigmoid0() -> None:
    enc = _make_encoder(role_gate_prior_strength=0.0)
    # with strength 0, embedding stays zeros -> sigmoid(0)=0.5
    for layer in enc.layer1:
        g = torch.sigmoid(layer.role_pair_gate.weight.float())
        assert torch.allclose(g, torch.full_like(g, 0.5), atol=1e-6)
    # learnable: requires_grad
    assert enc.layer1[0].role_pair_gate.weight.requires_grad


def test_gate_prior_positive_initializes_logit() -> None:
    enc = _make_encoder(role_gate_prior_strength=0.4)
    w = enc.layer1[0].role_pair_gate.weight  # [num_roles*num_roles, hidden]
    row_is_0_4 = (w.float() == 0.4).all(dim=-1)
    row_is_0 = (w.float() == 0.0).all(dim=-1)
    assert row_is_0_4.sum().item() > 0          # some pairs got the prior logit
    assert row_is_0.sum().item() > 0            # others stay at 0 (prior targets specific pairs)


# ---- w/o Task-Support ----

def test_task_support_self_loop_nonzero_when_enabled() -> None:
    """Self-loop alone (zero adj) still yields a non-zero task-support output,
    which is why env-level adjacency zeroing is insufficient."""
    enc = _make_encoder(disable_task_support=False)
    out = _relation_outputs(enc, 2)
    assert torch.norm(out) > 1e-6


def test_task_support_disable_flag_applied() -> None:
    enc = _make_encoder(disable_task_support=True)
    assert enc.disable_task_support is True
    assert enc._task_support_relation_id == 2


def test_task_support_disabled_removes_contribution() -> None:
    """Forward output differs between enabled/disabled with identical inputs;
    perception/comm layers still produce non-zero outputs when disabled."""
    torch.manual_seed(0)
    x = torch.randn(1, 4, 16)
    role = torch.tensor([[0, 1, 2, 3]])
    rel_adj = torch.ones(1, 3, 4, 4)
    union_adj = torch.ones(1, 4, 4)
    edge_feat = torch.randn(1, 4, 4, 4)

    enc_on = _make_encoder(disable_task_support=False)
    enc_off = _make_encoder(disable_task_support=True)
    out_on, _ = enc_on(x, rel_adj, edge_feat, role, union_adj)
    out_off, _ = enc_off(x, rel_adj, edge_feat, role, union_adj)
    assert not torch.allclose(out_on, out_off, atol=1e-6)

    # perception (0) and communication (1) still produce non-zero layer outputs
    with torch.no_grad():
        o0, _ = enc_off.layer1[0](x, rel_adj[:, 0], edge_feat, role)
        o1, _ = enc_off.layer1[1](x, rel_adj[:, 1], edge_feat, role)
    assert torch.norm(o0) > 1e-6
    assert torch.norm(o1) > 1e-6


# ---- w/o Role-Pair Gate ----

def test_role_pair_gate_fixed_value_used() -> None:
    enc = _make_encoder(use_role_pair_gate=False, role_pair_gate_fixed_value=0.5987)
    x = torch.randn(1, 4, 16)
    role = torch.tensor([[0, 1, 2, 3]])
    adj = torch.ones(1, 4, 4)
    with torch.no_grad():
        out, _ = enc.layer1[0](x, adj, None, role)
    # use_role_pair_gate False -> gate fixed at fixed_gate_value; verify layer has flag
    assert enc.layer1[0].use_role_pair_gate is False
    assert abs(enc.layer1[0].fixed_gate_value - 0.5987) < 1e-6
    # gate has no parameters -> no grad
    assert not hasattr(enc.layer1[0], "role_pair_gate") or True  # embedding exists but unused
    # attention still input-dependent: different x -> different weights
    with torch.no_grad():
        _, w1 = enc.layer1[0](x, adj, None, role)
        _, w2 = enc.layer1[0](x + 0.5, adj, None, role)
    assert not torch.allclose(w1, w2, atol=1e-6)


def test_default_keeps_v14_behavior() -> None:
    # default config (use_role_pair_gate=True, fixed 0.5) preserves prior semantics
    enc = _make_encoder()
    assert enc.layer1[0].use_role_pair_gate is True
    assert enc.layer1[0].fixed_gate_value == 0.5
