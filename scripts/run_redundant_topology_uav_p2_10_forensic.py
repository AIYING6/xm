"""Read-only P2.10 forensic audit for completed P2.9 trajectories."""
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
from scripts.run_redundant_topology_uav_p2 import graph_stack

PROTOCOL = "P2_10_ASSIGNED_BASELINE_LEARNING_FORENSIC_V1"
ARMS = ("plain_assigned_role_sg_mappo", "utr_assigned_role_sg_mappo")
SEEDS = (66011, 66012, 66013, 66014, 66015)
MILESTONES = ("0", "500k", "1m")
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_10_20260903/P2_10_LEARNING_FORENSIC_CONTRACT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def telemetry_rows(p29_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            source = p29_root / "runs" / arm / f"seed{seed}" / "train_log.csv"
            with source.open(encoding="utf-8") as handle:
                log = list(csv.DictReader(handle))
            if len(log) != 3907:
                raise RuntimeError(f"expected 3907 updates in {source}, found {len(log)}")
            first, last = log[:512], log[-512:]
            values = lambda key, block: np.asarray([float(row[key]) for row in block], dtype=float)
            finite = all(np.isfinite(values(key, log)).all() for key in ("policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm"))
            rows.append({
                "arm": arm, "seed": seed, "updates": len(log), "finite": finite,
                "entropy_first512": float(values("entropy", first).mean()),
                "entropy_last512": float(values("entropy", last).mean()),
                "value_loss_first512": float(values("value_loss", first).mean()),
                "value_loss_last512": float(values("value_loss", last).mean()),
                "approx_kl_first512": float(values("approx_kl", first).mean()),
                "approx_kl_last512": float(values("approx_kl", last).mean()),
                "grad_norm_first512": float(values("grad_norm", first).mean()),
                "grad_norm_last512": float(values("grad_norm", last).mean()),
                "source_sha256": sha256(source),
            })
    return rows


def raw_terminal_probe(agent: torch.nn.Module, seed: int, milestone: str, device: torch.device) -> dict[str, object]:
    """Compare raw terminal logits after a preference-only input swap.

    This does not invoke the environment transition function and deliberately
    avoids action masks: it measures whether the learned terminal actor uses
    the appended cue before legality masks would force terminal idling.
    """
    env = p29.make_env(seed, "nominal")
    _, _, graph = env.reset(seed_env=seed)
    stacked = graph_stack([graph])
    obs = torch.as_tensor(stacked["obs"], dtype=torch.float32, device=device)
    roles = torch.as_tensor(stacked["roles"], dtype=torch.long, device=device)
    adj = torch.as_tensor(stacked["adj"], dtype=torch.float32, device=device)
    terminal_ids = env.terminal_ids.astype(int)
    base_dim = 8 + 3 * env.k
    swapped = obs.clone()
    reversed_terminal_ids = terminal_ids[::-1].copy()
    swapped[:, terminal_ids, base_dim:] = swapped[:, reversed_terminal_ids, base_dim:].clone()
    with torch.no_grad():
        original_logits = agent.terminal_actor(obs, roles, adj)[0, terminal_ids]
        swapped_logits = agent.terminal_actor(swapped, roles, adj)[0, terminal_ids]
    preference = np.argmax(obs[0, terminal_ids, base_dim:].cpu().numpy(), axis=1) + 1
    raw_action = torch.argmax(original_logits, dim=-1).cpu().numpy()
    raw_swapped_action = torch.argmax(swapped_logits, dim=-1).cpu().numpy()
    return {
        "seed": seed,
        "milestone": milestone,
        "terminal_count": len(terminal_ids),
        "mean_abs_logit_shift_preference_swap": float(torch.mean(torch.abs(original_logits - swapped_logits)).cpu()),
        "raw_nonidle_fraction": float(np.mean(raw_action > 0)),
        "raw_assignment_alignment": float(np.mean(raw_action == preference)),
        "raw_swapped_action_change_fraction": float(np.mean(raw_action != raw_swapped_action)),
        "raw_actions": json.dumps(raw_action.tolist()),
        "assigned_actions": json.dumps(preference.tolist()),
        "raw_swapped_actions": json.dumps(raw_swapped_action.tolist()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p29-root", default="results/development/redundant_topology_uav_p2_9")
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_10_forensic")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "execute_required": True, "training_started": False})); return
    p29_root, out = Path(args.p29_root), Path(args.output_root)
    if out.exists():
        raise RuntimeError("P2.10 output exists; refusing overwrite")
    final = p29_root / "diagnostics" / "P2_9_FINAL_VERDICT.md"
    if "P2_9_BASE_TASK_NOT_LEARNABLE" not in final.read_text(encoding="utf-8"):
        raise RuntimeError("P2.10 requires the completed P2.9 base-task-not-learnable verdict")
    required = [p29_root / "runs" / arm / f"seed{seed}" / f"runtime_{milestone}.pt" for arm in ARMS for seed in SEEDS for milestone in MILESTONES]
    if not all(path.is_file() for path in required):
        raise RuntimeError("missing retained P2.9 checkpoint required by the frozen forensic audit")
    p29.configure_core()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    telemetry = telemetry_rows(p29_root)
    probes: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            for milestone in MILESTONES:
                checkpoint = p29_root / "runs" / arm / f"seed{seed}" / f"runtime_{milestone}.pt"
                agent = p29.core.load_agent(checkpoint, device)
                probes.append({"arm": arm, "checkpoint_sha256": sha256(checkpoint), **raw_terminal_probe(agent, seed, milestone, device)})
    diag = out / "diagnostics"
    diag.mkdir(parents=True)
    write_csv(diag / "P2_10_TRAINING_TELEMETRY.csv", telemetry)
    write_csv(diag / "P2_10_ASSIGNMENT_LOGIT_PROBE.csv", probes)
    final_probes = [row for row in probes if row["milestone"] == "1m"]
    max_shift = max(float(row["mean_abs_logit_shift_preference_swap"]) for row in final_probes)
    mean_nonidle = float(np.mean([float(row["raw_nonidle_fraction"]) for row in final_probes]))
    mean_alignment = float(np.mean([float(row["raw_assignment_alignment"]) for row in final_probes]))
    if max_shift <= 1e-7:
        verdict = "P2_10_ASSIGNMENT_SIGNAL_ABSENT"
    elif mean_nonidle == 0.0:
        verdict = "P2_10_RAW_TERMINAL_IDLE_COLLAPSE"
    elif mean_alignment < 0.50:
        verdict = "P2_10_ASSIGNMENT_SIGNAL_PRESENT_MISALIGNED"
    else:
        verdict = "P2_10_NO_SINGLE_MINIMAL_INTERFACE_DEFECT"
    payload = {
        "protocol": PROTOCOL, "verdict": verdict,
        "p29_verdict": "P2_9_BASE_TASK_NOT_LEARNABLE",
        "all_telemetry_finite": all(bool(row["finite"]) for row in telemetry),
        "final_checkpoint_max_preference_swap_logit_shift": max_shift,
        "final_raw_terminal_nonidle_fraction": mean_nonidle,
        "final_raw_assignment_alignment": mean_alignment,
        "probe_is_unmasked_forward_only": True,
        "environment_steps": 0, "ppo_updates": 0, "new_evaluation_started": False,
        "training_started": False, "automatic_continuation": False,
    }
    report = "# P2.10 learning forensic report\n\n"
    report += f"**Verdict:** `{verdict}`.\n\n"
    report += "The actor probe is an unmasked, preference-only forward-pass contrast; it is not a policy evaluation and it takes no environment steps.\n\n"
    report += "```json\n" + json.dumps(payload, indent=2) + "\n```\n"
    (diag / "P2_10_FORENSIC_REPORT.md").write_text(report, encoding="utf-8")
    (diag / "P2_10_FINAL_VERDICT.md").write_text("# P2.10 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
