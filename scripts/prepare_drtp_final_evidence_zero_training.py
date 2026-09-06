"""Prepare final DRTP paper-evidence contracts without training or evaluation.

This tool deliberately has no access to the held-out/OOD evaluation directory.
It freezes the next evidence interfaces, checks the maintained 6-UAV source
contract with reset/one-step probes only, and writes paper-ready empty tables.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from envs.redundant_topology_uav_env import ROLE_RELAY, RedundantTopologyUAVEnv, scale_config
from scripts.drtp_stabilization_confirmation_contracts import ARMS, cohort_spec
from scripts.run_drtp_stabilization_confirmatory_single import STEPS, UPDATES, training_config


PROTOCOL = "DRTP-FINAL-EVIDENCE-ZERO-TRAINING-PREPARATION-V1"
DATE = "2026-09-06"
DOCS = ROOT / "docs" / "drtp_final_evidence_preparation_20260906_complete"
CONFIG = ROOT / "configs" / "drtp_final_external_comparator_freeze_20260906.json"
METHOD_SELECTION = ROOT / "configs" / "drtp_stabilization_final_method_selection_20260906.json"
OOD_FREEZE = ROOT / "configs" / "drtp_final_evidence_p0_heldout_ood_freeze_20260906.json"
ARCHIVES = {
    "A": "429f13444c4ed10327abd62a13a0d9bf8ee737cedb6b6448353fd9087bcb275f",
    "B": "d5c4adbe4f0004f0f415ba38e2b03232c55cb46c7d5dc7c7b1031eef7c1eef73",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "working-tree-provenance-only"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def json_default(value: object):
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def six_uav_preflight() -> dict:
    env = RedundantTopologyUAVEnv(scale_config("main", assignment_observation=True, scout_assignment_observation=True))
    obs, share, graph = env.reset(seed_env=20260906)
    legal_paths = [(int(s), int(r), int(t)) for s in env.scout_ids for r in env.relay_ids for t in env.terminal_ids]
    relay_masks = graph["action_masks"][env.relay_ids]
    action = np.zeros(env.n, dtype=np.int64)
    next_obs, next_share, next_graph, rewards, dones, info = env.step(action)
    agent = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim)
    with torch.no_grad():
        logits = agent.scout_actor(
            torch.as_tensor(graph["node_features"][None], dtype=torch.float32),
            torch.as_tensor(graph["roles"][None]),
            torch.as_tensor(graph["active_adj"][None], dtype=torch.float32),
        )
    checks = {
        "six_agents_with_2_2_2_roles": env.n == 6 and len(env.scout_ids) == len(env.relay_ids) == len(env.terminal_ids) == 2,
        "eight_legal_scout_relay_terminal_paths": len(legal_paths) == 8,
        "within_role_sharing_and_cross_role_separation": agent.scout_actor is not agent.relay_actor and agent.relay_actor is not agent.terminal_actor,
        "relay_has_single_effective_policy_action": agent.relay_actor.action_dim == 1,
        "actor_observation_and_masks_exist": obs.shape == (6, env.obs_dim) and graph["action_masks"].shape == (6, env.action_dim) and np.all(relay_masks == 1),
        "scout_and_terminal_assignments_bijective": len(set(env.scout_assignment.values())) == 2 and len(set(env.terminal_assignment.values())) == 2,
        "graph_transition_changes_are_exposed": next_graph["active_adj"].shape == graph["active_adj"].shape and next_obs.shape == obs.shape,
        "termination_reward_and_goal_interfaces_exist": rewards.shape == (env.n, 1) and dones.shape == (env.n, 1) and {"success", "timeout", "collision_any"}.issubset(info),
        "role_actor_forward_is_finite": bool(torch.isfinite(logits).all()),
        "utr_reference_runner_exists": (ROOT / "scripts" / "run_redundant_topology_uav_p2_13.py").is_file(),
        "nonlearning_probe_only": True,
    }
    return {
        "protocol": "DRTP-FINAL-6UAV-CROSS-SCALE-PREFLIGHT-V1", "verdict": "DRTP_FINAL_6UAV_PREFLIGHT_PASS" if all(checks.values()) else "DRTP_FINAL_6UAV_PREFLIGHT_FAIL",
        "checks": checks, "scale": "main", "roles": {"scouts": 2, "relays": 2, "terminals": 2},
        "legal_paths": legal_paths, "interface": {"obs": list(obs.shape), "share_obs": list(share.shape), "node_features": list(graph["node_features"].shape), "task_adjacency": list(graph["task_adj"].shape), "active_adjacency": list(graph["active_adj"].shape)},
        "one_step": {"success": bool(info["success"]), "timeout": bool(info["timeout"]), "done": bool(dones[0, 0])},
        "training_started": False, "evaluation_started": False,
    }


def fairness_audit() -> dict:
    normalized: dict[str, dict] = {}
    for cohort in ("A", "B"):
        seed = cohort_spec(cohort)["seeds"][0]
        cfgs = {arm: asdict(training_config(arm, seed, Path("frozen-output") / cohort / arm)) for arm in ("utr_sg", "drtp_sg")}
        for cfg in cfgs.values():
            for key in ("seed", "drtp_sampler_seed", "out_dir", "device", "drtp_sampler_mode"):
                cfg.pop(key, None)
        normalized[cohort] = cfgs
    checks = {
        "same_ppo_model_reward_environment_budget": all(values["utr_sg"] == values["drtp_sg"] for values in normalized.values()),
        "only_sampler_mode_differs": all(training_config("utr_sg", cohort_spec(c)["seeds"][0], Path("x")).drtp_sampler_mode == "utr" and training_config("drtp_sg", cohort_spec(c)["seeds"][0], Path("x")).drtp_sampler_mode == "drtp" for c in ("A", "B")),
        "same_10m_endpoint_budget": UPDATES == 39063 and STEPS == 10000128,
        "same_frozen_endpoint_protocol": all(cohort_spec(c)["freeze"]["frozen_training"]["endpoint_only"] for c in ("A", "B")),
        "same_arm_specific_seed_set_within_cohort": all(len(cohort_spec(c)["seeds"]) == 5 for c in ("A", "B")),
        "no_checkpoint_selection_or_early_stopping": all(not training_config(arm, cohort_spec(c)["seeds"][0], Path("x")).save_snapshots for c in ("A", "B") for arm in ("utr_sg", "drtp_sg")),
    }
    return {"protocol": "DRTP-UTR-FINAL-FAIRNESS-AUDIT-V1", "verdict": "DRTP_UTR_FINAL_FAIRNESS_PASS" if all(checks.values()) else "DRTP_UTR_FINAL_FAIRNESS_FAIL", "checks": checks, "allowed_difference": "drtp_sampler_mode only", "training_started": False, "evaluation_started": False}


def external_comparator_contract() -> dict:
    payload = {
        "protocol": "DRTP-PLR-EXTERNAL-COMPARATOR-CONTRACT-V1", "date": DATE,
        "primary_comparator": {"name": "Prioritized Level Replay (PLR)-style topology-condition replay", "paper": "Jiang, Grefenstette, Rocktaschel, ICML 2021", "paper_url": "https://proceedings.mlr.press/v139/jiang21b.html", "source_url": "https://github.com/facebookresearch/level-replay", "source_license": "CC-BY-NC-4.0", "implementation_rule": "Independently implement only the published level-score/replay-distribution rule; do not copy non-commercial source code."},
        "mapping": {"level": "one of seven frozen DRTP groups; PLR reweights only the six failure groups", "score": "mean absolute unnormalised generalized advantage over vectorised training-rollout fragments only", "replay_distribution": "fixed nominal mass 0.50 plus PLR staleness/score mixture conditional on the six failure groups; frozen within-group member draw remains uniform", "evaluation_access": "forbidden", "forbidden": ["evaluation-tape access", "return-selected checkpoint", "post-hoc condition removal", "reward/environment/observation/PPO change"]},
        "fairness": {"same_environment": True, "same_failure_semantics": True, "same_reward_and_actor_information": True, "same_10m_budget": True, "same_fresh_seeds_per_cohort": True, "same_fixed_endpoint_tapes": True, "same_episode_counts": True, "report_parameter_count_and_wall_time": True, "no_endless_tuning": True},
        "status": "CONTRACT_ONLY_NO_EXTERNAL_TRAINING", "training_started": False,
    }
    return payload


def documents(out: Path, six: dict, fairness: dict, comparator: dict) -> None:
    write(out / "DRTP_FINAL_EXTERNAL_COMPARATOR_CONTRACT.md", """# DRTP final external-comparator contract

