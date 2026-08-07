# verify_task_support_v1_5.py — Steps 2+3: CPU/reference behavioral equivalence check
# + independent re-computation of window stats from per-step trajectories.
# Per (method, seed, scenario): first 5 episodes (indices 0-4), same base_seed derivation,
# deterministic actions. Reference = original eval entry (CPU). Compare against the locked
# extractor manifest/trajectory CSVs (GPU run).
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
OUT = ROOT / "docs" / "task_support_v1_5_assets"

sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs, make_env  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import (  # noqa: E402
    build_config, build_agent, build_episode_row,
)
from scripts.evaluate_3d_topology_robustness import SCENARIOS  # noqa: E402

FULL_CKPT = (ROOT / "results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802"
             "/ea_rg_mappo_s_gate_prior/ppo_seed{S}_1m/actor_critic_update_0700.pt")
WOT_CKPT = (AB_ROOT / "results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804"
            "/w_o_task_support/ppo_seed{S}_1m/actor_critic_update_0100.pt")
SEEDS = [0, 1, 2]
BASE_SEED = 745669
N_EP = 5
SCENARIOS_USED = ["dropout030_delay2_relay_failure", "dropout030_delay2_relay_failure_early"]
W = 20
BLUE = [0, 1, 2]


def make_args(scenario_name, ckpt, seed, ablation, device):
    s = SCENARIOS[scenario_name]
    return argparse.Namespace(
        checkpoint=ckpt, episodes=N_EP, eval_batch_size=1, seed=seed, base_seed=BASE_SEED,
        target_policy="straight", communication_range_scale=s.communication_range_scale,
        communication_dropout_prob=s.communication_dropout_prob,
        message_delay_steps=s.message_delay_steps, radar_dropout_prob=s.radar_dropout_prob,
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        target_prior_position=(0.0, 0.0, 0.0), max_target_message_age_steps=40,
        min_target_confidence=0.0, failed_blue_agent=s.failed_blue_agent,
        node_failure_start_step=s.node_failure_start_step,
        node_failure_duration_steps=s.node_failure_duration_steps, attack_hold_steps=4,
        min_success_step=0, stochastic=False, allow_random_policy=False,
        hidden_dim=64, role_dim=8, intent_dim=8, graph_encoder="multi_relation",
        graph_relation_ablation=ablation, graph_message_ablation="none",
        graph_input_ablation="none", multi_relation_global_residual_weight=0.5,
        device=device,
    )


