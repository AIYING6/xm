from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.lag_role_graph_adapter import build_lag_role_graph, states_from_lag_env


@dataclass(frozen=True)
class LAGRoleGraph:
    node_feat: np.ndarray
    edge_feat: np.ndarray
    adj: np.ndarray
    role: np.ndarray


class LAGRoleGraphWrapper:
    """Thin helper that exposes EA-RG graph tensors beside a LAG-like env."""

    def __init__(self, env: object, comm_radius: float):
        self.env = env
        self.comm_radius = float(comm_radius)
        self.last_graph: LAGRoleGraph | None = None

    def graph(self) -> LAGRoleGraph:
        node_feat, edge_feat, adj, role = build_lag_role_graph(
            states_from_lag_env(self.env),
            self.comm_radius,
        )
        self.last_graph = LAGRoleGraph(node_feat=node_feat, edge_feat=edge_feat, adj=adj, role=role)
        return self.last_graph

    def reset(self, *args: Any, **kwargs: Any) -> tuple[Any, LAGRoleGraph]:
        result = self.env.reset(*args, **kwargs)
        return result, self.graph()

    def step(self, action: Any) -> tuple[Any, LAGRoleGraph]:
        result = self.env.step(action)
        return result, self.graph()

    def close(self) -> Any:
        close = getattr(self.env, "close", None)
        if callable(close):
            return close()
        return None

