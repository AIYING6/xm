"""Topology-group constrained actor transaction used by TGTR-PPO C1.

This module is intentionally independent of evaluation code.  It consumes a
single training rollout containing fixed design/certificate stream labels,
uses ordinary Adam/PPO as the proposed update, and minimally projects only the
actor displacement when held-stream topology checks require it.
"""
from __future__ import annotations

import copy
import itertools
import math
import time
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from algorithms.ri_gmappo.drtp_topology_sampler import ALL_GROUPS, FAILURE_GROUPS, NOMINAL_GROUP
from algorithms.ri_gmappo.simple_ri_gmappo import (
    _restore_optimizer_parameter_states,
    _snapshot_optimizer_parameter_states,
    effective_chain_aux_coef,
    effective_intent_coef,
)


BACKTRACK_ALPHAS = (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625)
CERTIFICATE_NUMERICAL_TOLERANCE = 1e-7


def clip_derived_kl_cap(clip_coef: float) -> float:
    epsilon = float(clip_coef)
    if not 0.0 < epsilon < 1.0:
        raise ValueError("PPO clip coefficient must lie in (0, 1)")
    return -epsilon - math.log1p(-epsilon)


def flatten_tensors(values: list[torch.Tensor]) -> torch.Tensor:
    return torch.cat([value.reshape(-1) for value in values])


def assign_flat_parameters(parameters: list[torch.nn.Parameter], base: list[torch.Tensor], displacement: torch.Tensor, alpha: float = 1.0) -> None:
    cursor = 0
    with torch.no_grad():
        for parameter, original in zip(parameters, base):
            count = parameter.numel()
            parameter.copy_(original + float(alpha) * displacement[cursor:cursor + count].reshape_as(parameter))
            cursor += count
    if cursor != displacement.numel():
        raise ValueError("flat actor displacement has the wrong size")


def project_halfspaces(displacement: torch.Tensor, normals: list[torch.Tensor], tolerance: float = 1e-8) -> tuple[torch.Tensor, dict[str, Any]]:
    """Exact active-set projection onto ``normal @ d >= 0`` halfspaces."""
    if not normals:
        return displacement.clone(), {"active_constraint_indices": [], "max_violation": 0.0}
    output_device, output_dtype = displacement.device, displacement.dtype
    matrix = torch.stack([normal.to(displacement) for normal in normals]).detach().double().cpu()
    displacement64 = displacement.detach().double().cpu()
    values = matrix @ displacement64
    if bool(torch.all(values >= -tolerance)):
        return displacement.clone(), {"active_constraint_indices": [], "max_violation": float(torch.clamp(-values, min=0).max())}
    gram = (matrix @ matrix.T).numpy()
    rhs_all = (-values).numpy()
    best: tuple[float, torch.Tensor, tuple[int, ...]] | None = None
    count = len(normals)
    for size in range(1, count + 1):
        for active in itertools.combinations(range(count), size):
            idx = np.asarray(active, dtype=np.int64)
            sub_gram = gram[np.ix_(idx, idx)]
            multipliers = np.linalg.lstsq(sub_gram, rhs_all[idx], rcond=None)[0]
            if np.any(multipliers < -tolerance):
                continue
            correction = torch.zeros_like(displacement64)
            for coefficient, normal_index in zip(multipliers, active):
                correction.add_(matrix[normal_index], alpha=float(max(0.0, coefficient)))
            candidate = displacement64 + correction
            candidate_values = matrix @ candidate
            if bool(torch.any(candidate_values < -tolerance)):
                continue
            objective = float(correction.square().sum().detach().cpu())
            if best is None or objective < best[0]:
                best = (objective, candidate, active)
    if best is None:
        zero = torch.zeros_like(displacement)
        return zero, {"active_constraint_indices": list(range(count)), "max_violation": 0.0, "fallback_zero": True}
    projected64 = best[1]
    projected = projected64.to(device=output_device, dtype=output_dtype)
    violation = torch.clamp(-(matrix @ projected64), min=0.0)
    return projected, {
        "active_constraint_indices": list(best[2]),
        "max_violation": float(violation.max().detach().cpu()),
        "fallback_zero": False,
    }


