#!/usr/bin/env python3
"""T3 offline-only predictability audit for attacker support continuity.

The program consumes existing T1 JSONL telemetry.  It does not create an
environment, load a MARL checkpoint, invoke PyTorch optimization, or generate
any rollout.  The only fitted models are CPU logistic diagnostic probes.
"""

from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


SEEDS = (2201, 2202, 2203, 2204, 2205)
MAX_HISTORY = 32
LABEL_HORIZON = 16
SUPPORT_FRACTION = 0.75
MAX_GAP = 4
SAMPLES_PER_CLASS_PER_SEED = 4000
RANDOM_SEED = 73031
SCENARIO_CODE = {
    "nominal": 0,
    "f0_seen_44_80": 1,
    "timing_28_80": 2,
    "timing_36_80": 3,
    "timing_52_80": 4,
    "timing_60_80": 5,
    "duration_44_40": 6,
    "duration_44_60": 7,
    "duration_44_100": 8,
    "duration_44_120": 9,
    "compound_28_120": 10,
    "compound_60_120": 11,
}
SCENARIOS = tuple(SCENARIO_CODE)


def period_for(*, scenario: str, step: int, onset: int) -> str:
    if scenario == "nominal":
        return "nominal"
    tau = step - onset
    if tau < 0:
        return "pre"
    if tau < 20:
        return "early"
    if tau < 60:
        return "mid"
    if tau < 120:
        return "late"
    return "post_late"


def graph_summary(actor: dict) -> np.ndarray:
    """Compact, legal-only graph snapshot for the attacker (index 2)."""
    adjacency = np.asarray(actor["graph_adj"], dtype=np.float32)
    relation = np.asarray(actor["graph_relation_adj"], dtype=np.float32)
    edge = np.asarray(actor["graph_edge_feat"], dtype=np.float32)
    attacker = 2
    incoming = edge[:, attacker, :].mean(axis=0)
    outgoing = edge[attacker, :, :].mean(axis=0)
    relation_degrees = np.concatenate(
        [relation[:, attacker, :].sum(axis=1), relation[:, :, attacker].sum(axis=1)]
    )
    adjacency_degrees = np.asarray(
        [adjacency[attacker, :].sum(), adjacency[:, attacker].sum()], dtype=np.float32
    )
    return np.concatenate([incoming, outgoing, relation_degrees, adjacency_degrees]).astype(np.float32)


def longest_zero_run(values: list[float]) -> int:
    longest = current = 0
    for value in values:
        if value <= 0.0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def support_continuity_label(future_legal_information: list[float]) -> int:
    """Future-only, path-agnostic continuity label.

    The label is one when legal target information is available for >=75% of
    the *next* 16 steps and has no absence run longer than four steps.  It does
    not require the same relay/direct route, failure label, terminal event, or
    final return.
    """
    assert len(future_legal_information) == LABEL_HORIZON
    return int(
        np.mean(future_legal_information) >= SUPPORT_FRACTION
        and longest_zero_run(future_legal_information) <= MAX_GAP
    )


def build_sample(rows: list[dict], index: int, label: int) -> dict:
    history = rows[max(0, index - MAX_HISTORY + 1) : index + 1]
    obs = np.asarray([row["obs"] for row in history], dtype=np.float32)
    graph = np.asarray([row["graph"] for row in history], dtype=np.float32)
    if len(history) < MAX_HISTORY:
        pad = MAX_HISTORY - len(history)
        obs = np.concatenate([np.repeat(obs[:1], pad, axis=0), obs], axis=0)
        graph = np.concatenate([np.repeat(graph[:1], pad, axis=0), graph], axis=0)
    current = rows[index]
    scenario_one_hot = np.asarray(
        [float(current["scenario"] == scenario) for scenario in SCENARIOS], dtype=np.float32
    )
    # This is deliberately an *oracle-only* diagnostic feature.  It depends on
    # the final episode length and is never an execution-time actor input.
    terminal_remaining = float(rows[-1]["post_step"] - current["post_step"])
    return {
        "label": label,
        "obs_history": obs,
        "graph_history": graph,
        "period": period_for(
            scenario=current["scenario"], step=current["post_step"], onset=current["onset"]
        ),
        "scenario": current["scenario"],
        "metadata": np.asarray(
            [
                current["post_step"], current["scheduled_onset"],
                current["scheduled_duration"], *scenario_one_hot,
            ],
            dtype=np.float32,
        ),
        "failure_active": float(current["failure_active"]),
        "terminal_remaining_oracle": terminal_remaining,
        "episode_id": current["episode_id"],
    }


