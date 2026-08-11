"""L1 development-only requalification under the repaired actor contract."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from scripts import run_l1_role_specific_development as l1
from scripts import run_new_project_l0_single_interceptor as l0


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "l1_corrected_contract_requalification"
PROTOCOL = "L1_RECIPIENT_SPECIFIC_ACTOR_CONTRACT_REQUALIFICATION_V1"


def cfg(seed: int, out_dir: Path, updates: int = l1.UPDATES):
    return replace(l1.cfg(seed, out_dir, updates=updates), agent_target_info_bottleneck=True,
                   protocol_version=PROTOCOL, run_id=f"l1_corrected_contract_seed{seed}")


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite requalification output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    template = cfg(l1.TRAIN_SEEDS[0], OUT / "template", updates=1)
    (OUT / "L1_CORRECTED_CONTRACT_MANIFEST.json").write_text(json.dumps({
        "status": "L1_CORRECTED_CONTRACT_REQUALIFICATION", "performance_use_prohibited": True,
        "training_seeds": list(l1.TRAIN_SEEDS), "evaluation_seeds": list(l1.EVAL_SEEDS), "updates": l1.UPDATES,
        "only_changed_variable_from_l1_role_specific": "agent_target_info_bottleneck false -> true",
        "contract": "actor target information requires current local sensing or delivered cache-valid packet",
        "config": asdict(template),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trained = []
    for seed in l1.TRAIN_SEEDS:
        run = OUT / f"l1_corrected_contract_seed{seed}"
        run_cfg = cfg(seed, run)
        ckpt = run / "actor_critic_latest.pt"
        if not ckpt.exists():
            l0.train_ri_gmappo(run_cfg)
        trained.append((f"l1_corrected_contract_seed{seed}", l0.load_agent(run_cfg, ckpt)))
    rows = []
    eval_cfg = cfg(l1.TRAIN_SEEDS[0], OUT / "template", updates=1)
    for seed in l1.EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(l1.episode(eval_cfg, seed, mode))
        for name, agent in trained:
            rows.append({**l1.episode(eval_cfg, seed, name, agent), "mode": name})
    with (OUT / "episode_outcomes.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for mode in sorted({r["mode"] for r in rows}):
        group = [r for r in rows if r["mode"] == mode]
        summary.append({"mode": mode, "episodes": len(group),
                        "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])),
                        "neutralization_rate": float(np.mean([r["neutralized_by_180"] for r in group])),
                        "rmtn180": float(np.mean([r["rmtn180"] for r in group])),
                        "collision_rate": float(np.mean([r["collision"] for r in group])),
                        "constraint_failure_rate": float(np.mean([r["constraint_failure"] for r in group]))})
    with (OUT / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    random_row = next(row for row in summary if row["mode"] == "random")
    learned = [row for row in summary if row["mode"].startswith("l1_corrected_contract")]
    positive = [row for row in learned if row["geometry_entry_rate"] > 0 and row["neutralization_rate"] > random_row["neutralization_rate"] and row["rmtn180"] < l1.HORIZON]
    verdict = "L1_CORRECTED_CONTRACT_LEARNING_SIGNAL_RETAINED" if len(positive) == len(l1.TRAIN_SEEDS) else ("L1_CORRECTED_CONTRACT_NO_GO__COMMUNICATION_LADDER_REQUIRES_REDESIGN" if not positive else "L1_CORRECTED_CONTRACT_PARTIAL_UNSTABLE_SIGNAL")
    (OUT / "L1_CORRECTED_CONTRACT_VERDICT.json").write_text(json.dumps({"verdict": verdict, "summary": summary, "performance_use_prohibited": True}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "summary": summary}, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
