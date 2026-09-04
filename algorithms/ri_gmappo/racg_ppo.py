"""Frozen RACG-PPO actor update for the C1 same-rollout audit."""
from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.optimize import minimize
import torch

from algorithms.ri_gmappo.drtp_topology_sampler import ALL_GROUPS, NOMINAL_GROUP
from algorithms.ri_gmappo.tgtr_ppo import _batch_tensors, _forward, _metrics, _surrogate_per_graph, flatten_tensors


GROUP_MASSES = np.asarray([0.5] + [1.0 / 12.0] * 6, dtype=np.float64)


def _positive_cosine(left: np.ndarray, right: np.ndarray, relative_epsilon: float) -> float:
    scale = max(float(np.linalg.norm(left)), float(np.linalg.norm(right)))
    if not np.isfinite(scale) or scale == 0.0:
        return 0.0
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.clip(np.dot(left, right) / (denominator + relative_epsilon * scale * scale), 0.0, 1.0))


def _solve_weights(
    gradients: np.ndarray,
    anchor: np.ndarray,
    strength: float,
    masses: np.ndarray,
    relative_epsilon: float,
    ftol: float,
    max_iterations: int,
) -> tuple[np.ndarray, bool]:
    anchor_norm = float(np.linalg.norm(anchor))
    scale = max(anchor_norm, float(np.max(np.linalg.norm(gradients, axis=0))), np.finfo(float).tiny)
    gradients_n = gradients / scale
    anchor_n = anchor / scale
    anchor_norm_n = float(np.linalg.norm(anchor_n))

    def objective(weights: np.ndarray) -> float:
        proposal = gradients_n @ weights
        smooth_norm = float(np.sqrt(np.dot(proposal, proposal) + relative_epsilon**2))
        return float(np.dot(proposal, anchor_n) + strength * anchor_norm_n * smooth_norm)

    def jacobian(weights: np.ndarray) -> np.ndarray:
        proposal = gradients_n @ weights
        smooth_norm = float(np.sqrt(np.dot(proposal, proposal) + relative_epsilon**2))
        return gradients_n.T @ anchor_n + strength * anchor_norm_n * (gradients_n.T @ proposal) / smooth_norm

    result = minimize(
        objective,
        masses,
        method="SLSQP",
        jac=jacobian,
        bounds=[(0.0, 1.0)] * masses.size,
        constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0), "jac": lambda w: np.ones_like(w)}],
        options={"ftol": ftol, "maxiter": max_iterations, "disp": False},
    )
    weights = np.asarray(result.x, dtype=np.float64)
    valid = bool(
        result.success and np.all(np.isfinite(weights)) and np.min(weights) >= -1e-9
        and abs(float(np.sum(weights)) - 1.0) <= 1e-8
    )
    if not valid:
        return masses.copy(), False
    weights = np.clip(weights, 0.0, 1.0)
    weights /= float(np.sum(weights))
    return weights, True