def episode_candidate_indices(rows: list[dict]) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for index in range(len(rows) - LABEL_HORIZON):
        future = [rows[k]["legal_information"] for k in range(index + 1, index + 1 + LABEL_HORIZON)]
        candidates.append((index, support_continuity_label(future)))
    return candidates


def _push_reservoir(reservoir: list[tuple[float, int, int, list[dict]]], *, score: float,
                   episode_id: int, index: int, rows: list[dict]) -> None:
    """Keep the lowest deterministic random scores without retaining all windows."""
    item = (-score, episode_id, index, rows)
    if len(reservoir) < SAMPLES_PER_CLASS_PER_SEED:
        heapq.heappush(reservoir, item)
    elif score < -reservoir[0][0]:
        heapq.heapreplace(reservoir, item)


def parse_seed(raw_path: Path, seed: int) -> tuple[list[dict], dict]:
    label_counts = [0, 0]
    rng = np.random.default_rng(RANDOM_SEED + seed)
    reservoirs: dict[int, list[tuple[float, int, int, list[dict]]]] = {0: [], 1: []}
    current_key = None
    current_rows: list[dict] = []

    def flush() -> None:
        nonlocal current_rows
        if not current_rows:
            return
        for index, label in episode_candidate_indices(current_rows):
            label_counts[label] += 1
            _push_reservoir(
                reservoirs[label], score=float(rng.random()), episode_id=current_rows[index]["episode_id"],
                index=index, rows=current_rows,
            )
        current_rows = []

    with raw_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            key = (row["scenario"], int(row["episode_id"]))
            if current_key is not None and key != current_key:
                flush()
            current_key = key
            actor = row["actor"]
            info = row["diagnostic"]["info"]
            # T3 uses only attacker-local legal observation/graph as inputs.
            current_rows.append(
                {
                    "episode_id": key[1],
                    "scenario": key[0],
                    "post_step": int(row["post_step"]),
                    "scheduled_onset": int(row["scheduled_failure_onset"]),
                    "scheduled_duration": int(row["scheduled_failure_duration"]),
                    "onset": int(row["scheduled_failure_onset"]),
                    "failure_active": bool(row["failure_active_post"]),
                    "obs": np.asarray(actor["obs"][2], dtype=np.float32),
                    "graph": graph_summary(actor),
                    # Diagnostic-only label; never fed into a probe input.
                    "legal_information": float(info["attacker_legal_target_information_t"]),
                }
            )
    flush()
    selected: list[dict] = []
    for label in (0, 1):
        if not reservoirs[label]:
            raise RuntimeError(f"seed{seed} has no continuity label {label}")
        selected.extend(
            build_sample(rows, index, label)
            for _neg_score, _episode_id, index, rows in reservoirs[label]
        )
    rng.shuffle(selected)
    return selected, {
        "seed": seed,
        "candidate_count": sum(label_counts),
        "candidate_label_counts": {"0": label_counts[0], "1": label_counts[1]},
        "candidate_positive_prevalence": label_counts[1] / max(1, sum(label_counts)),
        "selected_count": len(selected),
        "selected_label_counts": {
            "0": sum(sample["label"] == 0 for sample in selected),
            "1": sum(sample["label"] == 1 for sample in selected),
        },
    }


def representation(samples: list[dict], name: str) -> np.ndarray:
    if name == "obs_l1":
        return np.stack([sample["obs_history"][-1] for sample in samples])
    if name == "obs_graph_l1":
        return np.stack(
            [np.concatenate([sample["obs_history"][-1], sample["graph_history"][-1]]) for sample in samples]
        )
    if name.startswith("obs_l"):
        horizon = int(name.removeprefix("obs_l"))
        return np.stack([sample["obs_history"][-horizon:].reshape(-1) for sample in samples])
    if name.startswith("obs_graph_l"):
        horizon = int(name.removeprefix("obs_graph_l"))
        return np.stack(
            [
                np.concatenate([sample["obs_history"][-horizon:], sample["graph_history"][-horizon:]], axis=1).reshape(-1)
                for sample in samples
            ]
        )
    if name == "metadata_only":
        return np.stack([sample["metadata"] for sample in samples])
    if name == "metadata_plus_failure_active":
        return np.stack([np.concatenate([sample["metadata"], [sample["failure_active"]]]) for sample in samples])
    if name == "metadata_plus_terminal_proximity_oracle":
        return np.stack(
            [np.concatenate([sample["metadata"], [sample["terminal_remaining_oracle"]]]) for sample in samples]
        )
    raise ValueError(name)