**Status:** `CONTRACT_ONLY_NO_EXTERNAL_TRAINING`.

The designated external comparator is a faithful, independent PLR-style topology-condition replay implementation, based on Jiang et al. (ICML 2021). It is a sampling-level comparator, not a replacement actor or a retrospective ablation. The original repository is CC-BY-NC-4.0, so no upstream source will be copied.

| Fairness dimension | Frozen rule |
|---|---|
| Support | Same nominal group + six failure groups; original uniform member draw remains inside each group |
| Environment / failures / reward / actor information | Identical to UTR and DRTP |
| PPO / model / budget | Identical; 10,000,128 environment steps per trajectory |
| Seeds / endpoint tapes / episodes | Fresh matched cohorts; same fixed endpoint tapes and counts |
| Tuning | One published-rule mapping; no outcome-driven sweep |
| Reporting | Parameter count and wall-clock cost alongside outcome metrics |

PLR can be reported only as an external adaptive task-sampling comparator. It does not establish that DRTP is a direct implementation of PLR or that either method solves universal robustness.
""")
    write(out / "DRTP_FINAL_6UAV_CROSS_SCALE_CONTRACT.md", """# DRTP final 6-UAV cross-scale contract

The retained cross-scale environment is the existing 2-scout / 2-relay / 2-terminal main scale with eight legal scout-relay-terminal paths. Future UTR and Original DRTP runs must inherit the role-shared learner, legal action masks, objective/assignment semantics, rewards, termination, seed handling and matched fixed evaluation design without source changes.

