from __future__ import annotations

import argparse
import csv
import glob
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from evaluate_ri_gmappo_3d import build_agent, build_config, stack_graphs  # noqa: E402


DEFAULT_ROOT = ROOT / "results" / "intercept_3d_gate1_dropout030_bottleneck_5seed_formal" / "checkpoint_sweep"
CURVE_FIELDS = (
    "graph_encoder",
    "relative_step",
    "n_available",
    "n_episode",
    "tracking_rate_mean",
    "connectivity_mean",
    "chain_closed_mean",
    "recovery_cdf",
)
CASE_FIELDS = (
    "graph_encoder",
    "train_seed",
    "episode",
    "rollout_seed",
    "step",
    "relative_step",
    "node_failure_active",
    "tracking_rate",
    "comm_connectivity",
    "chain_closed",
    "attack_window_rate",
    "mean_message_age",
    "mean_range",
    "success",
    "timeout",
    "collision",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate failure-aligned mechanism curves and a representative case replay."
    )
    parser.add_argument("--episode-csv", type=Path, default=DEFAULT_ROOT / "test_episode_metrics.csv")
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_ROOT / "validation_selected_checkpoints.csv")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "intercept_3d_gate1_dropout030_bottleneck_mechanism")
    parser.add_argument("--docs-dir", type=Path, default=ROOT / "docs" / "intercept_3d_gate1_dropout030_bottleneck_mechanism")
    parser.add_argument("--methods", nargs="+", default=["no_graph", "single", "multi_relation"])
    parser.add_argument("--train-seeds", nargs="*", type=int, default=None)
    parser.add_argument("--episode-start", type=int, default=0)
    parser.add_argument("--episode-count", type=int, default=0, help="Optional per-method episode-index chunk size.")
    parser.add_argument("--curve-input-glob", default="", help="Aggregate existing chunk curve CSVs instead of replaying episodes.")
    parser.add_argument("--skip-case", action="store_true", help="Only write aggregate curves; skip representative-case replay.")
    parser.add_argument("--skip-plots", action="store_true", help="Write CSV and summary without matplotlib figures.")
    parser.add_argument("--baseline-method", default="single")
    parser.add_argument("--proposed-method", default="multi_relation")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--window-before", type=int, default=20)
    parser.add_argument("--window-after", type=int, default=220)
    parser.add_argument(
        "--max-episodes-per-method",
        type=int,
        default=0,
        help="Optional smoke/debug limit. Zero means use all episodes.",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def selection_map(rows: list[dict[str, str]]) -> dict[tuple[str, int], Path]:
    out: dict[tuple[str, int], Path] = {}
    for row in rows:
        ckpt = Path(row["selected_checkpoint"])
        out[(row["graph_encoder"], int(row["train_seed"]))] = ckpt if ckpt.is_absolute() else ROOT / ckpt
    return out


def run_args_from_episode(row: dict[str, str], checkpoint: Path, device: str) -> argparse.Namespace:
    def truth(value: str) -> bool:
        return str(value).lower() in {"1", "true", "yes"}

    return argparse.Namespace(
        checkpoint=checkpoint,
        seed=int(row["seed"]),
        episodes=1,
        base_seed=int(row["seed"]),
        target_policy=row["target_policy"],
        communication_range_scale=float(row["communication_range_scale"]),
        communication_dropout_prob=float(row["communication_dropout_prob"]),
        message_delay_steps=int(float(row["message_delay_steps"])),
        radar_dropout_prob=float(row["radar_dropout_prob"]),
        strict_target_sensing=truth(row["strict_target_sensing"]),
        agent_target_info_bottleneck=truth(row["agent_target_info_bottleneck"]),
        max_target_message_age_steps=int(float(row.get("max_target_message_age_steps", 80))),
        min_target_confidence=float(row.get("min_target_confidence", 0.2)),
        failed_blue_agent=int(float(row["failed_blue_agent"])),
        node_failure_start_step=int(float(row["node_failure_start_step"])),
        node_failure_duration_steps=int(float(row["node_failure_duration_steps"])),
        graph_relation_ablation=row["graph_relation_ablation"],
        graph_message_ablation=row["graph_message_ablation"],
        graph_input_ablation=row["graph_input_ablation"],
        graph_encoder=row["graph_encoder"],
        stochastic=False,
        allow_random_policy=False,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
        device=device,
    )


def replay_episode(
    template: dict[str, str],
    checkpoint: Path,
    device: str,
    agent_cache: dict[tuple[str, str, str, str, str], tuple[object, object]] | None = None,
) -> list[dict[str, float | int | str]]:
    args = run_args_from_episode(template, checkpoint, device)
    cache_key = (
        str(checkpoint.resolve()),
        template["graph_encoder"],
        template["strict_target_sensing"],
        template["agent_target_info_bottleneck"],
        device,
    )
    if agent_cache is not None and cache_key in agent_cache:
        cfg, agent = agent_cache[cache_key]
    else:
        cfg = build_config(args)
        agent, _policy_source = build_agent(args, cfg)
        if agent_cache is not None:
            agent_cache[cache_key] = (cfg, agent)
    torch_device = torch.device(device)
    env = make_env(cfg, args.seed, training=False)
    obs, share_obs, graph = env.reset()
    rows: list[dict[str, float | int | str]] = []
    recovered_so_far = 0.0
    failure_start = int(float(template["node_failure_start_step"]))

    with torch.no_grad():
        while True:
            g = stack_graphs([graph])
            actions, _, _, _, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs[None, ...], dtype=torch.float32, device=torch_device),
                torch.as_tensor(g["node_feat"], dtype=torch.float32, device=torch_device),
                torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=torch_device),
                torch.as_tensor(g["role"], dtype=torch.long, device=torch_device),
                torch.as_tensor(g["adj"], dtype=torch.float32, device=torch_device),
                torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=torch_device),
                relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=torch_device),
                deterministic=True,
                intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=torch_device),
                detach_intent=False,
                oracle_intent=False,
            )
            obs, share_obs, graph, _rewards, dones, info = env.step(actions.squeeze(0).cpu().numpy())
            step = int(float(info["step"]))
            if step >= failure_start and float(info.get("chain_closed", 0.0)) > 0.5:
                recovered_so_far = 1.0
            rows.append(
                {
                    "graph_encoder": template["graph_encoder"],
                    "train_seed": int(float(template["train_seed"])),
                    "episode": int(float(template["episode"])),
                    "rollout_seed": int(float(template["seed"])),
                    "step": step,
                    "relative_step": step - failure_start,
                    "node_failure_active": float(info.get("node_failure_active", 0.0)),
                    "tracking_rate": float(info.get("tracking_rate", 0.0)),
                    "comm_connectivity": float(info.get("comm_connectivity", 0.0)),
                    "chain_closed": float(info.get("chain_closed", 0.0)),
                    "attack_window_rate": float(info.get("attack_window_rate", 0.0)),
                    "mean_message_age": float(info.get("mean_message_age", 0.0)),
                    "mean_range": float(info.get("mean_range", 0.0)),
                    "success": float(info.get("success", 0.0)),
                    "timeout": float(info.get("timeout", 0.0)),
                    "collision": float(info.get("collision", 0.0)),
                    "recovered_so_far": recovered_so_far,
                }
            )
            if np.all(dones):
                return rows