def fit_score(train: list[dict], validation: list[dict], name: str) -> dict:
    x_train = representation(train, name)
    x_validation = representation(validation, name)
    y_train = np.asarray([sample["label"] for sample in train], dtype=np.int64)
    y_validation = np.asarray([sample["label"] for sample in validation], dtype=np.int64)
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x_train)
    x_validation = scaler.transform(x_validation)
    classifier = SGDClassifier(
        loss="log_loss", alpha=1e-4, max_iter=40, tol=1e-3, random_state=RANDOM_SEED,
        early_stopping=False,
    )
    classifier.fit(x_train, y_train)
    probability = classifier.predict_proba(x_validation)[:, 1]
    prediction = (probability >= 0.5).astype(np.int64)
    def sliced_metrics(mask: np.ndarray) -> dict | None:
        if mask.sum() < 20 or len(np.unique(y_validation[mask])) < 2:
            return None
        return {
            "n": int(mask.sum()),
            "auc": float(roc_auc_score(y_validation[mask], probability[mask])),
            "balanced_accuracy": float(balanced_accuracy_score(y_validation[mask], prediction[mask])),
        }

    by_period = {}
    for period in ("nominal", "pre", "early", "mid", "late", "post_late"):
        mask = np.asarray([sample["period"] == period for sample in validation])
        metrics = sliced_metrics(mask)
        if metrics is not None:
            by_period[period] = metrics
    by_family = {}
    for family, scenarios in {
        "f0": ("f0_seen_44_80",),
        "timing": ("timing_28_80", "timing_36_80", "timing_52_80", "timing_60_80"),
        "duration": ("duration_44_40", "duration_44_60", "duration_44_100", "duration_44_120"),
        "compound": ("compound_28_120", "compound_60_120"),
    }.items():
        metrics = sliced_metrics(np.asarray([sample["scenario"] in scenarios for sample in validation]))
        if metrics is not None:
            by_family[family] = metrics
    return {
        "representation": name,
        "validation_seed": validation[0].get("seed"),
        "n_train": len(train),
        "n_validation": len(validation),
        "auc": float(roc_auc_score(y_validation, probability)),
        "balanced_accuracy": float(balanced_accuracy_score(y_validation, prediction)),
        "period_metrics": by_period,
        "family_metrics": by_family,
    }


def attach_seed(samples: list[dict], seed: int) -> None:
    for sample in samples:
        sample["seed"] = seed


def mean_metric(rows: list[dict], key: str) -> float:
    return float(np.mean([row[key] for row in rows]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    by_seed: dict[int, list[dict]] = {}
    summaries = []
    for seed in SEEDS:
        raw = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        samples, summary = parse_seed(raw, seed)
        attach_seed(samples, seed)
        by_seed[seed] = samples
        summaries.append(summary)
        print(f"T3 parsed seed{seed}: {summary['selected_count']} diagnostic samples", flush=True)
    names = (
        "obs_l1", "obs_graph_l1", "obs_l4", "obs_l8", "obs_l16", "obs_l32",
        "obs_graph_l16", "metadata_only", "metadata_plus_failure_active",
        "metadata_plus_terminal_proximity_oracle",
    )
    rows = []
    for validation_seed in SEEDS:
        train = [sample for seed, samples in by_seed.items() if seed != validation_seed for sample in samples]
        validation = by_seed[validation_seed]
        for name in names:
            result = fit_score(train, validation, name)
            result["validation_seed"] = validation_seed
            rows.append(result)
            print(f"T3 {name} -> seed{validation_seed}: AUC {result['auc']:.3f}", flush=True)
    pooled = {}
    for name in names:
        group = [row for row in rows if row["representation"] == name]
        pooled[name] = {
            "mean_auc": mean_metric(group, "auc"),
            "mean_balanced_accuracy": mean_metric(group, "balanced_accuracy"),
            "per_seed_auc": {str(row["validation_seed"]): row["auc"] for row in group},
            "per_seed_balanced_accuracy": {str(row["validation_seed"]): row["balanced_accuracy"] for row in group},
        }
    args.output_root.mkdir(parents=True)
    result = {
        "protocol": "T3-OFFLINE-CONTINUITY-PREDICTABILITY-V1",
        "offline_only": True,
        "label": {
            "role": "attacker",
            "horizon": LABEL_HORIZON,
            "future_only": True,
            "minimum_legal_information_fraction": SUPPORT_FRACTION,
            "maximum_consecutive_unavailable_steps": MAX_GAP,
            "uses_as_input": "actor.obs[2] and legal graph summaries only",
            "training_only_supervision": "diagnostic.info.attacker_legal_target_information_t",
        },
        "split": "leave-one-training-seed-out; no timestep split",
        "sample_cap": SAMPLES_PER_CLASS_PER_SEED,
        "seed_summaries": summaries,
        "results": rows,
        "pooled": pooled,
    }
    (args.output_root / "t3_predictability.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_root": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