def _batch_tensors(batch: dict, device: torch.device) -> dict[str, Any]:
    t_steps, n_envs, num_agents = batch["actions"].shape
    graphs = t_steps * n_envs
    result = {
        "num_graphs": graphs,
        "num_agents": num_agents,
        "obs": torch.as_tensor(batch["obs"].reshape(graphs, num_agents, -1), dtype=torch.float32, device=device),
        "share_obs": torch.as_tensor(batch["share_obs"].reshape(graphs, num_agents, -1), dtype=torch.float32, device=device),
        "node_feat": torch.as_tensor(batch["node_feat"].reshape(graphs, *batch["node_feat"].shape[2:]), dtype=torch.float32, device=device),
        "edge_feat": torch.as_tensor(batch["edge_feat"].reshape(graphs, *batch["edge_feat"].shape[2:]), dtype=torch.float32, device=device),
        "role": torch.as_tensor(batch["role"].reshape(graphs, *batch["role"].shape[2:]), dtype=torch.long, device=device),
        "adj": torch.as_tensor(batch["adj"].reshape(graphs, *batch["adj"].shape[2:]), dtype=torch.float32, device=device),
        "relation_adj": torch.as_tensor(batch["relation_adj"].reshape(graphs, *batch["relation_adj"].shape[2:]), dtype=torch.float32, device=device),
        "intent_label": torch.as_tensor(batch["intent_label"].reshape(graphs, -1), dtype=torch.long, device=device),
        "actions": torch.as_tensor(batch["actions"].reshape(graphs, num_agents), dtype=torch.long, device=device),
        "old_logp": torch.as_tensor(batch["logp"].reshape(graphs, num_agents), dtype=torch.float32, device=device),
        "advantages": torch.as_tensor(batch["advantages"].reshape(graphs, num_agents), dtype=torch.float32, device=device),
        "returns": torch.as_tensor(batch["returns"].reshape(graphs, num_agents), dtype=torch.float32, device=device),
        "groups": np.asarray(batch["condition_group"]).reshape(graphs),
        "splits": np.asarray(batch["condition_split"]).reshape(graphs),
    }
    result["advantages"] = (result["advantages"] - result["advantages"].mean()) / (result["advantages"].std() + 1e-8)
    return result


def _forward(agent, tensors: dict):
    logits, _, intent_logits, chain_aux_logits = agent.actor(
        tensors["obs"], tensors["node_feat"], tensors["edge_feat"], tensors["role"], tensors["adj"],
        agent.num_agents, relation_adj=tensors["relation_adj"], intent_label=tensors["intent_label"],
        return_chain_aux=True,
    )
    log_probs = torch.log_softmax(logits, dim=-1)
    selected = log_probs.gather(-1, tensors["actions"].unsqueeze(-1)).squeeze(-1)
    entropy = -(log_probs.exp() * log_probs).sum(dim=-1)
    values = agent.critic_value(tensors["share_obs"], tensors["role"])
    return logits, selected, entropy, values, intent_logits, chain_aux_logits


def _surrogate_per_graph(selected_logp: torch.Tensor, tensors: dict, clip_coef: float) -> torch.Tensor:
    ratio = (selected_logp - tensors["old_logp"]).exp()
    unclipped = ratio * tensors["advantages"]
    clipped = torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef) * tensors["advantages"]
    return torch.minimum(unclipped, clipped).mean(dim=1)


def ordinary_full_batch_update(agent, optimizer, batch: dict, cfg, device: torch.device) -> dict[str, Any]:
    """Matched Sync-UTR PPO update in canonical full-batch order.

    The canonical order removes floating-point differences caused solely by a
    permutation of a complete minibatch, making critic equality auditable.
    """
    tensors = _batch_tensors(batch, device)
    started = time.perf_counter()
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    for _ in range(int(cfg.ppo_epochs)):
        _, selected, entropy, values, _, _ = _forward(agent, tensors)
        surrogate = _surrogate_per_graph(selected, tensors, cfg.clip_coef)
        actor_loss = -surrogate.mean() - cfg.entropy_coef * entropy.mean()
        value_loss = 0.5 * (tensors["returns"] - values).pow(2).mean()
        optimizer.zero_grad(set_to_none=True)
        (actor_loss + cfg.value_coef * value_loss).backward()
        torch.nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
        optimizer.step()
    return {
        "wall_seconds": time.perf_counter() - started,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
    }


def synchronize_module_optimizer_state(target_module, source_module, target_optimizer, source_optimizer) -> None:
    """Copy a module and its Adam slots between isomorphic branch objects."""
    target_module.load_state_dict(copy.deepcopy(source_module.state_dict()), strict=True)
    target_parameters = list(target_module.parameters())
    source_parameters = list(source_module.parameters())
    if len(target_parameters) != len(source_parameters):
        raise ValueError("cannot synchronize non-isomorphic optimizer parameter sets")
    for target, source in zip(target_parameters, source_parameters):
        if source in source_optimizer.state:
            target_optimizer.state[target] = copy.deepcopy(source_optimizer.state[source])
        else:
            target_optimizer.state.pop(target, None)


