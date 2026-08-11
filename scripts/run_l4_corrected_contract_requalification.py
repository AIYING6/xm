"""L4 delay-only development requalification under the repaired actor contract."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from scripts import run_l4_delay_development as l4
from scripts import run_new_project_l0_single_interceptor as l0


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "l4_corrected_contract_requalification"
PROTOCOL = "L4_RECIPIENT_SPECIFIC_ACTOR_CONTRACT_REQUALIFICATION_V1"


def cfg(seed: int, out_dir: Path, updates: int = l4.UPDATES):
    """Keep historical L4 fixed except for the repaired target contract."""
    return replace(
        l4.cfg(seed, out_dir, updates=updates),
        agent_target_info_bottleneck=True,
        protocol_version=PROTOCOL,
        run_id=f"l4_corrected_contract_seed{seed}",
    )


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite requalification output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    template = cfg(l4.TRAIN_SEEDS[0], OUT / "template", updates=1)
    (OUT / "L4_CORRECTED_CONTRACT_MANIFEST.json").write_text(
        json.dumps(
            {
                "status": "L4_CORRECTED_CONTRACT_DELAY_REQUALIFICATION",
                "performance_use_prohibited": True,
                "source_commit": l4.source_commit(),
                "training_seeds": list(l4.TRAIN_SEEDS),
                "evaluation_seeds": list(l4.EVAL_SEEDS),
                "updates": l4.UPDATES,
                "only_changed_variable_from_l4": "agent_target_info_bottleneck false -> true",
                "added_complexity_relative_to_corrected_l3": "message delay 8 steps",
                "communication_range_scale": 0.5,
                "communication_dropout_prob": 0.3,
                "message_delay_steps": 8,
                "contract": "actor target information requires current local sensing or delivered cache-valid packet",
                "config": asdict(template),
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    trained = []
    for seed in l4.TRAIN_SEEDS:
        run = OUT / f"l4_corrected_contract_seed{seed}"
        run_cfg = cfg(seed, run)
        checkpoint = run / "actor_critic_latest.pt"
        if not checkpoint.exists():
            l0.train_ri_gmappo(run_cfg)
        trained.append((f"l4_corrected_contract_seed{seed}", l0.load_agent(run_cfg, checkpoint)))

    rows = []
    eval_cfg = cfg(l4.TRAIN_SEEDS[0], OUT / "template", updates=1)
    for seed in l4.EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(l4.episode(eval_cfg, seed, mode))
        for name, agent in trained:
            rows.append({**l4.episode(eval_cfg, seed, name, agent), "mode": name})
    with (OUT / "episode_outcomes.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    for mode in sorted({row["mode"] for row in rows}):
        group = [row for row in rows if row["mode"] == mode]
        summary.append(
            {
                "mode": mode,
                "episodes": len(group),
                "geometry_entry_rate": float(np.mean([row["geometry_entry"] for row in group])),
                "neutralization_rate": float(np.mean([row["neutralized_by_180"] for row in group])),
                "rmtn180": float(np.mean([row["rmtn180"] for row in group])),
                "collision_rate": float(np.mean([row["collision"] for row in group])),
                "constraint_failure_rate": float(np.mean([row["constraint_failure"] for row in group])),
            }
        )
    with (OUT / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    random_row = next(row for row in summary if row["mode"] == "random")
    learned = [row for row in summary if row["mode"].startswith("l4_corrected_contract")]
    positive = [
        row
        for row in learned
        if row["geometry_entry_rate"] > 0
        and row["neutralization_rate"] > random_row["neutralization_rate"]
        and row["rmtn180"] < l4.HORIZON
    ]
    if len(positive) == len(l4.TRAIN_SEEDS):
        verdict = "L4_CORRECTED_CONTRACT_DELAY_LEARNING_SIGNAL_RETAINED__READY_FOR_RELAY_PATH_REDESIGN"
    elif not positive:
        verdict = "L4_CORRECTED_CONTRACT_DELAY_NO_GO__DELAY_ASSOCIATED_BREAKPOINT"
    else:
        verdict = "L4_CORRECTED_CONTRACT_DELAY_PARTIAL_UNSTABLE_SIGNAL"
    payload = {"verdict": verdict, "summary": summary, "performance_use_prohibited": True}
    (OUT / "L4_CORRECTED_CONTRACT_VERDICT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