def frozen_racg_direction(
    split_a: np.ndarray,
    split_b: np.ndarray,
    entropy_gradient: np.ndarray,
    *,
    maximum_strength: float = 0.5,
    correction_cap: float = 0.5,
    relative_epsilon: float = 1e-12,
    solver_ftol: float = 1e-12,
    solver_max_iterations: int = 256,
) -> dict[str, Any]:
    split_a = np.asarray(split_a, dtype=np.float64)
    split_b = np.asarray(split_b, dtype=np.float64)
    entropy_gradient = np.asarray(entropy_gradient, dtype=np.float64)
    if split_a.shape != split_b.shape or split_a.ndim != 2 or split_a.shape[1] != len(ALL_GROUPS):
        raise ValueError("RACG split gradients must have shape [parameters, 7]")
    if entropy_gradient.shape != (split_a.shape[0],):
        raise ValueError("entropy gradient has the wrong shape")
    if not all(np.all(np.isfinite(value)) for value in (split_a, split_b, entropy_gradient)):
        raise ValueError("RACG gradients must be finite")

    agreements = np.asarray([
        _positive_cosine(split_a[:, index], split_b[:, index], relative_epsilon)
        for index in range(len(ALL_GROUPS))
    ])
    pooled_a, pooled_b = split_a @ GROUP_MASSES, split_b @ GROUP_MASSES
    pooled_agreement = _positive_cosine(pooled_a, pooled_b, relative_epsilon)
    reliability = float(np.clip(pooled_agreement * np.dot(GROUP_MASSES, agreements), 0.0, 1.0))
    group_mean = 0.5 * (split_a + split_b)
    surrogate_anchor = group_mean @ GROUP_MASSES
    ordinary = surrogate_anchor + entropy_gradient
    shrunk = agreements[np.newaxis, :] * group_mean + (1.0 - agreements[np.newaxis, :]) * surrogate_anchor[:, np.newaxis]
    strength = float(maximum_strength * reliability)
    weights = GROUP_MASSES.copy()
    solver_ok = True
    fallback = strength == 0.0 or float(np.linalg.norm(surrogate_anchor)) == 0.0
    correction = np.zeros_like(ordinary)
    if not fallback:
        weights, solver_ok = _solve_weights(
            shrunk, surrogate_anchor, strength, GROUP_MASSES, relative_epsilon, solver_ftol, solver_max_iterations
        )
        fallback = not solver_ok
    if not fallback:
        proposal = shrunk @ weights
        proposal_norm = float(np.linalg.norm(proposal))
        scale = max(float(np.linalg.norm(surrogate_anchor)), float(np.max(np.linalg.norm(shrunk, axis=0))), np.finfo(float).tiny)
        correction = strength * float(np.linalg.norm(surrogate_anchor)) * proposal / max(proposal_norm, relative_epsilon * scale)
        ordinary_norm, correction_norm = float(np.linalg.norm(ordinary)), float(np.linalg.norm(correction))
        if ordinary_norm == 0.0 or correction_norm == 0.0:
            correction = np.zeros_like(ordinary)
        else:
            correction *= min(1.0, correction_cap * ordinary_norm / correction_norm)
    direction = ordinary + correction
    if not np.all(np.isfinite(direction)):
        direction, correction, weights, strength, solver_ok, fallback = ordinary.copy(), np.zeros_like(ordinary), GROUP_MASSES.copy(), 0.0, False, True
    return {
        "direction": direction,
        "ordinary": ordinary,
        "correction": correction,
        "group_agreement": agreements,
        "pooled_agreement": pooled_agreement,
        "reliability": reliability,
        "strength": strength,
        "weights": weights,
        "solver_ok": solver_ok,
        "ordinary_fallback": fallback,
    }


def _flatten_batched_gradients(raw: tuple[torch.Tensor | None, ...], parameters: list[torch.nn.Parameter]) -> torch.Tensor:
    rows = raw[0].shape[0] if raw and raw[0] is not None else 14
    pieces = []
    for gradient, parameter in zip(raw, parameters):
        pieces.append(
            torch.zeros((rows, parameter.numel()), dtype=parameter.dtype, device=parameter.device)
            if gradient is None else gradient.detach().reshape(rows, -1)
        )
    return torch.cat(pieces, dim=1)


def _assign_descent_gradient(parameters: list[torch.nn.Parameter], ascent_direction: torch.Tensor) -> None:
    cursor = 0
    for parameter in parameters:
        count = parameter.numel()
        value = -ascent_direction[cursor:cursor + count].reshape_as(parameter)
        parameter.grad = value.detach().clone()
        cursor += count
    if cursor != ascent_direction.numel():
        raise ValueError("RACG flat direction has the wrong parameter count")


