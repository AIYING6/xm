"""Read-only, paired M2 failure diagnosis from a frozen pilot archive.

This script never updates model parameters or environment configuration.  It
replays the four frozen checkpoints over the frozen evaluation seeds, verifies
that its endpoint summaries reproduce the archived values, and then exports
step-level control/progress diagnostics for the Full-versus-B1 comparison.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import tarfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from algorithms.ri_gmappo.acquisition_oriented import AcquisitionHistoryState, AcquisitionOrientedHybridPolicy
from algorithms.ri_gmappo.hybrid_action import TanhGaussianBernoulli
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR
from scripts import run_m2_acquisition_oriented_pilot as m2
from scripts import run_new_project_l0_single_interceptor as l0

METHODS = ("full", "b1")
SEEDS = (9201, 9202)


def archive_member(root: str, method: str, seed: int, leaf: str) -> str:
    return f"{root}/{method}_seed{seed}/{leaf}"


def stacked_graph(graphs):
    return __import__("algorithms.ri_gmappo.simple_ri_gmappo", fromlist=["stack_graphs"]).stack_graphs(graphs)


def load_checkpoint(archive: tarfile.TarFile, root: str, method: str, seed: int, device: torch.device):
    path = archive_member(root, method, seed, f"{method}_seed{seed}/checkpoint.pt")
    payload = torch.load(io.BytesIO(archive.extractfile(path).read()), map_location=device, weights_only=False)
    run_cfg = m2.cfg(seed, Path("diagnostic"), updates=payload["config"]["updates"])
    env = l0.make_env(run_cfg, seed, training=False)
    obs, share, _graph = env.reset()
    policy = AcquisitionOrientedHybridPolicy(obs.shape[-1], 4, run_cfg.hidden_dim, full=method == "full").to(device)
    critic = m2.CentralCritic(share.shape[-1], 4, run_cfg.hidden_dim).to(device)
    policy.load_state_dict(payload["policy"]); critic.load_state_dict(payload["critic"])
    policy.eval()
    return policy, run_cfg


def replay(policy, run_cfg, method: str, training_seed: int, episode_seed: int, device: torch.device):
    env = l0.make_env(run_cfg, episode_seed, training=False)
    obs, _share, graph = env.reset()
    state = policy.core.initial_state(torch.as_tensor(obs, dtype=torch.float32, device=device))
    previous = np.zeros((env.num_agents, 3), np.float32)
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    attack = np.asarray([typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} for typ in env.config.blue_types], np.float32)
    evidence_step = range_step = None
    steps = []
    while True:
        roles, evidence = m2.role_ids(graph), m2.legal_evidence(obs, run_cfg)
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
        prev_t = torch.as_tensor(previous, dtype=torch.float32, device=device)
        with torch.no_grad():
            fused, progress, next_state = policy.core.forward_step(
                obs_t, prev_t, torch.as_tensor(evidence, device=device), state
            )
            scale = torch.sigmoid(policy.core.fusion_projection(progress))
            flat = fused.reshape(-1, fused.shape[-1]); role_flat = torch.as_tensor(roles, device=device).reshape(-1).long()
            logits = flat.new_zeros((flat.shape[0], 5))
            for role_id, head in enumerate(policy.role_heads):
                mask = role_flat == role_id
                if torch.any(mask): logits[mask] = head(flat[mask])
            logits = logits.reshape(*fused.shape[:-1], 5)
            dist = TanhGaussianBernoulli(logits[..., :2], logits[..., 2:4], logits[..., 4])
            cont, commit, _ = dist.sample(deterministic=True)
            action_t = torch.cat([cont, commit.unsqueeze(-1)], dim=-1)
        action = action_t.cpu().numpy(); action[:, 2] = np.where(attack > .5, action[:, 2], -1.0)
        distance = float(np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker]))
        if evidence[attacker] and evidence_step is None: evidence_step = env.step_count
        steps.append({"training_seed": training_seed, "method": method, "episode_seed": episode_seed, "step": env.step_count, "attacker_evidence": int(evidence[attacker]), "distance": distance, "turn": float(action[attacker, 0]), "climb": float(action[attacker, 1]), "commit": float(action[attacker, 2]), "progress_norm": float(progress[attacker].norm().cpu()), "modulation_mean": float(scale[attacker].mean().cpu()), "target_history_norm": float(next_state.target[attacker].norm().cpu()), "self_history_norm": float(next_state.self_state[attacker].norm().cpu())})
        obs, _share, graph, _reward, done, info = env.step(action)
        post_distance = float(np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker]))
        if post_distance <= env.config.blue_types[attacker].attack_range_max and range_step is None: range_step = env.step_count
        previous = action.copy(); state = next_state
        if bool(np.all(done)):
            neutral = l0.outcome(info) == "NEUTRALIZED"
            record = {"training_seed": training_seed, "method": method, "episode_seed": episode_seed, "evidence_observed": int(evidence_step is not None), "attack_range_acquired": int(range_step is not None), "evidence_to_range_latency": int(range_step - evidence_step) if evidence_step is not None and range_step is not None else 180 - (evidence_step or 0), "no_attack_range_acquisition": int(evidence_step is not None and range_step is None and not neutral), "neutralized": int(neutral), "rmtn180": int(info["step"]) if neutral else 180, "failure_stage": "NEUTRALIZED" if neutral else "NO_ATTACK_RANGE_ACQUISITION" if evidence_step is not None and range_step is None else "RANGE_ACQUIRED_NO_NEUTRALIZATION" if range_step is not None else "NO_LEGAL_EVIDENCE"}
            return record, steps


def read_archived_summary(archive, root, method, seed):
    reader = csv.DictReader(io.TextIOWrapper(archive.extractfile(archive_member(root, method, seed, "summary.csv")), encoding="utf-8"))
    return next(reader)


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--archive", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--device", default="cpu"); args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite {args.output}")
    device = torch.device(args.device)
    records, steps = [], []
    with tarfile.open(args.archive, "r:gz") as archive:
        verdict_path = next(
            m.name for m in archive.getmembers()
            if m.name.endswith("m2_acquisition_oriented_pilot_cloud/PILOT_VERDICT.json")
        )
        root = verdict_path.rsplit("/", 1)[0]
        for method in METHODS:
            for seed in SEEDS:
                policy, run_cfg = load_checkpoint(archive, root, method, seed, device)
                arm_records = []
                for episode_seed in m2.EVAL_SEEDS:
                    record, trace = replay(policy, run_cfg, method, seed, episode_seed, device); arm_records.append(record); steps.extend(trace)
                archived = read_archived_summary(archive, root, method, seed)
                observed = {"acquisition_given_evidence": np.mean([r["attack_range_acquired"] for r in arm_records]), "evidence_to_range_latency": np.mean([r["evidence_to_range_latency"] for r in arm_records]), "no_attack_range_acquisition_fraction": np.mean([r["no_attack_range_acquisition"] for r in arm_records]), "neutralization_rate": np.mean([r["neutralized"] for r in arm_records]), "rmtn180": np.mean([r["rmtn180"] for r in arm_records])}
                for key, value in observed.items():
                    if not np.isclose(value, float(archived[key])): raise RuntimeError(f"replay mismatch for {method}/{seed}/{key}: {value} != {archived[key]}")
                records.extend(arm_records)
    args.output.mkdir(parents=True)
    write_csv(args.output / "episode_stage_records.csv", records); write_csv(args.output / "step_diagnostics.csv", steps)
    paired = []
    for seed in SEEDS:
        by = {(r["method"], r["episode_seed"]): r for r in records if r["training_seed"] == seed}
        for episode_seed in m2.EVAL_SEEDS:
            full, b1 = by[("full", episode_seed)], by[("b1", episode_seed)]
            paired.append({"training_seed": seed, "episode_seed": episode_seed, "paired_neutralization": "BOTH_SUCCESS" if full["neutralized"] and b1["neutralized"] else "FULL_ONLY" if full["neutralized"] else "B1_ONLY" if b1["neutralized"] else "BOTH_FAIL", "paired_acquisition": "BOTH_ACQUIRE" if full["attack_range_acquired"] and b1["attack_range_acquired"] else "FULL_ONLY" if full["attack_range_acquired"] else "B1_ONLY" if b1["attack_range_acquired"] else "BOTH_FAIL", "full_stage": full["failure_stage"], "b1_stage": b1["failure_stage"]})
    write_csv(args.output / "paired_episode_decomposition.csv", paired)
    counts = defaultdict(lambda: defaultdict(int))
    for row in paired: counts[str(row["training_seed"])][row["paired_neutralization"]] += 1
    payload = {"status": "M2_PARTIAL_READ_ONLY_DIAGNOSIS_COMPLETE", "replay_reproduces_archived_summary": True, "paired_neutralization_counts": {k: dict(v) for k, v in counts.items()}, "note": "No training, parameter update, environment modification, or new episode seed was used."}
    (args.output / "DIAGNOSIS_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__": main()
