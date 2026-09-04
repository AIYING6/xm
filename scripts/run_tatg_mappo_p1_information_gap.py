"""Zero-training TATG P1 topology-transition information-gap diagnostic.

This program deliberately tests a narrow property of the existing actor-legal
*topology* interface.  It does not claim that the full continuous actor
observation is non-Markov, and it does not load or evaluate a learned policy.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    RELATION_COMMUNICATION,
    RELATION_TASK_SUPPORT,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


FREEZE_PATH = ROOT / "configs" / "tatg_mappo_p1_information_gap_freeze.json"
NEUTRAL_ACTION = 13


def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def load_freeze() -> dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def topology_snapshot_code(graph: dict[str, np.ndarray], max_steps: int) -> str:
    """Serialize only the frozen actor-legal topology fields.

    Continuous geometry and target estimates are intentionally excluded: P1
    asks whether a *topology snapshot* represents transition direction or
    stage.  The message-age field is retained so that the test does not hide
    the existing current-snapshot temporal proxy.
    """

    relations = graph["relation_adj"]
    blue_n = graph["node_feat"].shape[0] - 1
    comm = relations[RELATION_COMMUNICATION, :blue_n, :blue_n].astype(np.int8)
    support = relations[RELATION_TASK_SUPPORT, :blue_n, :blue_n].astype(np.int8)
    ages = np.rint(graph["edge_feat"][:blue_n, :blue_n, 15] * max_steps).astype(np.int16)
    payload = {
        "comm": comm.reshape(-1).tolist(),
        "support": support.reshape(-1).tolist(),
        "age_steps": ages.reshape(-1).tolist(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def transition_label(previous_comm: np.ndarray, current_comm: np.ndarray) -> str:
    delta = current_comm.astype(np.int16) - previous_comm.astype(np.int16)
    lost = int(np.count_nonzero(delta < 0))
    recovered = int(np.count_nonzero(delta > 0))
    if lost and recovered:
        return "mixed"
    if lost:
        return "loss"
    if recovered:
        return "recovery"
    return "stable"


def make_env(seed: int, scripted: dict[str, Any]) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed,
            target_policy=str(scripted["target_policy"]),
            strict_target_sensing=bool(scripted["strict_target_sensing"]),
            agent_target_info_bottleneck=bool(scripted["agent_target_info_bottleneck"]),
            relay_dependent_task=bool(scripted["relay_dependent_task"]),
            failed_blue_agent=1,
            node_failure_start_step=int(scripted["failure_onset_step"]),
            node_failure_duration_steps=int(scripted["failure_duration_steps"]),
            communication_dropout_prob=float(scripted["communication_dropout_prob"]),
            radar_dropout_prob=float(scripted["radar_dropout_prob"]),
            max_steps=int(scripted["capture_steps"]) + 8,
            min_success_step=10_000,
        )
    )


def collect_seed(cohort: str, seed: int, scripted: dict[str, Any]) -> list[dict[str, Any]]:
    env = make_env(seed, scripted)
    _, _, graph = env.reset()
    previous_code = topology_snapshot_code(graph, env.config.max_steps)
    previous_comm = graph["relation_adj"][RELATION_COMMUNICATION].copy()
    rows: list[dict[str, Any]] = []
    actions = np.full(env.num_agents, NEUTRAL_ACTION, dtype=np.int64)

    for _ in range(int(scripted["capture_steps"])):
        _, _, graph, _rewards, dones, _info = env.step(actions)
        current_code = topology_snapshot_code(graph, env.config.max_steps)
        current_comm = graph["relation_adj"][RELATION_COMMUNICATION].copy()
        label = transition_label(previous_comm, current_comm)
        rows.append(
            {
                "cohort": cohort,
                "state_seed": seed,
                "step": int(env.step_count),
                "snapshot_code": current_code,
                "history_code": previous_code + "=>" + current_code,
                "transition_label": label,
            }
        )
        previous_code = current_code
        previous_comm = current_comm
        if bool(np.all(dones)):
            raise RuntimeError(f"scripted P1 trajectory ended before capture horizon for state seed {seed}")
    return rows


def ambiguity_count(rows: list[dict[str, Any]], key: str) -> tuple[int, int]:
    labels: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        labels[str(row[key])].add(str(row["transition_label"]))
        counts[str(row[key])] += 1
    ambiguous_codes = {code for code, values in labels.items() if len(values) > 1}
    ambiguous_rows = sum(counts[code] for code in ambiguous_codes)
    return len(ambiguous_codes), ambiguous_rows


def cohort_summary(rows: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    labels = [str(row["transition_label"]) for row in rows]
    snapshot_mixed_codes, snapshot_ambiguous_rows = ambiguity_count(rows, "snapshot_code")
    history_mixed_codes, _ = ambiguity_count(rows, "history_code")
    return {
        "rows": len(rows),
        "loss_events": labels.count("loss"),
        "recovery_events": labels.count("recovery"),
        "mixed_events": labels.count("mixed"),
        "snapshot_mixed_code_count": snapshot_mixed_codes,
        "snapshot_ambiguous_rows": snapshot_ambiguous_rows,
        "history_mixed_code_count": history_mixed_codes,
        "pass": (
            labels.count("loss") >= int(decision["per_cohort_required_loss_events"])
            and labels.count("recovery") >= int(decision["per_cohort_required_recovery_events"])
            and snapshot_ambiguous_rows >= int(decision["per_cohort_required_ambiguous_snapshot_rows"])
            and history_mixed_codes == int(decision["per_cohort_required_history_mixed_code_count"])
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO P1 topology-transition information-gap diagnostic",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "P1 uses no policy, reward, return, evaluation tape, checkpoint or PPO update. Its labels are derived only from two consecutive legal communication relation snapshots.",
        "",
        "## Interpretation boundary",
        "",
        "A pass establishes a narrow topology-transition information gap: the frozen current structural topology snapshot, including its current edge-age proxy, maps to more than one transition label, whereas a one-step legal topology history removes that ambiguity in both state cohorts. It does not establish improved control return, full-observation non-Markovness, or novelty of a generic recurrent graph network.",
        "",
        "## Cohorts",
        "",
    ]
    for name, summary in result["cohorts"].items():
        lines.append(f"- Cohort {name}: `{json.dumps(summary, sort_keys=True)}`")
    lines += [
        "",
        "A pass authorizes only a separate exact-formula, fairness and serialization audit. It does not authorize TATG implementation, PPO training or cloud execution.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to generate P1 diagnostic data without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")

    freeze = load_freeze()
    output.mkdir(parents=True)
    all_rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    for cohort, seeds in freeze["cohorts"].items():
        rows: list[dict[str, Any]] = []
        for seed in seeds:
            rows.extend(collect_seed(str(cohort), int(seed), freeze["scripted_environment"]))
        all_rows.extend(rows)
        summaries[str(cohort)] = cohort_summary(rows, freeze["decision_rule"])

    passed = all(summary["pass"] for summary in summaries.values())
    result = {
        "protocol": freeze["protocol"],
        "verdict": freeze["pass"] if passed else freeze["fail"],
        "cohorts": summaries,
        "state_cohorts_separate": True,
        "training_started": False,
        "evaluation_started": False,
        "environment_steps": len(all_rows),
        "ppo_updates": 0,
        "checkpoint_loaded": False,
        "automatic_continuation": False,
    }
    fields = ["cohort", "state_seed", "step", "snapshot_code", "history_code", "transition_label"]
    with (output / "TATG_P1_TRANSITION_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_rows)
    write_lf(output / "TATG_P1_RESULT.json", json.dumps(result, indent=2) + "\n")
    write_lf(output / "TATG_P1_REPORT.md", render_report(result))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
