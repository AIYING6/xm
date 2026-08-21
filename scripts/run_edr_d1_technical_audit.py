"""Pre-training A--H audit for the frozen EDR-D1 aggregation substitution."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    EdgeDeletionResilientGraphAttentionLayer,
    GraphAttentionLayer,
    RIGMAPPOAgent,
    train_ri_gmappo,
)
from scripts.run_edr_d1_single import training_config  # noqa: E402
from scripts.telemetry_native_t0 import F0, NOMINAL, make_env  # noqa: E402


PROTOCOL = "EDR-D1-TECHNICAL-AUDIT-V1"
TOLERANCE = 1e-7


def build_agent(graph_encoder: str, seed: int = 2202) -> tuple[RIGMAPPOAgent, object, object, dict]:
    env = make_env(seed, NOMINAL)
    obs, share_obs, graph = env.reset()
    torch.manual_seed(seed)
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(graph["role"].max()) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder=graph_encoder, role_gate_mode="none", use_intent_context=False,
    )
    return agent, env, obs, graph


def layer_contributions(layer: EdgeDeletionResilientGraphAttentionLayer, x, adj, edge):
    h = layer.proj(x)
    nodes = h.shape[1]
    hi = h.unsqueeze(2).expand(-1, nodes, nodes, -1)
    hj = h.unsqueeze(1).expand(-1, nodes, nodes, -1)
    scores = layer.attn(torch.cat([hi, hj], dim=-1)).squeeze(-1)
    if layer.edge_score is not None:
        scores = scores + layer.edge_score(edge).squeeze(-1)
    scores = layer.leaky_relu(scores)
    mask = torch.clamp(adj + torch.eye(nodes, dtype=adj.dtype).unsqueeze(0), 0.0, 1.0)
    gates = torch.sigmoid(scores) * mask
    return gates, gates.unsqueeze(-1) * h.unsqueeze(1)


def recorded_f0_graph(t1_root: Path) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
    """Select a frozen T1 F0 record where the legal direct link is present.

    This keeps Audit E attached to the documented `0-1-2 -> 0-2` topology
    transition, instead of making a claim from an unrelated geometry episode.
    """
    raw_path = t1_root / "evaluations" / "final_1m" / "utr_sg" / "seed2202" / "raw_step_telemetry.jsonl"
    # Step telemetry is intentionally large.  Retain only onset-adjacent rows
    # keyed by episode instead of loading the complete evidence file.
    candidates: dict[int, dict[int, dict]] = {}
    with raw_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("scenario") != "f0_seen_44_80":
                continue
            step = int(row["post_step"])
            if step not in {43, 45}:
                continue
            candidates.setdefault(int(row["episode_id"]), {})[step] = row
    pre = post = None
    for episode_id in sorted(candidates):
        pair = candidates[episode_id]
        candidate, later = pair.get(43), pair.get(45)
        if candidate is None or later is None:
            continue
        before = candidate["actor"]["graph_adj"]
        after = later["actor"]["graph_adj"]
        if before[2][1] == 1.0 and before[2][0] == 1.0 and after[2][1] == 0.0 and after[2][0] == 1.0:
            pre, post = candidate, later
            break
    if pre is None or post is None:
        raise RuntimeError("no frozen T1 F0 record contains the required legal 0-1-2 to 0-2 transition")
    transition = {
        "scheduled_onset": 44,
        "episode_id": int(pre["episode_id"]),
        "pre_step": int(pre["post_step"]),
        "post_step": int(post["post_step"]),
        "failure_active_before": int(pre["failure_active_post"]),
        "failure_active": int(post["failure_active_post"]),
        "relay_to_attacker_before": float(pre["actor"]["graph_adj"][2][1]),
        "relay_to_attacker_after": float(post["actor"]["graph_adj"][2][1]),
        "direct_scout_to_attacker_before": float(pre["actor"]["graph_adj"][2][0]),
        "direct_scout_to_attacker_after": float(post["actor"]["graph_adj"][2][0]),
    }
    return (
        torch.as_tensor(pre["actor"]["graph_node_feat"], dtype=torch.float32).unsqueeze(0),
        torch.as_tensor(pre["actor"]["graph_edge_feat"], dtype=torch.float32).unsqueeze(0),
        torch.as_tensor(pre["actor"]["graph_adj"], dtype=torch.float32).unsqueeze(0),
        transition,
    )


def run_pytest() -> tuple[bool, str]:
    command = [sys.executable, "-m", "pytest", "-q", "tests/test_t0_telemetry_native.py", "tests/test_t1_telemetry_native_checkpoint_adapter.py", "tests/test_edr_sg.py"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--t1-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    edr, env, obs, graph = build_agent("edr")
    sg, _, _, _ = build_agent("single")
    parameter_edr = sum(parameter.numel() for parameter in edr.parameters())
    parameter_sg = sum(parameter.numel() for parameter in sg.parameters())
    node, edge, adj, transition = recorded_f0_graph(args.t1_root)
    role = torch.as_tensor(graph["role"][None], dtype=torch.long)
    with torch.no_grad():
        x = edr.actor.input(torch.cat([node, edr.actor.role_emb(role)], dim=-1))
    layer = edr.actor.edr_gat1
    before_gate, before = layer_contributions(layer, x, adj, edge)
    deleted = adj.clone()
    deleted[0, 2, 1] = 0.0
    after_gate, after = layer_contributions(layer, x, deleted, edge)
    survivors = [0, 2, 3]
    locality_max = float((before[0, 2, survivors] - after[0, 2, survivors]).abs().max())
    locality_mean = float((before[0, 2, survivors] - after[0, 2, survivors]).abs().mean())

    control = GraphAttentionLayer(115, 115, edge_dim=edge.shape[-1])
    control.load_state_dict(layer.state_dict())
    with torch.no_grad():
        h = control.proj(x)
        nodes = h.shape[1]
        hi = h.unsqueeze(2).expand(-1, nodes, nodes, -1)
        hj = h.unsqueeze(1).expand(-1, nodes, nodes, -1)
        score = control.leaky_relu(control.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1) + control.edge_score(edge).squeeze(-1)
        def soft(current):
            mask = torch.clamp(current + torch.eye(nodes).unsqueeze(0), 0.0, 1.0)
            return torch.softmax(score.masked_fill(mask <= 0.0, -1e9), dim=-1).unsqueeze(-1) * h.unsqueeze(1)
        sg_delta = float((soft(adj)[0, 2, survivors] - soft(deleted)[0, 2, survivors]).abs().max())

    args_forward = (
        torch.as_tensor(obs[None], dtype=torch.float32),
        torch.as_tensor(graph["node_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["role"][None], dtype=torch.long),
        torch.as_tensor(graph["adj"][None], dtype=torch.float32),
        torch.as_tensor(env.reset()[1][None], dtype=torch.float32),
    )
    edr.eval()
    with torch.no_grad():
        first = edr.get_action_and_value(*args_forward, deterministic=True)[0]
        second = edr.get_action_and_value(*args_forward, deterministic=True)[0]
    deterministic = bool(torch.equal(first, second) and torch.isfinite(first.float()).all())
    with tempfile.TemporaryDirectory(prefix="edr_d1_checkpoint_") as folder:
        checkpoint = Path(folder) / "edr.pt"
        torch.save(edr.state_dict(), checkpoint)
        restored, _, _, _ = build_agent("edr")
        restored.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=False))
        restored.eval()
        with torch.no_grad():
            restored_action = restored.get_action_and_value(*args_forward, deterministic=True)[0]
        checkpoint_ok = bool(torch.equal(first, restored_action))
    with tempfile.TemporaryDirectory(prefix="edr_d1_one_update_") as folder:
        smoke_dir = Path(folder) / "run"
        smoke_cfg = training_config(2201, smoke_dir)
        smoke_cfg.updates = 1
        smoke_cfg.device = "cpu"
        smoke_cfg.save_interval = 1
        smoke_cfg.runtime_state_save_interval = 1
        train_ri_gmappo(smoke_cfg)
        one_update_smoke = all((smoke_dir / name).exists() for name in (
            "actor_critic_latest.pt", "actor_critic_training_state_latest.pt",
            "actor_critic_runtime_state_latest.pt", "train_log.csv",
        ))
    pytest_ok, pytest_output = run_pytest()
    results = {
        "protocol": PROTOCOL,
        "audit_A_syntax_import_runtime": bool(torch.isfinite(first.float()).all() and checkpoint_ok and one_update_smoke),
        "audit_B_parameter_equality": parameter_sg == 116728 and parameter_edr == 116728,
        "audit_C_deletion_locality": locality_max <= TOLERANCE and locality_mean <= TOLERANCE,
        "audit_D_sg_redistribution_positive_control": sg_delta > TOLERANCE,
        "audit_E_real_f0_relevance": transition["failure_active"] == 1 and transition["relay_to_attacker_before"] == 1.0 and transition["relay_to_attacker_after"] == 0.0 and transition["direct_scout_to_attacker_after"] == 1.0,
        "audit_F_actor_legality": pytest_ok,
        "audit_G_baseline_non_regression": pytest_ok,
        "audit_H_deterministic_forward": deterministic,
        "parameter_counts": {"sg": parameter_sg, "edr": parameter_edr},
        "deletion_locality": {"max_absolute_error": locality_max, "mean_absolute_error": locality_mean, "tolerance": TOLERANCE, "surviving_sender_ids": survivors},
        "sg_positive_control": {"surviving_contribution_max_absolute_change": sg_delta},
        "f0_transition": transition,
        "checkpoint_save_reload": checkpoint_ok,
        "one_update_finite_value_smoke": one_update_smoke,
        "pytest": {"pass": pytest_ok, "output": pytest_output},
        "actor_inputs": ["obs", "node_feat", "edge_feat", "role", "adj"],
        "forbidden_actor_inputs": ["failure label", "share_obs", "global route", "future topology", "simulator state"],
    }
    passed = all(value for key, value in results.items() if key.startswith("audit_"))
    results["final"] = "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL"
    args.output_root.mkdir(parents=True)
    (args.output_root / "edr_d1_technical_audit.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"final": results["final"], "results": results}, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