def _metrics(agent, tensors: dict, reference_logits: torch.Tensor, reference_surrogate: torch.Tensor, clip_coef: float, split: str) -> dict[str, Any]:
    with torch.no_grad():
        logits, selected, _, _, _, _ = _forward(agent, tensors)
        surrogate = _surrogate_per_graph(selected, tensors, clip_coef)
        old_log_probs = torch.log_softmax(reference_logits, dim=-1)
        old_probs = old_log_probs.exp()
        new_log_probs = torch.log_softmax(logits, dim=-1)
        full_kl = (old_probs * (old_log_probs - new_log_probs)).sum(dim=-1).mean(dim=1)
    split_mask = tensors["splits"] == split
    result: dict[str, Any] = {"groups": {}}
    for group in ALL_GROUPS:
        mask_np = split_mask & (tensors["groups"] == group)
        if not np.any(mask_np):
            raise RuntimeError(f"missing {split} samples for topology group {group}")
        mask = torch.as_tensor(mask_np, dtype=torch.bool, device=surrogate.device)
        result["groups"][group] = {
            "surrogate_change": float((surrogate[mask] - reference_surrogate[mask]).mean().cpu()),
            "full_categorical_kl": float(full_kl[mask].mean().cpu()),
            "graphs": int(mask.sum().item()),
        }
    failure_np = split_mask & np.isin(tensors["groups"], FAILURE_GROUPS)
    failure_mask = torch.as_tensor(failure_np, dtype=torch.bool, device=surrogate.device)
    all_mask = torch.as_tensor(split_mask, dtype=torch.bool, device=surrogate.device)
    result["pooled_failure_surrogate_change"] = float((surrogate[failure_mask] - reference_surrogate[failure_mask]).mean().cpu())
    result["overall_surrogate_change"] = float((surrogate[all_mask] - reference_surrogate[all_mask]).mean().cpu())
    return result


def evaluate_actor_change(agent, batch: dict, reference_actor_state: dict, cfg, device: torch.device) -> dict[str, Any]:
    tensors = _batch_tensors(batch, device)
    current_state = copy.deepcopy(agent.actor.state_dict())
    try:
        agent.actor.load_state_dict(reference_actor_state, strict=True)
        with torch.no_grad():
            reference_logits, selected, _, _, _, _ = _forward(agent, tensors)
            reference_surrogate = _surrogate_per_graph(selected, tensors, cfg.clip_coef)
    finally:
        agent.actor.load_state_dict(current_state, strict=True)
    return {
        "design": _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "design"),
        "certificate": _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "certificate"),
    }


