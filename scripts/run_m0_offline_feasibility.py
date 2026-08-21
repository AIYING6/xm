"""M0 zero-rollout feasibility probes for mature robust-policy candidates.

This tool never calls an environment, takes no optimizer step, and never writes
model state.  It reads a bounded, deterministic set of actor-legal graph states
from the frozen T1 telemetry and reports two exploratory signals:

* local policy response to a legal relay-edge deletion;
* local policy response to a norm-bounded actor-parameter perturbation.

The former informs a Lipschitz/spectral-policy candidate; the latter is a
behavioural sharpness proxy for a SAM-style candidate.  Neither is used as a
selection threshold or as performance evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.distributions import Categorical

from scripts.telemetry_native_t1 import build_matched_sg_agent


SEEDS = (2201, 2202, 2203, 2204, 2205)
SAMPLES_PER_SEED = 24


def actor_tensors(row: dict[str, Any], device: torch.device) -> tuple[torch.Tensor, ...]:
    actor = row["actor"]
    return (
        torch.as_tensor(actor["obs"], dtype=torch.float32, device=device).unsqueeze(0),
        torch.as_tensor(actor["graph_node_feat"], dtype=torch.float32, device=device).unsqueeze(0),
        torch.as_tensor(actor["graph_edge_feat"], dtype=torch.float32, device=device).unsqueeze(0),
        torch.as_tensor(actor["graph_role"], dtype=torch.long, device=device).unsqueeze(0),
        torch.as_tensor(actor["graph_adj"], dtype=torch.float32, device=device).unsqueeze(0),
        torch.as_tensor(actor["share_obs"], dtype=torch.float32, device=device).unsqueeze(0),
        torch.as_tensor(actor["graph_relation_adj"], dtype=torch.float32, device=device).unsqueeze(0),
    )


def logits(agent: torch.nn.Module, row: dict[str, Any], adj_override: torch.Tensor | None = None) -> torch.Tensor:
    obs, node, edge, role, adj, _share, relation = actor_tensors(row, next(agent.parameters()).device)
    if adj_override is not None:
        adj = adj_override
    with torch.no_grad():
        values = agent.actor(obs, node, edge, role, adj, agent.num_agents, relation_adj=relation)
    return values[0]


def mean_kl(reference_logits: torch.Tensor, changed_logits: torch.Tensor) -> float:
    reference = Categorical(logits=reference_logits)
    changed = Categorical(logits=changed_logits)
    return float(torch.distributions.kl_divergence(reference, changed).mean().item())


def relay_deletion(adj: torch.Tensor) -> torch.Tensor:
    """Delete only non-self messages *from* relay node 1; preserve direct 0->2."""
    changed = adj.clone()
    changed[:, :, 1] = 0.0
    changed[:, 1, 1] = 1.0
    return changed


def collect_f0_states(raw_path: Path, limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    # Use the final pre-trigger state.  We then apply an in-memory legal relay
    # deletion to exactly that same actor state, avoiding confounding topology
    # sensitivity with subsequent trajectory progression.
    with raw_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("scenario") != "f0_seen_44_80" or int(row.get("timestep", -1)) != 43:
                continue
            episode_id = int(row["episode_id"])
            if episode_id in seen:
                continue
            seen.add(episode_id)
            selected.append(row)
            if len(selected) == limit:
                break
    if len(selected) != limit:
        raise RuntimeError(f"expected {limit} F0 actor states in {raw_path}, found {len(selected)}")
    return selected


def spectral_norms(agent: torch.nn.Module) -> dict[str, float]:
    result: dict[str, float] = {}
    for name, parameter in agent.actor.named_parameters():
        if parameter.ndim == 2:
            result[name] = float(torch.linalg.matrix_norm(parameter.detach(), ord=2).cpu().item())
    return result


def parameter_perturbation(agent: torch.nn.Module, radius: float, generator: torch.Generator) -> list[torch.Tensor]:
    parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    noises = [torch.randn(parameter.shape, generator=generator, device=parameter.device, dtype=parameter.dtype) for parameter in parameters]
    norm = torch.sqrt(sum((noise * noise).sum() for noise in noises))
    parameter_norm = torch.sqrt(sum((parameter.detach() * parameter.detach()).sum() for parameter in parameters))
    scale = radius * parameter_norm / norm.clamp_min(1e-12)
    with torch.no_grad():
        for parameter, noise in zip(parameters, noises):
            parameter.add_(noise * scale)
    return [noise * scale for noise in noises]


def restore_parameters(agent: torch.nn.Module, perturbations: list[torch.Tensor]) -> None:
    parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    with torch.no_grad():
        for parameter, perturbation in zip(parameters, perturbations):
            parameter.sub_(perturbation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parameter-radius", type=float, default=0.01)
    args = parser.parse_args()

    device = torch.device("cpu")
    report: dict[str, Any] = {
        "protocol": "M0-OFFLINE-FEASIBILITY-V1",
        "zero_training": True,
        "zero_rollout": True,
        "parameter_radius": args.parameter_radius,
        "states_per_seed": SAMPLES_PER_SEED,
        "relay_deletion": "remove non-self sender=1 graph messages while preserving every other recorded legal edge",
        "per_seed": {},
    }
    for seed in SEEDS:
        checkpoint = args.t1_root / "runs" / "utr_sg" / f"seed{seed}" / "actor_critic_latest.pt"
        raw = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        agent = build_matched_sg_agent(checkpoint, construction_seed=seed, device=str(device))
        states = collect_f0_states(raw, SAMPLES_PER_SEED)
        local_kls: list[float] = []
        parameter_kls: list[float] = []
        for index, state in enumerate(states):
            base = logits(agent, state)
            tensors = actor_tensors(state, device)
            local_kls.append(mean_kl(base, logits(agent, state, relay_deletion(tensors[4]))))
            generator = torch.Generator(device=device).manual_seed(seed * 10_000 + index)
            perturbations = parameter_perturbation(agent, args.parameter_radius, generator)
            try:
                parameter_kls.append(mean_kl(base, logits(agent, state)))
            finally:
                restore_parameters(agent, perturbations)
        report["per_seed"][str(seed)] = {
            "mean_policy_kl_under_local_relay_deletion": float(np.mean(local_kls)),
            "mean_policy_kl_under_parameter_perturbation": float(np.mean(parameter_kls)),
            "spectral_norms": spectral_norms(agent),
        }
    report["interpretation_boundary"] = (
        "These are exploratory sensitivity diagnostics, not return estimates, training evidence, "
        "or a selection threshold.  They use only actor-legal recorded inputs and in-memory weights."
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