def main():
    rows = []
    problems = []
    device = "cpu"
    for method, templ, abl in (("full", FULL_CKPT, "none"),
                               ("w_o_task_support", WOT_CKPT, "no_task_support")):
        for s in SEEDS:
            ck = Path(str(templ).replace("{S}", str(s)))
            if not ck.exists():
                problems.append(f"{method} seed{s}: ckpt missing")
                continue
            for sc in SCENARIOS_USED:
                args = make_args(sc, ck, s, abl, device)
                cfg = build_config(args)
                agent, policy_source = build_agent(args, cfg)
                agent = agent.to(device)
                for ep in range(N_EP):
                    env = make_env(cfg, BASE_SEED + ep, training=False)
                    obs, so, g = env.reset()
                    stepinf, reward_sum, act_bytes, ts_traj = [], 0.0, [], []
                    with torch.no_grad():
                        while True:
                            act, _, _, _, _, _, _ = agent.get_action_and_value(
                                torch.as_tensor(obs[None], dtype=torch.float32),
                                torch.as_tensor(g["node_feat"][None], dtype=torch.float32),
                                torch.as_tensor(g["edge_feat"][None], dtype=torch.float32),
                                torch.as_tensor(g["role"][None], dtype=torch.long),
                                torch.as_tensor(g["adj"][None], dtype=torch.float32),
                                torch.as_tensor(so[None], dtype=torch.float32),
                                relation_adj=torch.as_tensor(g["relation_adj"][None], dtype=torch.float32),
                                deterministic=True,
                                intent_label=torch.as_tensor(g["intent_label"][None], dtype=torch.long),
                                detach_intent=False, oracle_intent=False)
                            a = act.cpu().numpy()[0]
                            act_bytes.append(a.astype("<f4").tobytes())
                            ra = g["relation_adj"]
                            ts_traj.append(ra[2, BLUE][:, BLUE].flatten())
                            obs, so, g, rew, done, info = env.step(a)
                            reward_sum += float(np.sum(rew))
                            stepinf.append(info)
                            if np.all(done):
                                break
                    row = build_episode_row(args, policy_source, BASE_SEED + ep, ep,
                                            stepinf, info, reward_sum)
                    f = -1
                    for ii, inf in enumerate(stepinf):
                        if float(inf.get("node_failure_active", 0.0)) > 0.5:
                            f = ii
                            break
                    rec = float(row["post_failure_chain_recovered"]) > 0.5
                    r = float(row["post_failure_first_chain_step"]) if rec else -1.0
                    h = hashlib.sha1(b"".join(act_bytes)).hexdigest()[:16]
                    rows.append({
                        "method": method, "seed": s, "scenario": sc, "episode": ep,
                        "ref_success": float(row["success"]), "ref_collision": float(row["collision"]),
                        "ref_steps": int(row["steps"]), "ref_failure_step": f,
                        "ref_recovered": 1.0 if rec else 0.0,
                        "ref_recovery_step": int(r) if r >= 0 else -1,
                        "ref_action_hash": h,
                        "ts_window_pre_failure": np.stack(ts_traj)[max(0, f - W):f].mean() if f >= 0 else "",
                        "ts_window_early_post": np.stack(ts_traj)[f:min(len(ts_traj), f + W + 1)].mean() if f >= 0 else "",
                    })
    # ---- compare with locked extractor CSVs ----
    with (OUT / "task_support_episode_manifest.csv").open(encoding="utf-8", newline="") as fh:
        man = {(r["method"], r["seed"], r["scenario"], r["episode"]): r
               for r in csv.DictReader(fh)}
    with (OUT / "task_support_relation_trajectory.csv").open(encoding="utf-8", newline="") as fh:
        traj = list(csv.DictReader(fh))

    comp = []
    for r in rows:
        k = (r["method"], str(r["seed"]), r["scenario"], str(r["episode"]))
        m = man.get(k)
        if m is None:
            problems.append(f"missing extractor row {k}")
            continue
        ok_succ = abs(float(m["success"]) - r["ref_success"]) < 1e-9
        ok_steps = int(m["steps"]) == r["ref_steps"]
        ok_fail = int(m["failure_step"]) == r["ref_failure_step"]
        ok_rec = abs(float(m["post_failure_chain_recovered"]) - r["ref_recovered"]) < 1e-9
        ok_hash = m["action_hash"] == r["ref_action_hash"]
        # independent window recompute: compare pre_failure / early_post from trajectory CSV
        ws = {t["window"]: t for t in traj
              if (t["method"], t["seed"], t["scenario"], t["episode"]) == k}
        ok_pre = ""
        if "pre_failure" in ws and r["ts_window_pre_failure"] != "":
            ok_pre = abs(float(ws["pre_failure"]["mean_strength"]) - r["ts_window_pre_failure"]) < 1e-6
        ok_early = ""
        if "early_post_failure" in ws and r["ts_window_early_post"] != "":
            ok_early = abs(float(ws["early_post_failure"]["mean_strength"]) - r["ts_window_early_post"]) < 1e-6
        comp.append({**r, "ok_success": ok_succ, "ok_steps": ok_steps, "ok_fail": ok_fail,
                     "ok_rec": ok_rec, "ok_hash": ok_hash,
                     "ok_pre_window": ("" if ok_pre == "" else bool(ok_pre)),
                     "ok_early_window": ("" if ok_early == "" else bool(ok_early))})
        if not (ok_succ and ok_steps and ok_fail and ok_rec):
            problems.append(f"EVENT MISMATCH {k}: ref={r['ref_success']}/{r['ref_steps']}/{r['ref_failure_step']}/"
                            f"{r['ref_recovered']} extr={m['success']}/{m['steps']}/{m['failure_step']}/"
                            f"{m['post_failure_chain_recovered']}")
        if not ok_hash:
            problems.append(f"HASH MISMATCH {k}: ref={r['ref_action_hash']} extr={m['action_hash']}")

    with (OUT / "task_support_behavioral_equiv.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comp[0].keys()))
        w.writeheader(); w.writerows(comp)

    n_ev = sum(1 for c in comp if c["ok_success"] and c["ok_steps"] and c["ok_fail"] and c["ok_rec"])
    n_hash = sum(1 for c in comp if c["ok_hash"])
    n_pre = sum(1 for c in comp if c["ok_pre_window"] is True or c["ok_pre_window"] == "True")
    n_early = sum(1 for c in comp if c["ok_early_window"] is True or c["ok_early_window"] == "True")
    n_pre_tot = sum(1 for c in comp if c["ok_pre_window"] in (True, False) or c["ok_pre_window"] in ("True", "False"))
    n_early_tot = sum(1 for c in comp if c["ok_early_window"] in (True, False) or c["ok_early_window"] in ("True", "False"))
    print(f"checked episodes: {len(comp)}")
    print(f"event-match (success/steps/failure/recovered): {n_ev}/{len(comp)}")
    print(f"action-hash match: {n_hash}/{len(comp)}")
    print(f"independent pre_failure window match: {n_pre}/{n_pre_tot}")
    print(f"independent early_post window match: {n_early}/{n_early_tot}")
    print(f"\nOVERALL: {'PASS' if not problems else 'FAIL'}")
    for p in problems[:20]:
        print("  -", p)
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