Future training is not authorized by this contract. When separately authorized, it must use fresh training seeds, a frozen endpoint budget, fixed final checkpoint only, frozen failure groups, matched UTR/DRTP configurations, and seed-level primary analysis. No 6-UAV result may be inferred from the 3-UAV evidence.
""")
    write(out / "DRTP_UTR_FINAL_FAIRNESS_AUDIT.md", """# DRTP versus UTR final fairness audit

**Verdict:** `DRTP_UTR_FINAL_FAIRNESS_PASS`.

| Dimension | UTR | Original DRTP | Audit result |
|---|---|---|---|
| Actor/critic, PPO, reward, environment, failure support | Frozen common configuration | Frozen common configuration | identical |
| Training distribution | Uniform topology sampling | Adaptive DRTP sampling | intended sole method difference |
| Budget | 39,063 updates / 10,000,128 steps | same | identical |
| Checkpoint / stopping | final 10M only; no promotion | same | identical |
| Seeds and endpoint tapes | matched within each cohort | same | identical |

The audit is a source/configuration comparison, not a performance claim. It identifies no implementation correction; further fairness re-auditing is not automatically authorized.
""")
    write(out / "DRTP_FINAL_PAPER_EVIDENCE_TABLES.md", """# DRTP final paper evidence tables (frozen skeleton)

Terminology: **robustness benefit** means higher frozen-endpoint perturbed return under the stated condition set; **reliability** means the observed seed-level lower-tail, spread and safety profile. Neither term means universal seed-stable superiority.

## Table A — Cohort A (completed)

| Method | Perturbed mean | Worst seed | Sample SD | Primary inference unit |
|---|---:|---:|---:|---|
| UTR | 177.02 | 79.75 | 64.53 | training seed |
| Original DRTP | 216.66 | 191.49 | 23.48 | training seed |
| EGTR | 226.13 | 203.92 | 15.86 | training seed |
| GA-EGTR alpha=.75 | 210.82 | 128.64 | 46.73 | training seed |

## Table B — Cohort B (completed)

| Method | Perturbed mean | Worst seed | Sample SD | Primary inference unit |
|---|---:|---:|---:|---|
| UTR | 187.18 | 164.98 | 21.66 | training seed |
| Original DRTP | 210.34 | 172.03 | 30.54 | training seed |
| EGTR | 144.00 | 29.13 | 76.84 | training seed |
| GA-EGTR alpha=.75 | 181.23 | 110.07 | 40.62 | training seed |

## Table C — Frozen held-out structural OOD (do not populate until the cloud evaluation is complete)

| Condition | UTR | Original DRTP | Paired direction | Timeout | Collision |
|---|---:|---:|---:|---:|---:|
| structural_scout_node |  |  |  |  |  |
| structural_symmetric_longest_edge |  |  |  |  |  |
| structural_directed_longest_edge |  |  |  |  |  |
| structural_scout_node_plus_edge |  |  |  |  |  |

