"""Training-agnostic rollout collector for the v1.6R interface."""
from __future__ import annotations

from typing import Any

import numpy as np
import torch

from .continuous_guidance_policy import ContinuousGuidanceActor
from envs.v16r_env_adapter import V16RIntercept3DEnv


def collect_v16r_rollout(
    env: V16RIntercept3DEnv,
    actor: ContinuousGuidanceActor,
    horizon: int,
    device: torch.device | str = "cpu",
    graph_conditioned: bool = False,
    history_len: int = 1,
) -> dict[str, Any]:
    """Collect one rollout without updating parameters.

    The returned arrays preserve recipient and graph dimensions explicitly and
    include a reset mask for a future recurrent actor.  At present the actor is
    feed-forward, but the mask is recorded now so expiry/reset semantics cannot
    be added later as an afterthought.
    """
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if history_len <= 0:
        raise ValueError("history_len must be positive")
    obs, share_obs, graph = env.reset()
    obs_history = np.repeat(obs[:, None, :], history_len, axis=1)
    records: dict[str, list[np.ndarray]] = {key: [] for key in (
        "obs", "share_obs", "node", "edge", "relation_adj", "actions", "logp", "rewards", "dones", "reset_mask"
    )}
    actor.eval()
    for _ in range(horizon):
        with torch.no_grad():
            model_obs = obs_history.reshape(env.num_agents, -1)
            obs_t = torch.as_tensor(model_obs, dtype=torch.float32, device=device)
            if graph_conditioned:
                action_t, logp_t = actor(
                    obs_t,
                    torch.as_tensor(graph["node"], dtype=torch.float32, device=device),
                    torch.as_tensor(graph["relation_adj"], dtype=torch.float32, device=device),
                )
            else:
                action_t, logp_t = actor(obs_t)
        action = action_t.cpu().numpy().astype(np.float32)
        next_obs, next_share, next_graph, rewards, dones, _info = env.step(action)
        for key, value in (
            ("obs", model_obs), ("share_obs", share_obs), ("node", graph["node"]),
            ("edge", graph["edge"]), ("relation_adj", graph["relation_adj"]),
            ("actions", action), ("logp", logp_t.cpu().numpy()),
            ("rewards", rewards), ("dones", dones.reshape(-1)),
            ("reset_mask", np.ones(env.num_agents, dtype=np.float32) if bool(dones.all()) else np.zeros(env.num_agents, dtype=np.float32)),
        ):
            records[key].append(np.asarray(value).copy())
        obs, share_obs, graph = next_obs, next_share, next_graph
        obs_history = np.concatenate([obs_history[:, 1:, :], obs[:, None, :]], axis=1) if history_len > 1 else obs[:, None, :]
        if bool(dones.all()):
            obs, share_obs, graph = env.reset()

    batch = {key: np.stack(values, axis=0) for key, values in records.items()}
    batch["next_obs"] = np.asarray(obs_history.reshape(env.num_agents, -1), dtype=np.float32).copy()
    batch["next_share_obs"] = np.asarray(share_obs, dtype=np.float32).copy()
    batch["next_graph_node"] = np.asarray(graph["node"], dtype=np.float32).copy()
    batch["next_graph_edge"] = np.asarray(graph["edge"], dtype=np.float32).copy()
    batch["next_graph_relation_adj"] = np.asarray(graph["relation_adj"], dtype=np.float32).copy()
    return batch