def capped_recovery(row: dict[str, str]) -> float:
    failure_start = float(row["node_failure_start_step"])
    max_remaining = max(0.0, 260.0 - failure_start)
    if float(row["post_failure_chain_recovered"]) > 0.5:
        return min(float(row["post_failure_chain_recovery_steps"]), max_remaining)
    return max_remaining


def choose_case(
    rows: list[dict[str, str]],
    baseline_method: str,
    proposed_method: str,
) -> dict[str, dict[str, str]]:
    grouped: dict[tuple[int, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        grouped[(int(row["train_seed"]), int(row["episode"]))][row["graph_encoder"]] = row

    candidates: list[tuple[float, tuple[int, int], dict[str, dict[str, str]]]] = []
    for key, methods in grouped.items():
        if baseline_method not in methods or proposed_method not in methods:
            continue
        baseline = methods[baseline_method]
        proposed = methods[proposed_method]
        if float(proposed["post_failure_chain_recovered"]) <= 0.5:
            continue
        score = (capped_recovery(baseline) - capped_recovery(proposed)) + 100.0 * (
            float(proposed["post_failure_chain_recovered"]) - float(baseline["post_failure_chain_recovered"])
        )
        if score <= 0.0:
            continue
        candidates.append((score, key, methods))
    if not candidates:
        raise RuntimeError("No positive representative-case candidates found.")
    scores = np.asarray([item[0] for item in candidates], dtype=np.float64)
    median_score = float(np.median(scores))
    score, _key, methods = min(candidates, key=lambda item: abs(item[0] - median_score))
    methods["_selection"] = {
        "case_score": f"{score:.6g}",
        "median_positive_case_score": f"{median_score:.6g}",
        "n_positive_candidates": str(len(candidates)),
    }
    return methods


def aggregate_curves(
    replay_rows: list[dict[str, float | int | str]],
    methods: list[str],
    rel_min: int,
    rel_max: int,
) -> list[dict[str, str]]:
    buckets: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    episodes: dict[tuple[str, int, int, int], list[dict[str, float | int | str]]] = defaultdict(list)
    for row in replay_rows:
        rel = int(row["relative_step"])
        episodes[
            (
                str(row["graph_encoder"]),
                int(row["train_seed"]),
                int(row["episode"]),
                int(row["rollout_seed"]),
            )
        ].append(row)
        if rel < rel_min or rel > rel_max:
            continue
        key = (str(row["graph_encoder"]), rel)
        buckets[key]["tracking_rate"].append(float(row["tracking_rate"]))
        buckets[key]["comm_connectivity"].append(float(row["comm_connectivity"]))
        buckets[key]["chain_closed"].append(float(row["chain_closed"]))

    recovery_buckets: dict[tuple[str, int], list[float]] = defaultdict(list)
    for (method, _train_seed, _episode, _rollout_seed), rows in episodes.items():
        recovered_rel = None
        for row in rows:
            rel = int(row["relative_step"])
            if rel >= 0 and float(row["chain_closed"]) > 0.5:
                recovered_rel = rel
                break
        for rel in range(rel_min, rel_max + 1):
            recovery_buckets[(method, rel)].append(float(recovered_rel is not None and rel >= recovered_rel))

    output: list[dict[str, str]] = []
    for method in methods:
        for rel in range(rel_min, rel_max + 1):
            values = buckets.get((method, rel), {})
            n = len(values.get("tracking_rate", []))
            recovery_values = recovery_buckets.get((method, rel), [])
            n_episode = len(recovery_values)
            output.append(
                {
                    "graph_encoder": method,
                    "relative_step": str(rel),
                    "n_available": str(n),
                    "n_episode": str(n_episode),
                    "tracking_rate_mean": f"{float(np.mean(values['tracking_rate'])):.6g}" if n else "nan",
                    "connectivity_mean": f"{float(np.mean(values['comm_connectivity'])):.6g}" if n else "nan",
                    "chain_closed_mean": f"{float(np.mean(values['chain_closed'])):.6g}" if n else "nan",
                    "recovery_cdf": f"{float(np.mean(recovery_values)):.6g}" if n_episode else "nan",
                }
            )
    return output


def combine_curve_csvs(paths: list[Path], methods: list[str]) -> list[dict[str, str]]:
    buckets: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for path in paths:
        for row in read_rows(path):
            n = int(float(row["n_available"]))
            n_episode = int(float(row.get("n_episode", n)))
            key = (row["graph_encoder"], int(row["relative_step"]))
            buckets[key]["n_available"] += n
            buckets[key]["n_episode"] += n_episode
            for metric in ("tracking_rate_mean", "connectivity_mean", "chain_closed_mean", "recovery_cdf"):
                if row[metric] != "nan":
                    weight = n_episode if metric == "recovery_cdf" else n
                    buckets[key][metric] += weight * float(row[metric])

    if not buckets:
        return []
    rel_values = [key[1] for key in buckets]
    output: list[dict[str, str]] = []
    for method in methods:
        for rel in range(min(rel_values), max(rel_values) + 1):
            values = buckets.get((method, rel), {})
            n = int(values.get("n_available", 0))
            n_episode = int(values.get("n_episode", 0))
            output.append(
                {
                    "graph_encoder": method,
                    "relative_step": str(rel),
                    "n_available": str(n),
                    "n_episode": str(n_episode),
                    "tracking_rate_mean": f"{values['tracking_rate_mean'] / n:.6g}" if n else "nan",
                    "connectivity_mean": f"{values['connectivity_mean'] / n:.6g}" if n else "nan",
                    "chain_closed_mean": f"{values['chain_closed_mean'] / n:.6g}" if n else "nan",
                    "recovery_cdf": f"{values['recovery_cdf'] / n_episode:.6g}" if n_episode else "nan",
                }
            )
    return output


def plot_outputs(curve_rows: list[dict[str, str]], case_rows: list[dict[str, str]], out_dir: Path) -> tuple[Path, Path]:
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    colors = {"no_graph": "#7f7f7f", "single": "#386cb0", "multi_relation": "#1b9e77"}
    labels = {"no_graph": "No graph", "single": "Single graph", "multi_relation": "Multi-relation"}

    curve_fig = out_dir / "failure_aligned_mechanism_curves.png"
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.6), dpi=180, sharex=True)
    metrics = [
        ("tracking_rate_mean", "Tracking"),
        ("connectivity_mean", "Connectivity"),
        ("chain_closed_mean", "Chain closure"),
        ("recovery_cdf", "Recovery CDF"),
    ]
    for ax, (metric, title) in zip(axes.ravel(), metrics):
        for method in sorted({row["graph_encoder"] for row in curve_rows}):
            part = [row for row in curve_rows if row["graph_encoder"] == method and row[metric] != "nan"]
            if not part:
                continue
            ax.plot(
                [int(row["relative_step"]) for row in part],
                [float(row[metric]) for row in part],
                color=colors.get(method, "#333333"),
                linewidth=2.0,
                label=labels.get(method, method),
            )
        ax.axvline(0, color="#222222", linewidth=0.8, linestyle="--")
        ax.set_title(title)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
    axes[1, 0].set_xlabel("Steps after relay failure")
    axes[1, 1].set_xlabel("Steps after relay failure")
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(curve_fig)
    plt.close(fig)

    case_fig = out_dir / "representative_case_timeline.png"
    fig, ax = plt.subplots(figsize=(9.5, 4.2), dpi=180)
    for method in sorted({row["graph_encoder"] for row in case_rows}):
        part = [row for row in case_rows if row["graph_encoder"] == method]
        x = [int(row["relative_step"]) for row in part]
        ax.plot(x, [float(row["tracking_rate"]) for row in part], color=colors.get(method, "#333333"), linewidth=2.0, label=f"{labels.get(method, method)} tracking")
        ax.plot(x, [float(row["chain_closed"]) for row in part], color=colors.get(method, "#333333"), linestyle="--", linewidth=1.8, label=f"{labels.get(method, method)} chain")
    ax.axvspan(0, 80, color="#dddddd", alpha=0.45, label="Relay failure window")
    ax.set_xlabel("Steps after relay failure")
    ax.set_ylabel("Rate / indicator")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
    ax.legend(ncol=2, frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(case_fig)
    plt.close(fig)
    return curve_fig, case_fig


def format_row(row: dict[str, str]) -> str:
    return (
        f"`{row['graph_encoder']}` seed {row['train_seed']} episode {row['episode']}: "
        f"recovered={row['post_failure_chain_recovered']}, "
        f"recovery_steps={row['post_failure_chain_recovery_steps']}, "
        f"success={row['success']}, timeout={row['timeout']}"
    )


def display_path(path: Path) -> str:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        return resolved.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_summary(
    args: argparse.Namespace,
    curve_fig: Path | None,
    case_fig: Path | None,
    case_methods: dict[str, dict[str, str]] | None,
) -> None:
    args.docs_dir.mkdir(parents=True, exist_ok=True)
    summary = args.docs_dir / "failure_aligned_mechanism_summary.md"
    lines = [
        "# Failure-Aligned Mechanism Evidence",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Inputs",
        "",
        f"- Episode CSV: `{display_path(args.episode_csv)}`",
        f"- Selection CSV: `{display_path(args.selection_csv)}`",
        "",
    ]
    if case_methods is None:
        lines.extend(
            [
                "## Representative Case",
                "",
                "Representative-case replay was skipped for this run.",
                "",
            ]
        )
    else:
        selection = case_methods["_selection"]
        lines.extend(
            [
                "## Representative Case Rule",
                "",
                "The case is selected automatically from matched `single` and `multi_relation` test episodes.",
                "The script computes a positive case score from recovery-probability gain and capped recovery-step gain, then chooses the candidate closest to the median positive score. This avoids hand-picking the largest gap.",
                "",
                "```text",
                f"positive_candidates = {selection['n_positive_candidates']}",
                f"median_positive_case_score = {selection['median_positive_case_score']}",
                f"selected_case_score = {selection['case_score']}",
                "```",
                "",
                "## Selected Episode",
                "",
            ]
        )
        for method in (args.baseline_method, args.proposed_method):
            lines.append(f"- {format_row(case_methods[method])}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Curves CSV: `{display_path(args.out_dir / 'failure_aligned_curves.csv')}`",
        ]
    )
    if case_methods is not None:
        lines.append(f"- Case CSV: `{display_path(args.out_dir / 'representative_case_replay.csv')}`")
    if curve_fig is not None:
        lines.append(f"- Curves figure: `{display_path(curve_fig)}`")
    if case_fig is not None:
        lines.append(f"- Case figure: `{display_path(case_fig)}`")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "Use these figures to explain the completed five-seed formal result. They are not a new training result and should not be used to tune model checkpoints.",
            "",
        ]
    )
    summary.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    all_episode_rows = read_rows(args.episode_csv)
    selections = selection_map(read_rows(args.selection_csv))
    agent_cache: dict[tuple[str, str, str, str, str], tuple[object, object]] = {}

    if args.curve_input_glob:
        curve_paths = [Path(p) for p in sorted(glob.glob(args.curve_input_glob, recursive=True))]
        if not curve_paths:
            raise FileNotFoundError(args.curve_input_glob)
        curve_rows = combine_curve_csvs(curve_paths, args.methods)
    else:
        episode_rows = [row for row in all_episode_rows if row["graph_encoder"] in set(args.methods)]
        if args.train_seeds is not None:
            allowed_seeds = {int(seed) for seed in args.train_seeds}
            episode_rows = [row for row in episode_rows if int(row["train_seed"]) in allowed_seeds]
        if args.episode_count > 0:
            start = args.episode_start
            stop = start + args.episode_count
            episode_rows = [row for row in episode_rows if start <= int(row["episode"]) < stop]
        limited_rows: list[dict[str, str]] = []
        for method in args.methods:
            rows = [row for row in episode_rows if row["graph_encoder"] == method]
            if args.max_episodes_per_method > 0:
                rows = rows[: args.max_episodes_per_method]
            limited_rows.extend(rows)

        replay_rows: list[dict[str, float | int | str]] = []
        for row in limited_rows:
            ckpt = selections[(row["graph_encoder"], int(row["train_seed"]))]
            replay_rows.extend(replay_episode(row, ckpt, args.device, agent_cache))

        rel_min = -args.window_before
        rel_max = args.window_after
        curve_rows = aggregate_curves(replay_rows, args.methods, rel_min, rel_max)

    case_methods: dict[str, dict[str, str]] | None = None
    case_rows_raw: list[dict[str, float | int | str]] = []
    if not args.skip_case:
        case_methods = choose_case(all_episode_rows, args.baseline_method, args.proposed_method)
        for method in (args.baseline_method, args.proposed_method):
            row = case_methods[method]
            ckpt = selections[(row["graph_encoder"], int(row["train_seed"]))]
            case_rows_raw.extend(replay_episode(row, ckpt, args.device, agent_cache))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    curve_path = args.out_dir / "failure_aligned_curves.csv"
    case_path = args.out_dir / "representative_case_replay.csv"
    write_csv(curve_path, curve_rows, CURVE_FIELDS)
    if case_rows_raw:
        write_csv(case_path, [{k: f"{v:.6g}" if isinstance(v, float) else str(v) for k, v in row.items() if k in CASE_FIELDS} for row in case_rows_raw], CASE_FIELDS)
    curve_fig = None
    case_fig = None
    if not args.skip_plots:
        if case_rows_raw:
            curve_fig, case_fig = plot_outputs(curve_rows, read_rows(case_path), args.out_dir)
        else:
            curve_fig, _case_fig = plot_outputs(curve_rows, [], args.out_dir)
            case_fig = None
    write_summary(args, curve_fig, case_fig, case_methods)
    print(curve_path)
    if case_rows_raw:
        print(case_path)
    if curve_fig is not None:
        print(curve_fig)
    if case_fig is not None:
        print(case_fig)


if __name__ == "__main__":
    main()