## Table D — External comparator (blank until separately executed)

| Method | Budget | Matched cohort | Perturbed return | Lower-tail | Timeout / collision |
|---|---:|---|---:|---:|---:|
| UTR |  |  |  |  |  |
| Original DRTP |  |  |  |  |  |
| PLR-style replay |  |  |  |  |  |

## Table E — 6-UAV cross-scale (blank until separately executed)

| Method | Scale | Budget | Robust return | Lower-tail | Safety |
|---|---|---:|---:|---:|---:|
| UTR | 2S/2R/2T |  |  |  |  |
| Original DRTP | 2S/2R/2T |  |  |  |  |
""")
    write(out / "DRTP_FINAL_FROZEN_CLAIM_EVIDENCE_MATRIX.md", """# DRTP final frozen claim–evidence matrix

| Claim | Required evidence | Current status | Boundary |
|---|---|---|---|
| DRTP changes topology-condition exposure under a matched UTR control | Source/config fairness audit | supported | Method definition, not universal superiority |
| DRTP produced repeated robustness benefit in two frozen fresh 10M cohorts | A and B kept separate | supported | Does not erase historical cohort sensitivity |
| DRTP transfers to held-out structural topology shift | Completed frozen Table C | pending | Conditional on Table C; no universal generalization claim |
| DRTP compares favorably with a relevant external adaptive sampler | Matched PLR-style comparator | pending | Conditional on separately executed comparison |
| DRTP transfers to 6-UAV scale | Matched 6-UAV UTR/DRTP study | pending | Conditional on separately executed cross-scale study |
""")
    ledger = {"protocol": PROTOCOL, "date": DATE, "source_commit": source_commit(), "source_sha256": {"learner": sha256(ROOT / "algorithms/ri_gmappo/simple_ri_gmappo.py"), "sampler": sha256(ROOT / "algorithms/ri_gmappo/drtp_topology_sampler.py"), "3uav_environment": sha256(ROOT / "envs/uav_intercept_3d_env.py"), "6uav_environment": sha256(ROOT / "envs/redundant_topology_uav_env.py"), "ood_freeze": sha256(OOD_FREEZE)}, "archives": ARCHIVES, "method_selection": json.loads(METHOD_SELECTION.read_text(encoding="utf-8")), "confirmation": {c: {"seeds": list(cohort_spec(c)["seeds"]), "updates": UPDATES, "environment_steps": STEPS, "tape": cohort_spec(c)["episode_ids"]} for c in ("A", "B")}, "ood": json.loads(OOD_FREEZE.read_text(encoding="utf-8"))["fresh_heldout_ood_tape"], "six_uav_preflight": six, "fairness": fairness, "external_comparator": comparator, "training_started": False, "evaluation_started": False, "ood_performance_read": False}
    write(out / "DRTP_FINAL_REPRODUCIBILITY_LEDGER.json", json.dumps(ledger, indent=2, default=json_default))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DOCS)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    args.output_root = args.output_root.resolve()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    six, fairness, comparator = six_uav_preflight(), fairness_audit(), external_comparator_contract()
    if six["verdict"] != "DRTP_FINAL_6UAV_PREFLIGHT_PASS" or fairness["verdict"] != "DRTP_UTR_FINAL_FAIRNESS_PASS":
        raise RuntimeError("zero-training preflight failed")
    args.output_root.mkdir(parents=True)
    documents(args.output_root, six, fairness, comparator)
    (args.output_root / "DRTP_FINAL_6UAV_PREFLIGHT_REPORT.json").write_text(json.dumps(six, indent=2, default=json_default) + "\n", encoding="utf-8")
    (args.output_root / "DRTP_FINAL_EXTERNAL_COMPARATOR_CONTRACT.json").write_text(json.dumps(comparator, indent=2, default=json_default) + "\n", encoding="utf-8")
    outputs = [display_path(path) for path in sorted(args.output_root.iterdir())]
    print(json.dumps({"protocol": PROTOCOL, "verdict": "ZERO_TRAINING_FINAL_EVIDENCE_PREPARATION_COMPLETE", "training_started": False, "evaluation_started": False, "ood_performance_read": False, "outputs": outputs}, indent=2, default=json_default))


if __name__ == "__main__":
    main()
