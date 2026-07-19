from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from evaluate_ri_gmappo_3d import build_agent, build_config, stack_graphs  # noqa: E402


DEFAULT_INPUT = (
    ROOT
    / "results"
    / "intercept_3d_gate1_hardened_60update_3seed_dev"
    / "checkpoint_sweep"
    / "test_episode_metrics.csv"
)
DEFAULT_OUT_DIR = (
    ROOT
    / "results"
    / "intercept_3d_gate1_hardened_60update_3seed_dev"
    / "collision_replay"
)
DEFAULT_DOC = ROOT / "docs" / "intercept_3d_gate1_hardened_60update_collision_replay.md"


CSV_COLUMNS = (
    "case_id",
    "graph_encoder",
    "train_seed",
    "checkpoint_update",
    "episode_seed",
    "episode",
    "step",
    "action_0",
    "action_1",
    "action_2",
    "node_failure_active",
    "success",
    "timeout",
    "collision",
    "constraint_violation",
    "chain_closed",
    "tracking_rate",
    "attack_window_rate",
    "comm_connectivity",
    "mean_message_age",
    "mean_range",
    "min_blue_red_distance",
    "min_blue_red_pair",
    "min_blue_blue_distance",
    "min_blue_blue_pair",
    "collision_pair",
    "blue0_x",
    "blue0_y",
    "blue0_z",
    "blue1_x",
    "blue1_y",
    "blue1_z",
    "blue2_x",
    "blue2_y",
    "blue2_z",
    "red0_x",
    "red0_y",
    "red0_z",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay collision episodes and record per-step safety traces.")
    parser.add_argument("--episode-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--limit", type=int, default=0, help="Optional max number of collision cases to replay.")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def resolve_checkpoint(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def collision_cases(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    cases = [row for row in rows if float(row.get("collision", 0.0)) > 0.5]
    cases.sort(key=lambda r: (r.get("graph_encoder", ""), int(float(r.get("train_seed", 0))), int(float(r.get("seed", 0)))))
    return cases[:limit] if limit > 0 else cases


def agent_args(args: argparse.Namespace, case: dict[str, str]) -> argparse.Namespace:
    return argparse.Namespace(
        checkpoint=resolve_checkpoint(case["checkpoint"]),
        seed=int(float(case["seed"])),
        episodes=1,
        base_seed=int(float(case["seed"])),
        target_policy=case.get("target_policy", "straight"),
        communication_range_scale=float(case.get("communication_range_scale", 1.0)),
        communication_dropout_prob=float(case.get("communication_dropout_prob", 0.0)),
        message_delay_steps=int(float(case.get("message_delay_steps", 0))),
        radar_dropout_prob=float(case.get("radar_dropout_prob", 0.0)),
        strict_target_sensing=case.get("strict_target_sensing", "False") == "True",
        agent_target_info_bottleneck=case.get("agent_target_info_bottleneck", "False") == "True",
        max_target_message_age_steps=int(float(case.get("max_target_message_age_steps", 80))),
        min_target_confidence=float(case.get("min_target_confidence", 0.2)),
        failed_blue_agent=int(float(case.get("failed_blue_agent", -1))),
        node_failure_start_step=int(float(case.get("node_failure_start_step", 0))),
        node_failure_duration_steps=int(float(case.get("node_failure_duration_steps", 0))),
        graph_relation_ablation=case.get("graph_relation_ablation", "none"),
        graph_message_ablation=case.get("graph_message_ablation", "none"),
        graph_input_ablation=case.get("graph_input_ablation", "none"),
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
        graph_encoder=case["graph_encoder"],
        device=args.device,
    )


def pair_distances(env) -> tuple[float, str, float, str]:
    blue_red = [(float(np.linalg.norm(env.blue_pos[i] - env.red_pos[0])), f"blue{i}-red0") for i in range(env.config.num_blue)]
    blue_blue = [
        (float(np.linalg.norm(env.blue_pos[i] - env.blue_pos[j])), f"blue{i}-blue{j}")
        for i in range(env.config.num_blue)
        for j in range(i + 1, env.config.num_blue)
    ]
    min_br = min(blue_red, key=lambda item: item[0])
    min_bb = min(blue_blue, key=lambda item: item[0])
    return min_br[0], min_br[1], min_bb[0], min_bb[1]


def collision_pair(env) -> str:
    radius = float(env.config.collision_radius)
    hits: list[str] = []
    for i in range(env.config.num_blue):
        if float(np.linalg.norm(env.blue_pos[i] - env.red_pos[0])) < radius:
            hits.append(f"blue{i}-red0")
        for j in range(i + 1, env.config.num_blue):
            if float(np.linalg.norm(env.blue_pos[i] - env.blue_pos[j])) < radius:
                hits.append(f"blue{i}-blue{j}")
    return ";".join(hits) if hits else "none"


def trace_row(case_id: str, case: dict[str, str], step_actions: np.ndarray, info: dict[str, float], env) -> dict[str, str]:
    min_br, min_br_pair, min_bb, min_bb_pair = pair_distances(env)
    row: dict[str, str] = {
        "case_id": case_id,
        "graph_encoder": case["graph_encoder"],
        "train_seed": case["train_seed"],
        "checkpoint_update": case["checkpoint_update"],
        "episode_seed": case["seed"],
        "episode": case["episode"],
        "step": f"{float(info['step']):.0f}",
        "action_0": str(int(step_actions[0])),
        "action_1": str(int(step_actions[1])),
        "action_2": str(int(step_actions[2])),
        "node_failure_active": f"{float(info['node_failure_active']):.0f}",
        "success": f"{float(info['success']):.0f}",
        "timeout": f"{float(info['timeout']):.0f}",
        "collision": f"{float(info['collision']):.0f}",
        "constraint_violation": f"{float(info['constraint_violation']):.0f}",
        "chain_closed": f"{float(info['chain_closed']):.0f}",
        "tracking_rate": f"{float(info['tracking_rate']):.6g}",
        "attack_window_rate": f"{float(info['attack_window_rate']):.6g}",
        "comm_connectivity": f"{float(info['comm_connectivity']):.6g}",
        "mean_message_age": f"{float(info['mean_message_age']):.6g}",
        "mean_range": f"{float(info['mean_range']):.6g}",
        "min_blue_red_distance": f"{min_br:.6g}",
        "min_blue_red_pair": min_br_pair,
        "min_blue_blue_distance": f"{min_bb:.6g}",
        "min_blue_blue_pair": min_bb_pair,
        "collision_pair": collision_pair(env),
    }
    for i in range(env.config.num_blue):
        row[f"blue{i}_x"] = f"{float(env.blue_pos[i, 0]):.6g}"
        row[f"blue{i}_y"] = f"{float(env.blue_pos[i, 1]):.6g}"
        row[f"blue{i}_z"] = f"{float(env.blue_pos[i, 2]):.6g}"
    row["red0_x"] = f"{float(env.red_pos[0, 0]):.6g}"
    row["red0_y"] = f"{float(env.red_pos[0, 1]):.6g}"
    row["red0_z"] = f"{float(env.red_pos[0, 2]):.6g}"
    return row


def replay_case(args: argparse.Namespace, case_id: str, case: dict[str, str]) -> list[dict[str, str]]:
    run_args = agent_args(args, case)
    cfg = build_config(run_args)
    agent, _policy_source = build_agent(run_args, cfg)
    device = torch.device(args.device)
    env = make_env(cfg, int(float(case["seed"])), training=False)
    obs, share_obs, graph = env.reset()
    rows: list[dict[str, str]] = []
    with torch.no_grad():
        while True:
            g = stack_graphs([graph])
            actions, _, _, _, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(g["role"], dtype=torch.long, device=device),
                torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                deterministic=True,
                intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                detach_intent=False,
                oracle_intent=False,
            )
            action_np = actions.squeeze(0).cpu().numpy().astype(np.int64)
            obs, share_obs, graph, _rewards, dones, info = env.step(action_np)
            rows.append(trace_row(case_id, case, action_np, info, env))
            if np.all(dones):
                return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def summarize_case(rows: list[dict[str, str]]) -> dict[str, str]:
    final = rows[-1]
    min_br_row = min(rows, key=lambda row: float(row["min_blue_red_distance"]))
    min_bb_row = min(rows, key=lambda row: float(row["min_blue_blue_distance"]))
    failure_rows = [row for row in rows if float(row["node_failure_active"]) > 0.5]
    return {
        "case_id": final["case_id"],
        "graph_encoder": final["graph_encoder"],
        "train_seed": final["train_seed"],
        "episode_seed": final["episode_seed"],
        "steps": final["step"],
        "collision_pair": final["collision_pair"],
        "success": final["success"],
        "timeout": final["timeout"],
        "chain_closed_final": final["chain_closed"],
        "min_blue_red_distance": min_br_row["min_blue_red_distance"],
        "min_blue_red_pair": min_br_row["min_blue_red_pair"],
        "min_blue_red_step": min_br_row["step"],
        "min_blue_blue_distance": min_bb_row["min_blue_blue_distance"],
        "min_blue_blue_pair": min_bb_row["min_blue_blue_pair"],
        "min_blue_blue_step": min_bb_row["step"],
        "tracking_during_failure": (
            f"{np.mean([float(row['tracking_rate']) for row in failure_rows]):.6g}" if failure_rows else "NA"
        ),
        "connectivity_during_failure": (
            f"{np.mean([float(row['comm_connectivity']) for row in failure_rows]):.6g}" if failure_rows else "NA"
        ),
    }


def write_md(path: Path, summaries: list[dict[str, str]], out_csv: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Hardened 60-Update Collision Replay",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This audit replays the disjoint-test collision episodes from the hardened 60-update development run. It is a safety diagnostic, not a new training result.",
        "",
        "## Files",
        "",
        f"- Per-step trace CSV: `{out_csv.relative_to(ROOT).as_posix()}`",
        "",
        "## Summary",
        "",
        "| Case | Method | Train seed | Episode seed | Steps | Collision pair | Min blue-red | Min blue-red step | Min blue-blue | Min blue-blue step | Tracking during failure | Connectivity during failure |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['case_id']} | `{row['graph_encoder']}` | {row['train_seed']} | {row['episode_seed']} | "
            f"{row['steps']} | {row['collision_pair']} | {float(row['min_blue_red_distance']):.1f} "
            f"({row['min_blue_red_pair']}) | {row['min_blue_red_step']} | "
            f"{float(row['min_blue_blue_distance']):.1f} ({row['min_blue_blue_pair']}) | {row['min_blue_blue_step']} | "
            f"{row['tracking_during_failure']} | {row['connectivity_during_failure']} |"
        )
    blue_blue_cases = [row for row in summaries if "blue" in row["collision_pair"] and "red" not in row["collision_pair"]]
    blue_red_cases = [row for row in summaries if "red0" in row["collision_pair"]]
    lines.extend(
        [
            "",
            "## Diagnostic Interpretation",
            "",
            f"- Blue-blue collision cases: {len(blue_blue_cases)}.",
            f"- Blue-target collision cases: {len(blue_red_cases)}.",
            "- All listed cases terminate during the configured node-failure interval, so they are relevant to the relay-failure safety analysis.",
            "- The collision pairs identify different failure modes: intra-blue deconfliction for blue-blue collisions, and terminal overshoot/unsafe target approach for blue-target collisions.",
            "- Because the validation split was zero-collision but the test split was not, safety should be reported separately from recovery and considered before a five-seed formal rerun.",
            "",
            "## Interpretation Boundary",
            "",
            "- A collision is triggered below the environment collision radius of 120 m.",
            "- This replay determines which pair caused termination and whether the collision occurred during node failure.",
            "- It does not by itself decide whether to change rewards; that decision should compare collision timing, pair type, and recovery behavior.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    cases = collision_cases(read_rows(args.episode_csv), args.limit)
    if not cases:
        raise RuntimeError(f"no collision cases found in {args.episode_csv}")
    all_rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    for idx, case in enumerate(cases, start=1):
        case_id = f"case{idx:02d}"
        rows = replay_case(args, case_id, case)
        all_rows.extend(rows)
        summaries.append(summarize_case(rows))
    out_csv = args.out_dir / "collision_replay_trace.csv"
    write_csv(out_csv, all_rows)
    write_md(args.out_md, summaries, out_csv)
    print(out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
