from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.lag_role_graph_adapter import build_lag_role_graph, states_from_lag_env


DEFAULT_REPORT = ROOT / "docs" / "lag_role_graph_adapter_test.md"
DEFAULT_CSV = ROOT / "results" / "lag_role_graph_adapter_test.csv"


@dataclass
class FakeSim:
    pos: tuple[float, float, float]
    vel: tuple[float, float, float]
    rpy: tuple[float, float, float]
    body_vel: tuple[float, float, float]
    is_alive: bool = True

    @property
    def state_var(self):
        return list(range(12))

    def get_position(self):
        return np.asarray(self.pos, dtype=np.float32)

    def get_velocity(self):
        return np.asarray(self.vel, dtype=np.float32)

    def get_rpy(self):
        return np.asarray(self.rpy, dtype=np.float32)

    def get_property_values(self, _state_var):
        return np.asarray([0.0, 0.0, 0.0, *self.rpy, *self.vel, *self.body_vel], dtype=np.float32)


class FakeLAGEnv:
    def __init__(self):
        self.agents = {
            "A0100": FakeSim((-1000.0, -500.0, 3200.0), (180.0, 15.0, -2.0), (0.01, 0.02, 0.08), (181.0, 1.0, -2.0)),
            "A0200": FakeSim((-900.0, 600.0, 3180.0), (176.0, -10.0, 1.0), (0.02, 0.01, -0.05), (176.3, -0.5, 1.0)),
            "B0100": FakeSim((1100.0, -650.0, 3300.0), (-175.0, 8.0, -1.0), (-0.01, 0.03, 3.09), (175.2, 0.0, -1.0)),
            "B0200": FakeSim((1250.0, 650.0, 3250.0), (-181.0, -14.0, 1.0), (0.0, -0.02, -3.05), (181.5, 0.0, 1.0)),
        }
        self.ego_ids = ["A0100", "A0200"]
        self.enm_ids = ["B0100", "B0200"]
        self.num_agents = 4


def check(condition: bool, name: str, detail: str, rows: list[dict]) -> None:
    rows.append({"check": name, "status": "ok" if condition else "failed", "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


def run_checks() -> list[dict]:
    rows: list[dict] = []
    env = FakeLAGEnv()
    states = states_from_lag_env(env)
    check(len(states) == 4, "state_count", f"states={len(states)}", rows)
    check([s.role for s in states] == [0, 0, 1, 1], "role_assignment", str([s.role for s in states]), rows)

    previous_team_edges = -1
    for radius in [500.0, 1500.0, 4000.0]:
        node_feat, edge_feat, adj, role = build_lag_role_graph(states, radius)
        team_mask = (role[:, None] == role[None, :]) & (~np.eye(len(role), dtype=bool))
        enemy_mask = role[:, None] != role[None, :]
        team_edges = int(np.sum((adj > 0.5) & team_mask))
        enemy_edges = int(np.sum((adj > 0.5) & enemy_mask))
        check(node_feat.shape == (4, 15), f"node_shape_r{radius:g}", str(node_feat.shape), rows)
        check(edge_feat.shape == (4, 4, 13), f"edge_shape_r{radius:g}", str(edge_feat.shape), rows)
        check(adj.shape == (4, 4), f"adj_shape_r{radius:g}", str(adj.shape), rows)
        check(np.all(np.diag(adj) > 0.5), f"self_edges_r{radius:g}", str(np.diag(adj).tolist()), rows)
        check(enemy_edges == 8, f"enemy_edges_r{radius:g}", f"enemy_edges={enemy_edges}", rows)
        check(team_edges >= previous_team_edges, f"team_monotonic_r{radius:g}", f"team_edges={team_edges}", rows)
        check(not np.isnan(node_feat).any() and not np.isnan(edge_feat).any() and not np.isnan(adj).any(), f"no_nan_r{radius:g}", "no NaN", rows)
        check(not np.isinf(node_feat).any() and not np.isinf(edge_feat).any() and not np.isinf(adj).any(), f"no_inf_r{radius:g}", "no Inf", rows)
        previous_team_edges = team_edges
    return rows


def write_csv(rows: list[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict], out_report: Path) -> None:
    out_report.parent.mkdir(parents=True, exist_ok=True)
    failed = [row for row in rows if row["status"] != "ok"]
    lines = [
        "# LAG Role Graph Adapter Test",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Validate the duck-typed adapter that converts LAG-like simulator states into EA-RG-MAPPO-S role graph tensors.",
        "This test uses fake simulator objects and does not claim real JSBSim validation.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Checks | {len(rows)} |",
        f"| Failed | {len(failed)} |",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['check']} | {row['status']} | `{row['detail']}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "```text",
            "The adapter can already be tested without JSBSim by using LAG-like get_position/get_velocity/get_rpy methods.",
            "The next real migration step is to run the same adapter on a real MultipleCombatEnv reset after JSBSim data is available.",
            "```",
            "",
        ]
    )
    out_report.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test LAG role graph adapter with fake simulator objects.")
    parser.add_argument("--out-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = run_checks()
    write_csv(rows, args.out_csv)
    write_report(rows, args.out_report)
    print(args.out_report)
    print(args.out_csv)


if __name__ == "__main__":
    main()
