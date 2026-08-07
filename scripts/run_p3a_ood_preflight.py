# run_p3a_ood_preflight.py — P3-A exposure-only preflight (protocol v1.1).
# Checks ONLY failure exposure (steps >= failure_start) across 84 primary cells.
# It must NOT output or summarize success / recovery / t_rec / RMST / reward / rankings.
# Hard gate: exposure_rate >= 0.99 in all 84 cells.
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.p3a_ood_cells import (  # noqa: E402
    PRIMARY_METHODS, CELLS, TRAIN_SEEDS, EPISODES_PER_CELL, EVAL_BASE_SEED,
    FAILURE_START, FAILURE_DURATION, HORIZON, EXPOSURE_GATE, FAILED_BLUE_AGENT,
    checkpoint_path, cell_overrides, common_eval_overrides,
)


def make_args(checkpoint, seed, device, eval_batch_size, overrides):
    a = argparse.Namespace(
        checkpoint=checkpoint, episodes=EPISODES_PER_CELL, eval_batch_size=eval_batch_size,
        seed=int(seed), base_seed=EVAL_BASE_SEED, target_policy="straight",
        communication_range_scale=1.0, communication_dropout_prob=0.3,
        message_delay_steps=2, radar_dropout_prob=0.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(0.0, 0.0, 0.0),
        max_target_message_age_steps=40, min_target_confidence=0.0,
        failed_blue_agent=FAILED_BLUE_AGENT, node_failure_start_step=FAILURE_START,
        node_failure_duration_steps=FAILURE_DURATION, attack_hold_steps=4,
        min_success_step=0, stochastic=False, allow_random_policy=False,
        hidden_dim=64, role_dim=8, intent_dim=8, graph_encoder="multi_relation",
        graph_relation_ablation="none", graph_message_ablation="none",
        graph_input_ablation="none", multi_relation_global_residual_weight=0.5,
        device=device, max_steps=HORIZON,
        blue_init_rotation_deg=0.0, blue_init_spacing_scale=1.0,
        target_init_range_scale=1.0, target_init_bearing_offset_deg=0.0,
        comm_topology_mode="none",
    )
    for k, v in overrides.items():
        setattr(a, k, v)
    return a


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out-root", required=True)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--eval-batch-size", type=int, default=8)
    args = parser.parse_args()
    device = args.device

    from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_config as ri_build_config  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_agent as ri_build_agent  # noqa: E402
    from scripts.evaluate_happo_3d import build_config as ha_build_config  # noqa: E402
    from scripts.evaluate_happo_3d import build_agent as ha_build_agent  # noqa: E402

    out = Path("docs/statistics/p3a_ood_results_v1_0")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    failures = []
    for method in PRIMARY_METHODS:
        for seed in TRAIN_SEEDS:
            ck = checkpoint_path(method, seed)
            if not ck.exists():
                failures.append(f"{method} seed{seed}: checkpoint missing {ck}")
                continue
            for cell in sorted(CELLS):
                over = common_eval_overrides()
                over.update(cell_overrides(cell))
                a = make_args(ck, seed, device, args.eval_batch_size, over)
                if method == "happo":
                    cfg = ha_build_config(a)
                    agent, _ = ha_build_agent(a, cfg)
                else:
                    cfg = ri_build_config(a)
                    agent, _ = ri_build_agent(a, cfg)
                agent = agent.to(device)
                exposed = 0
                total = 0
                with torch.no_grad():
                    for batch_start in range(0, EPISODES_PER_CELL, a.eval_batch_size):
                        batch_eps = list(range(batch_start, min(EPISODES_PER_CELL, batch_start + a.eval_batch_size)))
                        envs, obs_l, share_l, graph_l = [], [], [], []
                        for ep in batch_eps:
                            env = make_env(cfg, EVAL_BASE_SEED + ep, training=False)
                            obs, so, g = env.reset()
                            envs.append(env); obs_l.append(obs); share_l.append(so); graph_l.append(g)
                        active = [True] * len(batch_eps)
                        while any(active):
                            ai = [i for i, ac in enumerate(active) if ac]
                            g = stack_graphs([graph_l[i] for i in ai])
                            if method == "happo":
                                obs_t = torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device)
                                so_t = torch.as_tensor(np.stack([share_l[i] for i in ai]), dtype=torch.float32, device=device)
                                role_t = torch.as_tensor(g["role"], dtype=torch.long, device=device)
                                # HAPPO agent uses obs + share_obs (no graph inputs)
                                act, *_ = agent.get_action(obs_t, so_t, role=role_t, deterministic=True)
                                act = act.cpu().numpy()
                            else:
                                actions, *_ = agent.get_action_and_value(
                                    torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device),
                                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                                    torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                                    torch.as_tensor(np.stack([share_l[i] for i in ai]), dtype=torch.float32, device=device),
                                    relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                                    deterministic=True,
                                    intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                                    detach_intent=False, oracle_intent=False,
                                )
                                act = actions.cpu().numpy()
                            for k, env_i in enumerate(ai):
                                obs_l[env_i], share_l[env_i], graph_l[env_i], rew, done, info = envs[env_i].step(act[k])
                                if np.all(done):
                                    steps = int(getattr(envs[env_i], "step_count", 0))
                                    total += 1
                                    if steps >= FAILURE_START:
                                        exposed += 1
                                    active[env_i] = False
                rate = exposed / total if total else 0.0
                ok = rate >= EXPOSURE_GATE
                rows.append({
                    "method": method, "train_seed": seed, "cell": cell,
                    "episodes": total, "failure_start": FAILURE_START,
                    "exposed_count": exposed, "exposure_rate": f"{rate:.4f}",
                    "threshold": EXPOSURE_GATE, "pass": "1" if ok else "0",
                    "base_seed": EVAL_BASE_SEED, "checkpoint": str(ck),
                    "checkpoint_sha256": sha256_file(ck),
                    "ood_config": str(cell_overrides(cell)),
                })
                if not ok:
                    failures.append(f"{method} seed{seed} {cell}: exposure {rate:.4f} < {EXPOSURE_GATE}")
                print(f"{method} s{seed} {cell}: exposure {rate:.4f} ({exposed}/{total})", flush=True)

    with (out / "p3a_preflight_exposure.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    n_cells = len(rows)
    n_pass = sum(1 for r in rows if r["pass"] == "1")
    print(f"\ncells: {n_cells}  pass: {n_pass}")
    if failures:
        print("FAILURES:")
        for x in failures:
            print("  -", x)
        return 1
    print("PREFLIGHT PASS (exposure-only; no performance was inspected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