def tgtr_update_policy(agent, optimizer, batch: dict, cfg, device: torch.device) -> dict[str, Any]:
    """Run the frozen TGTR actor transaction for all matched PPO epochs."""
    tensors = _batch_tensors(batch, device)
    if tensors["num_graphs"] != 1536:
        raise ValueError("TGTR C1 requires a complete 24x64 rollout")
    for group in ALL_GROUPS:
        for split in ("design", "certificate"):
            expected = 384 if group == NOMINAL_GROUP else 64
            actual = int(np.sum((tensors["groups"] == group) & (tensors["splits"] == split)))
            if actual != expected:
                raise ValueError(f"TGTR batch contract violation for {group}/{split}: {actual} != {expected}")
    actor_parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    kl_cap = clip_derived_kl_cap(cfg.clip_coef)
    epoch_rows = []
    started = time.perf_counter()
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    for epoch in range(1, int(cfg.ppo_epochs) + 1):
        actor_before = copy.deepcopy(agent.actor.state_dict())
        actor_tensors_before = [parameter.detach().clone() for parameter in actor_parameters]
        actor_optimizer_before = _snapshot_optimizer_parameter_states(optimizer, actor_parameters)
        with torch.no_grad():
            reference_logits, reference_selected, _, _, _, _ = _forward(agent, tensors)
            reference_surrogate = _surrogate_per_graph(reference_selected, tensors, cfg.clip_coef)

        logits, selected, entropy, values, _, _ = _forward(agent, tensors)
        surrogate = _surrogate_per_graph(selected, tensors, cfg.clip_coef)
        design_mask_np = tensors["splits"] == "design"
        design_mask = torch.as_tensor(design_mask_np, dtype=torch.bool, device=device)
        actor_loss = -surrogate.mean() - cfg.entropy_coef * entropy.mean()
        value_loss = 0.5 * (tensors["returns"] - values).pow(2).mean()

        group_objectives = []
        for group in ALL_GROUPS:
            group_mask = torch.as_tensor(
                design_mask_np & (tensors["groups"] == group), dtype=torch.bool, device=device
            )
            group_objectives.append(surrogate[group_mask].mean())
        objective_vector = torch.stack(group_objectives)
        batched_raw = torch.autograd.grad(
            objective_vector,
            actor_parameters,
            grad_outputs=torch.eye(len(ALL_GROUPS), dtype=objective_vector.dtype, device=device),
            retain_graph=True,
            allow_unused=True,
            is_grads_batched=True,
        )
        group_ascent_gradients = {}
        for group_index, group in enumerate(ALL_GROUPS):
            group_ascent_gradients[group] = flatten_tensors([
                torch.zeros_like(parameter).reshape(-1)
                if gradient is None else gradient[group_index].detach().reshape(-1)
                for parameter, gradient in zip(actor_parameters, batched_raw)
            ])
        overall_gradient = 0.5 * group_ascent_gradients[NOMINAL_GROUP]
        for group in FAILURE_GROUPS:
            overall_gradient = overall_gradient + (1.0 / 12.0) * group_ascent_gradients[group]

        optimizer.zero_grad(set_to_none=True)
        (actor_loss + cfg.value_coef * value_loss).backward()
        torch.nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
        optimizer.step()
        attempted = flatten_tensors([parameter.detach() - original for parameter, original in zip(actor_parameters, actor_tensors_before)])
        ordinary_design = _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "design")
        active_groups = [
            group for group in FAILURE_GROUPS
            if ordinary_design["groups"][group]["surrogate_change"] < 0.0
        ]
        normals = [group_ascent_gradients[NOMINAL_GROUP], *[group_ascent_gradients[group] for group in active_groups], overall_gradient]
        projected, projection = project_halfspaces(attempted, normals)
        correction_norm = float(torch.linalg.vector_norm(projected - attempted).cpu())
        attempted_norm = float(torch.linalg.vector_norm(attempted).cpu())

        accepted_alpha = 0.0
        accepted_metrics = None
        certificate_attempts = []
        candidate_nonzero = float(torch.linalg.vector_norm(projected).cpu()) > 1e-12
        for alpha in BACKTRACK_ALPHAS if candidate_nonzero else ():
            assign_flat_parameters(actor_parameters, actor_tensors_before, projected, alpha)
            metrics = _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "certificate")
            minimum_group_surrogate = min(metrics["groups"][group]["surrogate_change"] for group in ALL_GROUPS)
            maximum_group_kl = max(metrics["groups"][group]["full_categorical_kl"] for group in ALL_GROUPS)
            group_ok = minimum_group_surrogate >= -CERTIFICATE_NUMERICAL_TOLERANCE
            kl_ok = all(metrics["groups"][group]["full_categorical_kl"] <= kl_cap for group in ALL_GROUPS)
            finite = all(
                math.isfinite(value)
                for group in ALL_GROUPS
                for value in metrics["groups"][group].values()
                if isinstance(value, float)
            )
            certificate_attempts.append({
                "alpha": alpha,
                "minimum_group_surrogate_change": minimum_group_surrogate,
                "pooled_failure_surrogate_change": metrics["pooled_failure_surrogate_change"],
                "maximum_group_full_categorical_kl": maximum_group_kl,
                "finite": finite,
            })
            if (
                group_ok
                and metrics["pooled_failure_surrogate_change"] >= -CERTIFICATE_NUMERICAL_TOLERANCE
                and kl_ok and finite
            ):
                accepted_alpha = alpha
                accepted_metrics = metrics
                break
        if accepted_metrics is None:
            agent.actor.load_state_dict(actor_before, strict=True)
            _restore_optimizer_parameter_states(optimizer, actor_optimizer_before)
            accepted_metrics = _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "certificate")
        epoch_rows.append({
            "epoch": epoch,
            "active_groups": active_groups,
            "attempted_displacement_l2": attempted_norm,
            "correction_l2": correction_norm,
            "qp": projection,
            "accepted_alpha": accepted_alpha,
            "zero_step": accepted_alpha == 0.0,
            "ordinary_design": ordinary_design,
            "accepted_certificate": accepted_metrics,
            "certificate_attempts": certificate_attempts,
            "certificate_numerical_tolerance": CERTIFICATE_NUMERICAL_TOLERANCE,
            "actor_optimizer_state_policy": "ordinary_adam_slots_retained_after_nonzero_projection",
        })
    wall = time.perf_counter() - started
    peak = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
    return {
        "epochs": epoch_rows,
        "wall_seconds": wall,
        "peak_gpu_memory_bytes": peak,
        "zero_step_count": sum(bool(row["zero_step"]) for row in epoch_rows),
        "nonzero_step_count": sum(not bool(row["zero_step"]) for row in epoch_rows),
        "kl_cap": kl_cap,
    }
