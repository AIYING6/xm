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

from envs.lag_role_graph_wrapper import LAGRoleGraphWrapper


DEFAULT_REPORT = ROOT / "docs" / "lag_role_graph_wrapper_test.md"
DEFAULT_CSV = ROOT / "results" / "lag_role_graph_wrapper_test.csv"


@dataclass
class FakeSim:
    pos: np.ndarray
    vel: np.ndarray
    rpy: np.ndarray
    body_vel: np.ndarray

    @property
    def state_var(self):
        return list(range(12))

    def get_position(self):
        return self.pos

    def get_velocity(self):
        return self.vel

    def get_rpy(self):
        return self.rpy

    def get_property_values(self, _state_var):
        return np.asarray([0.0, 0.0, 0.0, *self.rpy, *self.vel, *self.body_vel], dtype=np.float32)


class FakeLAGEnv:
    def __init__(self):
        self.ego_ids = ["A0100", "A0200"]
        self.enm_ids = ["B0100", "B0200"]
        self.num_agents = 4
        self.reset_count = 0
        self.step_count = 0
        self.closed = False
        self.agents = {}
        self.reset()

    def reset(self):
        self.reset_count += 1
        self.step_count = 0
        self.agents = {
            "A0100": FakeSim(np.array([-1000.0, -500.0, 3200.0], dtype=np.float32), np.array([180.0, 15.0, -2.0], dtype=np.float32), np.array([0.01, 0.02, 0.08], dtype=np.float32), np.array([181.0, 1.0, -2.0], dtype=np.float32)),
            "A0200": FakeSim(np.array([-900.0, 600.0, 3180.0], dtype=np.float32), np.array([176.0, -10.0, 1.0], dtype=np.float32), np.array([0.02, 0.01, -0.05], dtype=np.float32), np.array([176.3, -0.5, 1.0], dtype=np.float32)),
            "B0100": FakeSim(np.array([1100.0, -650.0, 3300.0], dtype=np.float32), np.array([-175.0, 8.0, -1.0], dtype=np.float32), np.array([-0.01, 0.03, 3.09], dtype=np.float32), np.array([175.2, 0.0, -1.0], dtype=np.float32)),
            "B0200": FakeSim(np.array([1250.0, 650.0, 3250.0], dtype=np.float32), np.array([-181.0, -14.0, 1.0], dtype=np.float32), np.array([0.0, -0.02, -3.05], dtype=np.float32), np.array([181.5, 0.0, 1.0], dtype=np.float32)),
        }
        return {"reset_count": self.reset_count}

    def step(self, action):
        self.step_count += 1
        for sim in self.agents.values():
            sim.pos = sim.pos + sim.vel * 0.1
        return {"action": action, "step_count": self.step_count}

    def close(self):
        self.closed = True


def check(condition: bool, name: str, detail: str, rows: list[dict]) -> None:
    rows.append({"check": name, "status": "ok" if condition else "failed", "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


def run_checks() -> list[dict]:
    rows: list[dict] = []
    env = FakeLAGEnv()
    wrapper = LAGRoleGraphWrapper(env, comm_radius=1500.0)
    reset_result, reset_graph = wrapper.reset()
    check(reset_result["reset_count"] == 2, "reset_passthrough", str(reset_result), rows)
    check(reset_graph.node_feat.shape == (4, 15), "reset_node_shape", str(reset_graph.node_feat.shape), rows)
    check(reset_graph.edge_feat.shape == (4, 4, 13), "reset_edge_shape", str(reset_graph.edge_feat.shape), rows)
    check(reset_graph.adj.shape == (4, 4), "reset_adj_shape", str(reset_graph.adj.shape), rows)
    check(reset_graph.role.tolist() == [0, 0, 1, 1], "reset_role", str(reset_graph.role.tolist()), rows)
    step_result, step_graph = wrapper.step(np.zeros((4, 4), dtype=np.int64))
    check(step_result["step_count"] == 1, "step_passthrough", f"step_count={step_result['step_count']}", rows)
    check(wrapper.last_graph is step_graph, "last_graph_updated", "step graph cached", rows)
    check(not np.allclose(reset_graph.node_feat[:, 0], step_graph.node_feat[:, 0]), "step_state_refresh", "altitude feature changed after step", rows)
    check(not np.isnan(step_graph.node_feat).any() and not np.isnan(step_graph.edge_feat).any(), "no_nan", "no NaN", rows)
    check(not np.isinf(step_graph.node_feat).any() and not np.isinf(step_graph.edge_feat).any(), "no_inf", "no Inf", rows)
    wrapper.close()
    check(env.closed, "close_passthrough", "env closed", rows)
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
        "# LAG Role Graph Wrapper Test",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Validate a thin reset/step wrapper that exposes EA-RG-MAPPO-S graph tensors from a LAG-like environment.",
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
        lines.append(f"| `{row['check']}` | {row['status']} | {row['detail']} |")
    lines.append("")
    out_report.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test LAG role graph wrapper on fake LAG-like env.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = run_checks()
    write_csv(rows, args.csv)
    write_report(rows, args.report)
    print(args.report)
    print(args.csv)


if __name__ == "__main__":
    main()
