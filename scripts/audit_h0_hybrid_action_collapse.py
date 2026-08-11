"""H0 read-only audit of hybrid guidance/commit collapse across existing runs.

This script never trains or alters a checkpoint.  It replays existing
development checkpoints on their already frozen evaluation seed population and
reports *behavioural* (deterministic-policy) commit entropy separately from
continuous-guidance variation.  A low commit rate alone is not called collapse
unless legal target evidence was present: abstaining from commit without
evidence is a valid policy behaviour under the actor contract.
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR  # noqa: E402
from scripts import run_l1_corrected_contract_requalification as l1  # noqa: E402
from scripts import run_l2_corrected_contract_requalification as l2  # noqa: E402
from scripts import run_l3_corrected_contract_requalification as l3  # noqa: E402
from scripts import run_l4_corrected_contract_requalification as l4  # noqa: E402
from scripts import run_m2_acquisition_oriented_pilot as m2  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as base  # noqa: E402

OUT = ROOT / "results" / "h0_hybrid_action_collapse_identifiability_r3"
# Predeclared audit subsample: this is a collapse-identifiability screen, not
# a performance comparison. Eight existing L4 evaluation seeds keep replay
# bounded while preserving common initial states across all baseline families.
EVAL_SEEDS = tuple(range(890_000, 890_008))


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def binary_entropy(rate: float) -> float:
    if rate <= 0.0 or rate >= 1.0:
        return 0.0
    return float(-rate * math.log2(rate) - (1.0 - rate) * math.log2(1.0 - rate))


def checkpoint_specs() -> list[tuple[str, int, object, Path]]:
    # The requalification wrapper deliberately does not re-export historical
    # seed constants; retrieve them from the source protocol it wraps.
    from scripts import run_l1_role_specific_development as l1_source
    from scripts import run_l2_limited_communication_development as l2_source
    from scripts import run_l3_packet_loss_development as l3_source
    from scripts import run_l4_delay_development as l4_source
    levels = [
        ("L1_corrected", l1, l1_source.TRAIN_SEEDS),
        ("L2_corrected", l2, l2_source.TRAIN_SEEDS),
        ("L3_corrected", l3, l3_source.TRAIN_SEEDS),
        ("L4_corrected", l4, l4_source.TRAIN_SEEDS),
    ]
    specs = []
    for label, module, seeds in levels:
        for seed in seeds:
            # The frozen scripts all store runs under the config run_id.
            run = module.OUT / module.cfg(seed, module.OUT / "template", updates=1).run_id
            specs.append((label, seed, module.cfg(seed, run, updates=1), run / "actor_critic_latest.pt"))
    return specs


def replay(label: str, train_seed: int, cfg, checkpoint: Path) -> list[dict]:
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    agent = base.load_agent(cfg, checkpoint)
    rows = []
    for episode_seed in EVAL_SEEDS:
        env = base.make_env(cfg, episode_seed, training=False)
        obs, share, graph = env.reset()
        attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
        while True:
            evidence = bool(m2.legal_evidence(obs, cfg)[attacker])
            action_all = np.asarray(base.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.config.num_blue, 3)
            action = action_all[attacker]
            rows.append({
                "family": label, "training_seed": train_seed, "episode_seed": episode_seed,
                "step": env.step_count, "evidence": int(evidence), "turn": float(action[0]),
                "climb": float(action[1]), "commit": int(action[2] >= 0.0),
            })
            obs, share, graph, _reward, dones, _info = env.step(action_all)
            if bool(np.all(dones)):
                break
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    summaries = []
    for family, seed in sorted({(r["family"], r["training_seed"]) for r in rows}):
        all_steps = [r for r in rows if r["family"] == family and r["training_seed"] == seed]
        group = [r for r in all_steps if r["evidence"]]
        episode_groups = {}
        for row in group:
            episode_groups.setdefault(row["episode_seed"], []).append(row)
        commits = np.asarray([r["commit"] for r in group], dtype=np.float32)
        turns = np.asarray([r["turn"] for r in group], dtype=np.float32)
        climbs = np.asarray([r["climb"] for r in group], dtype=np.float32)
        all_zero = all_one = 0
        for episode in episode_groups.values():
            values = {r["commit"] for r in episode}
            all_zero += values == {0}
            all_one += values == {1}
        rate = float(commits.mean()) if len(commits) else float("nan")
        summaries.append({
            "family": family, "training_seed": seed, "evidence_steps": int(len(group)),
            "evidence_episodes": int(len(episode_groups)), "commit_rate": rate,
            "commit_behavioral_entropy_bits": binary_entropy(rate) if len(commits) else float("nan"),
            "all_steps_commit_rate": float(np.mean([r["commit"] for r in all_steps])),
            "all_steps_commit_behavioral_entropy_bits": binary_entropy(float(np.mean([r["commit"] for r in all_steps]))),
            "turn_std": float(turns.std()) if len(turns) else float("nan"),
            "climb_std": float(climbs.std()) if len(climbs) else float("nan"),
            "all_zero_commit_episode_fraction": all_zero / len(episode_groups) if episode_groups else float("nan"),
            "all_one_commit_episode_fraction": all_one / len(episode_groups) if episode_groups else float("nan"),
        })
    return summaries


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    rows = []
    for label, seed, cfg, checkpoint in checkpoint_specs():
        rows.extend(replay(label, seed, cfg, checkpoint))
    with (OUT / "baseline_step_actions.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = summarize(rows)
    with (OUT / "baseline_commit_summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    payload = {
        "status": "H0_HYBRID_ACTION_COLLAPSE_IDENTIFIABILITY_AUDIT_COMPLETE",
        "source_commit": source_commit(), "evaluation_seeds": list(EVAL_SEEDS),
        "baseline_summary": summary,
        "scope": "existing L1-L4 corrected-contract checkpoints only; no training or environment mutation",
        "interpretation_rule": "H0 PASS requires collapse to recur in baseline families, not only M0 Full/M2R Full.",
    }
    (OUT / "H0_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