def racg_update_policy(agent, optimizer, batch: dict, cfg, device: torch.device, formula: dict) -> dict[str, Any]:
    tensors = _batch_tensors(batch, device)
    if tensors["num_graphs"] != 1536:
        raise ValueError("RACG C1 requires one complete 24x64 rollout")
    for group in ALL_GROUPS:
        for split in ("design", "certificate"):
            expected = 384 if group == NOMINAL_GROUP else 64
            actual = int(np.sum((tensors["groups"] == group) & (tensors["splits"] == split)))
            if actual != expected:
                raise ValueError(f"RACG batch contract violation for {group}/{split}: {actual} != {expected}")

    actor_parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    rows = []
    started = time.perf_counter()
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    for epoch in range(1, int(cfg.ppo_epochs) + 1):
        actor_before = [parameter.detach().clone() for parameter in actor_parameters]
        with torch.no_grad():
            reference_logits, reference_selected, _, _, _, _ = _forward(agent, tensors)
            reference_surrogate = _surrogate_per_graph(reference_selected, tensors, cfg.clip_coef)

        _, selected, entropy, values, _, _ = _forward(agent, tensors)
        surrogate = _surrogate_per_graph(selected, tensors, cfg.clip_coef)
        objectives = []
        for split in ("design", "certificate"):
            for group in ALL_GROUPS:
                mask_np = (tensors["splits"] == split) & (tensors["groups"] == group)
                mask = torch.as_tensor(mask_np, dtype=torch.bool, device=device)
                objectives.append(surrogate[mask].mean())
        objective_vector = torch.stack(objectives)
        raw = torch.autograd.grad(
            objective_vector, actor_parameters,
            grad_outputs=torch.eye(14, dtype=objective_vector.dtype, device=device),
            retain_graph=True, allow_unused=True, is_grads_batched=True,
        )
        flat = _flatten_batched_gradients(raw, actor_parameters).double().cpu().numpy()
        split_a, split_b = flat[:7].T, flat[7:].T
        entropy_objective = cfg.entropy_coef * entropy.mean()
        entropy_raw = torch.autograd.grad(entropy_objective, actor_parameters, retain_graph=True, allow_unused=True)
        entropy_flat = flatten_tensors([
            torch.zeros_like(parameter).reshape(-1) if gradient is None else gradient.detach().reshape(-1)
            for parameter, gradient in zip(actor_parameters, entropy_raw)
        ]).double().cpu().numpy()
        result = frozen_racg_direction(
            split_a, split_b, entropy_flat,
            maximum_strength=float(formula["maximum_strength"]), correction_cap=float(formula["correction_cap"]),
            relative_epsilon=float(formula["relative_epsilon"]), solver_ftol=float(formula["solver_ftol"]),
            solver_max_iterations=int(formula["solver_max_iterations"]),
        )
        direction = torch.as_tensor(result["direction"], dtype=actor_parameters[0].dtype, device=device)
        ordinary = torch.as_tensor(result["ordinary"], dtype=actor_parameters[0].dtype, device=device)
        correction = torch.as_tensor(result["correction"], dtype=actor_parameters[0].dtype, device=device)
        direction_norm = float(torch.linalg.vector_norm(direction).cpu())
        ordinary_norm = float(torch.linalg.vector_norm(ordinary).cpu())
        correction_norm = float(torch.linalg.vector_norm(correction).cpu())

        value_loss = 0.5 * (tensors["returns"] - values).pow(2).mean()
        optimizer.zero_grad(set_to_none=True)
        (cfg.value_coef * value_loss).backward()
        _assign_descent_gradient(actor_parameters, direction)
        grad_norm = float(torch.nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm).detach().cpu())
        optimizer.step()
        displacement = flatten_tensors([
            parameter.detach() - before for parameter, before in zip(actor_parameters, actor_before)
        ])
        certificate = _metrics(agent, tensors, reference_logits, reference_surrogate, cfg.clip_coef, "certificate")
        rows.append({
            "epoch": epoch,
            "group_agreement": {group: float(result["group_agreement"][index]) for index, group in enumerate(ALL_GROUPS)},
            "pooled_agreement": float(result["pooled_agreement"]),
            "reliability": float(result["reliability"]),
            "strength": float(result["strength"]),
            "weights": {group: float(result["weights"][index]) for index, group in enumerate(ALL_GROUPS)},
            "solver_ok": bool(result["solver_ok"]),
            "ordinary_fallback": bool(result["ordinary_fallback"]),
            "ordinary_direction_l2": ordinary_norm,
            "correction_l2": correction_norm,
            "correction_ratio": correction_norm / max(ordinary_norm, np.finfo(float).tiny),
            "racg_direction_l2": direction_norm,
            "nonfreeze_ratio": direction_norm / max(ordinary_norm, np.finfo(float).tiny),
            "realized_actor_displacement_l2": float(torch.linalg.vector_norm(displacement).cpu()),
            "preclip_joint_gradient_l2": grad_norm,
            "certificate": certificate,
        })
    return {
        "epochs": rows,
        "wall_seconds": time.perf_counter() - started,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
        "solver_fallback_count": sum(not row["solver_ok"] for row in rows),
        "ordinary_fallback_count": sum(row["ordinary_fallback"] for row in rows),
        "zero_realized_step_count": sum(row["realized_actor_displacement_l2"] <= 1e-12 for row in rows),
    }
