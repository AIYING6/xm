"""Legal-controller feasibility audit for the public-board capacity task."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig
from envs.multi_threat_public_board_capacity_defense_env import MultiThreatPublicBoardCapacityDefenseEnv
POLICIES = ("parallel", "concentrated")
SEEDS = tuple(range(109001, 109025))
OUT = ROOT / "results" / "development" / "multi_threat_public_board_g0"
BASE_DIM = 19
CELLS = (
    {"branch_step": 10, "red_initial_lateral": 9500.0, "asset_lateral": 15000.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 13500.0},
    {"branch_step": 12, "red_initial_lateral": 8500.0, "asset_lateral": 15000.0},
)
JITTER = {"red_center_y_jitter": 1000.0, "approach_speed_jitter": 12.0, "branch_step_jitter": 2}


def action_from_relative(obs: np.ndarray, relative: np.ndarray) -> int:
    heading = math.atan2(float(obs[5]), float(obs[6]))
    desired = math.atan2(float(relative[1]), float(relative[0]))
    error = math.atan2(math.sin(desired - heading), math.cos(desired - heading))
    turn = int(np.sign(error)) if abs(error) > 0.035 else 0
    climb = int(np.sign(float(relative[2]))) if abs(float(relative[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def legal_actions(obs: np.ndarray, policy: str) -> np.ndarray:
    """Decode only the public board carried in actor observations."""
    board = obs[0, BASE_DIM:]
    blue = board[:9].reshape(3, 3) * 50_000.0
    red = board[9:15].reshape(2, 3) * 50_000.0
    alive = board[15:17] < 0.5
    primary = 0 if alive[0] else 1
    secondary = 1 if primary == 0 else 0
    goals = [red[secondary] if policy == "parallel" else red[primary], 0.5 * (blue[0] + blue[2]), red[primary]]
    return np.asarray([action_from_relative(obs[agent], goals[agent] - blue[agent]) for agent in range(3)], dtype=np.int64)


def run(seed: int, cell: int, policy: str) -> dict[str, object]:
    env = MultiThreatPublicBoardCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=seed, **CELLS[cell], **JITTER))
    obs, _, _ = env.reset()
    total, info = 0.0, {}
    while not env.base.done:
        obs, _, _, rewards, _, info = env.step(legal_actions(obs, policy))
        total += float(np.mean(rewards))
    return {
        "seed": seed, "cell": cell, "policy": policy, "return": total,
        "defense_success": int(info.get("defense_success", 0.0) > 0.5),
        "asset_breach": int(info.get("asset_breach", 0.0) > 0.5),
        "timeout": int(info.get("timeout", 0.0) > 0.5),
        "collision": int(info.get("collision", 0.0) > 0.5),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("G0 requires --execute")
    if (args.out_dir / "raw_episode_metrics.csv").exists():
        raise FileExistsError(f"Refusing to overwrite {args.out_dir}")
    rows = [run(seed, cell, policy) for cell in range(len(CELLS)) for seed in SEEDS for policy in POLICIES]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    success = {policy: sum(row["defense_success"] for row in rows if row["policy"] == policy) for policy in POLICIES}
    payload = {
        "protocol": "MULTI-THREAT-PUBLIC-BOARD-G0-V1",
        "artifact_class": "DEVELOPMENT_ONLY_LEGAL_CONTROLLER_FEASIBILITY",
        "actor_information": "explicit public board plus each actor local state; no environment-state reads",
        "training_started": False,
        "canonical_data_used": False,
        "success_by_policy": success,
        "parallel_minus_concentrated": success["parallel"] - success["concentrated"],
        "verdict": "EVIDENCE_REVIEW_REQUIRED",
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
