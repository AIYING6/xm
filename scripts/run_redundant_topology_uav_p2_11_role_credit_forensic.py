"""P2.11: frozen, non-learning role-credit and action-timing forensic."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_redundant_topology_uav_p2_9 as p29
from scripts.run_redundant_topology_uav_p2 import graph_stack, tensors

PROTOCOL = "P2_11_ROLE_CREDIT_ACTION_TIMING_FORENSIC_V1"
ARMS = ("plain_assigned_role_sg_mappo", "utr_assigned_role_sg_mappo")
SEEDS = (66011, 66012, 66013, 66014, 66015)
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_11_20260903/P2_11_ROLE_CREDIT_ACTION_TIMING_CONTRACT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def policy_probe(agent: torch.nn.Module, seed: int, device: torch.device) -> dict[str, object]:
    """One scripted support transition, followed by a masked actor forward pass.

    The selected policy action is never stepped into the environment. Thus this
    is an action-availability probe rather than an episode-level evaluation.
    """
    env = p29.make_env(seed, "nominal")
    _, share, graph = env.reset(seed_env=seed)
    setup = np.zeros(env.n, dtype=np.int64)
    setup[env.scout_ids] = np.arange(1, env.k + 1, dtype=np.int64)
    _, share, graph, _, _, _ = env.step(setup)
    packed = graph_stack([graph])
    with torch.no_grad():
        action = agent.action_value(*tensors(packed, share[None], device), deterministic=True)[0][0].cpu().numpy()
    scouts = action[env.scout_ids]
    terminals = action[env.terminal_ids]
    assigned = np.asarray([env.terminal_assignment[int(node)] + 1 for node in env.terminal_ids], dtype=np.int64)
    return {
        "seed": seed,
        "scout_actions_after_support": json.dumps(scouts.tolist()),
        "scout_distinct_objective_coverage": float(len(set(map(int, scouts))) == env.k and np.all(scouts > 0)),
        "terminal_actions_when_tokens_legal": json.dumps(terminals.tolist()),
        "terminal_nonidle_fraction": float(np.mean(terminals > 0)),
        "terminal_assignment_alignment": float(np.mean(terminals == assigned)),
        "terminal_distinct_objective_coverage": float(len(set(map(int, terminals))) == env.k and np.all(terminals > 0)),
        "scripted_setup_environment_steps": 1,
        "policy_action_environment_steps": 0,
    }


def run_script(label: str, actions: tuple[np.ndarray, np.ndarray, np.ndarray]) -> dict[str, object]:
    """Execute exactly three prescribed non-policy transitions for causal timing."""
    env = p29.make_env(771100, "nominal")
    env.reset(seed_env=771100)
    rewards, info = [], None
    for action in actions:
        _, _, _, reward, _, info = env.step(action)
        rewards.append(reward)
    assert info is not None
    return {
        "script": label,
        "steps": len(actions),
        "completed_objectives": int(env.completed.sum()),
        "success_after_three_steps": bool(info["success"]),
        "shared_reward_step1": float(rewards[0][0, 0]),
        "shared_reward_step2": float(rewards[1][0, 0]),
        "shared_reward_step3": float(rewards[2][0, 0]),
        "reward_broadcast_exact": bool(all(np.all(reward == reward[0, 0]) for reward in rewards)),
        "step1_actions": json.dumps(actions[0].tolist()),
        "step2_actions": json.dumps(actions[1].tolist()),
        "step3_actions": json.dumps(actions[2].tolist()),
    }


def fixed_scripts() -> list[dict[str, object]]:
    # Node order at main scale: Scouts 0,1; Relays 2,3; Terminals 4,5.
    full_1 = np.asarray([1, 2, 0, 0, 0, 0], dtype=np.int64)
    full_2 = np.asarray([1, 2, 0, 0, 1, 2], dtype=np.int64)
    same_1 = np.asarray([1, 1, 0, 0, 0, 0], dtype=np.int64)
    same_2 = np.asarray([1, 1, 0, 0, 1, 1], dtype=np.int64)
    scout_ablate_1 = np.asarray([0, 2, 0, 0, 0, 0], dtype=np.int64)
    scout_ablate_2 = np.asarray([0, 2, 0, 0, 1, 2], dtype=np.int64)
    terminal_ablate_2 = np.asarray([1, 2, 0, 0, 0, 2], dtype=np.int64)
    return [
        run_script("full_assigned_coordination", (full_1, full_2, full_2)),
        run_script("same_objective_coordination", (same_1, same_2, same_2)),
        run_script("scout0_ablation", (scout_ablate_1, scout_ablate_2, scout_ablate_2)),
        run_script("terminal0_ablation", (full_1, terminal_ablate_2, terminal_ablate_2)),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p29-root", default="results/development/redundant_topology_uav_p2_9")
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_11_role_credit_forensic")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    p29_root, out = Path(args.p29_root), Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.11 output exists; refusing overwrite")
    if "P2_9_BASE_TASK_NOT_LEARNABLE" not in (p29_root / "diagnostics" / "P2_9_FINAL_VERDICT.md").read_text(encoding="utf-8"):
        raise RuntimeError("P2.11 requires completed P2.9 no-learnability verdict")
    checkpoints = [p29_root / "runs" / arm / f"seed{seed}" / "runtime_1m.pt" for arm in ARMS for seed in SEEDS]
    if not all(path.is_file() for path in checkpoints):
        raise RuntimeError("missing retained P2.9 final checkpoint")
    p29.configure_core()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    probes: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            checkpoint = p29_root / "runs" / arm / f"seed{seed}" / "runtime_1m.pt"
            probes.append({"arm": arm, "checkpoint_sha256": sha256(checkpoint), **policy_probe(p29.core.load_agent(checkpoint, device), seed, device)})
    scripts = fixed_scripts()
    diag = out / "diagnostics"; diag.mkdir(parents=True)
    write_csv(diag / "P2_11_FINAL_POLICY_ACTION_PROBE.csv", probes)
    write_csv(diag / "P2_11_FIXED_SCRIPT_COUNTERFACTUALS.csv", scripts)
    scout_coverage = float(np.mean([float(row["scout_distinct_objective_coverage"]) for row in probes]))
    terminal_coverage = float(np.mean([float(row["terminal_distinct_objective_coverage"]) for row in probes]))
    terminal_alignment = float(np.mean([float(row["terminal_assignment_alignment"]) for row in probes]))
    full = next(row for row in scripts if row["script"] == "full_assigned_coordination")
    same = next(row for row in scripts if row["script"] == "same_objective_coordination")
    if scout_coverage < 0.50:
        verdict = "P2_11_SCOUT_OBJECTIVE_COVERAGE_COLLAPSE"
    elif terminal_coverage < 0.50 or terminal_alignment < 0.50:
        verdict = "P2_11_TERMINAL_ASSIGNMENT_ACTION_COLLAPSE"
    else:
        verdict = "P2_11_NO_SINGLE_ROLE_ACTION_COLLAPSE"
    payload = {
        "protocol": PROTOCOL, "verdict": verdict,
        "scout_distinct_objective_coverage": scout_coverage,
        "terminal_distinct_objective_coverage": terminal_coverage,
        "terminal_assignment_alignment": terminal_alignment,
        "full_script_completed_objectives": full["completed_objectives"],
        "same_objective_script_completed_objectives": same["completed_objectives"],
        "reward_broadcast_exact": all(bool(row["reward_broadcast_exact"]) for row in scripts),
        "policy_probe_environment_steps": len(probes),
        "scripted_counterfactual_environment_steps": sum(int(row["steps"]) for row in scripts),
        "formal_evaluation_started": False, "ppo_updates": 0, "training_started": False,
        "automatic_continuation": False,
    }
    report = "# P2.11 role-credit and action-timing report\n\n"
    report += f"**Verdict:** `{verdict}`.\n\n"
    report += "Policy actions are forward-pass-only after one scripted support transition; no selected policy action was stepped. Fixed scripts are causal timing probes, not evaluation episodes.\n\n"
    report += "```json\n" + json.dumps(payload, indent=2) + "\n```\n"
    (diag / "P2_11_ROLE_CREDIT_REPORT.md").write_text(report, encoding="utf-8")
    (diag / "P2_11_FINAL_VERDICT.md").write_text("# P2.11 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
