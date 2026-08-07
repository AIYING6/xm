# run_p3a_ood_eval.py — P3-A.3a formal zero-shot OOD performance collection.
#
# Inherits the ENTIRE frozen P3-A.2 chain (protocol v1.1, impl v1.1.3,
# preflight lock v1.1) and switches the SAME evaluator from exposure-only to
# recording full episode-level performance endpoints.
#
# Hard rules (frozen):
#   methods      = Full / MAPPO / HAPPO / Wider-SG
#   train seeds  = 0 / 1 / 2
#   cells        = G1 G2 M1 M2 C1 C2 J1
#   episodes     = 100 per method x seed x cell  -> 8400 total
#   failure start= 25, duration = 80, horizon = 260
#   tau primary  = 80, tau full = 220
#   recovery clock = P1 frozen: T_event = stable_window_start - failure_start
#                    T_censor = steps - failure_start
#
# Forbidden: retrain / fine-tune / checkpoint reselection / OOD severity change /
# failure-parameter change / seed-schedule change / cell adjustment based on
# intermediate results.
#
# The runner prints ONLY completion counters ("Full s0 G1: 100/100 completed").
# It must NOT print success / RMST / reward / method ranking in real time.
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.p3a_mappo_loader import (  # noqa: E402
    build_config as mappo_build_config,
    load_agent_strict,
    role_onehot,
    sha256_file,
)
from scripts.p3a_ood_cells import (  # noqa: E402
    CELLS, EPISODES_PER_CELL, EVAL_BASE_SEED, FAILURE_DURATION, FAILURE_START,
    HORIZON, OUT_ROOT, PRIMARY_METHODS, TRAIN_SEEDS, checkpoint_path,
    checkpoint_update, common_eval_overrides, cell_overrides,
)
from scripts.run_p3a_ood_preflight import make_args, _METHOD_GRAPH_ENCODER  # noqa: E402

# --- frozen provenance tags (P3-A.2 lock) ---
PROTOCOL_TAG = "p3a-ood-protocol-v1.1"
IMPLEMENTATION_TAG = "p3a-ood-eval-impl-v1.1.3"
PREFLIGHT_LOCK_TAG = "p3a-ood-preflight-lock-v1.1"

TAU_PRIMARY = 80
TAU_FULL = 220

RAW_COLUMNS = [
    "method", "train_seed", "cell", "episode_id", "eval_seed",
    "checkpoint_path", "checkpoint_sha256", "checkpoint_update",
    "protocol_tag", "implementation_tag", "preflight_lock_tag",
    "steps", "failure_start_step", "failure_exposed",
    "success", "collision", "post_failure_chain_recovered",
    "recovery_window_start_step", "recovery_event_time", "censor_time",
    "recovery_observed", "reward",
]


def build_raw_row(
    method: str,
    train_seed: str,
    cell: str,
    episode_id: int,
    args: argparse.Namespace,
    checkpoint_sha: str,
    step_infos: list[dict],
    final: dict,
    reward_sum: float,
) -> dict:
    """One episode-level row. Recovery clock is P1-frozen (reused from the
    held-out evaluator's post_failure_recovery_metrics)."""
    from scripts.evaluate_ri_gmappo_3d import post_failure_recovery_metrics  # noqa: E402

    rec = post_failure_recovery_metrics(step_infos, args)
    start = float(args.node_failure_start_step)
    steps = float(final["step"])
    recovered = float(rec.get("post_failure_chain_recovered", 0.0)) > 0.5
    # P1 frozen clock:
    #   recovered: T_event = stable_window_start - start  (= recovered_only_steps)
    #   censored : T_censor = steps - start                (= recovery_steps_censored)
    t_event = float(rec.get("post_failure_chain_recovered_only_steps", -1.0))
    t_censor = float(rec.get("post_failure_chain_recovery_steps_censored", -1.0))
    recovery_window_start = start + t_event if recovered else -1.0
    return {
        "method": method,
        "train_seed": train_seed,
        "cell": cell,
        "episode_id": int(episode_id),
        "eval_seed": EVAL_BASE_SEED + int(episode_id),
        "checkpoint_path": str(checkpoint_path(method, train_seed)),
        "checkpoint_sha256": checkpoint_sha,
        "checkpoint_update": checkpoint_update(method, train_seed),
        "protocol_tag": PROTOCOL_TAG,
        "implementation_tag": IMPLEMENTATION_TAG,
        "preflight_lock_tag": PREFLIGHT_LOCK_TAG,
        "steps": steps,
        "failure_start_step": start,
        "failure_exposed": float(steps >= start),
        "success": float(final.get("success", 0.0)),
        "collision": float(final.get("collision", 0.0)),
        "post_failure_chain_recovered": float(rec.get("post_failure_chain_recovered", 0.0)),
        "recovery_window_start_step": recovery_window_start,
        "recovery_event_time": t_event if recovered else -1.0,
        "censor_time": t_censor if not recovered else -1.0,
        "recovery_observed": float(recovered),
        "reward": float(reward_sum),
    }


def run_cell(method: str, seed: str, cell: str, device: str, eval_batch_size: int) -> list[dict]:
    """Run 100 episodes of one method x seed x cell. Collects full endpoints."""
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_config as ri_build_config  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_agent as ri_build_agent  # noqa: E402
    from scripts.evaluate_happo_3d import build_config as ha_build_config  # noqa: E402
    from scripts.evaluate_happo_3d import build_agent as ha_build_agent  # noqa: E402

    ck = checkpoint_path(method, seed)
    over = common_eval_overrides()
    over.update(cell_overrides(cell))
    a = make_args(ck, seed, device, eval_batch_size, over, method=method)
    if method == "mappo":
        cfg = mappo_build_config(a)
        agent, _ = load_agent_strict(a, cfg)
    elif method == "happo":
        cfg = ha_build_config(a)
        agent, _ = ha_build_agent(a, cfg)
    else:
        cfg = ri_build_config(a)
        agent, _ = ri_build_agent(a, cfg)
    agent = agent.to(device)
    ck_sha = sha256_file(ck)
    rows: list[dict] = []
    with torch.no_grad():
        for batch_start in range(0, EPISODES_PER_CELL, a.eval_batch_size):
            batch_eps = list(range(batch_start, min(EPISODES_PER_CELL, batch_start + a.eval_batch_size)))
            envs, obs_l, share_l, graph_l, step_l, rew_l, role_l = [], [], [], [], [], [], []
            active = []
            for ep in batch_eps:
                env = make_env(cfg, EVAL_BASE_SEED + ep, training=False)
                obs, so, g = env.reset()
                envs.append(env); obs_l.append(obs); share_l.append(so); graph_l.append(g)
                step_l.append([]); rew_l.append(0.0); role_l.append(np.asarray(g["role"], dtype=np.int64)[: env.num_agents])
                active.append(True)
            while any(active):
                ai = [i for i, ac in enumerate(active) if ac]
                g = stack_graphs([graph_l[i] for i in ai])
                n_env = len(ai)
                if method == "mappo":
                    obs_t = torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device)
                    num_agents = envs[ai[0]].num_agents
                    ro_batch = np.stack([role_onehot(role_l[i].reshape(1, -1), agent.role_dim)[0] for i in ai])
                    ro_t = torch.as_tensor(ro_batch, dtype=torch.float32, device=device)
                    actor_in = torch.cat([obs_t.reshape(n_env * num_agents, -1),
                                          ro_t.reshape(n_env * num_agents, -1)], dim=-1)
                    logits = agent.actor(actor_in)
                    act = torch.argmax(logits, dim=-1).reshape(n_env, num_agents).cpu().numpy()
                elif method == "happo":
                    actions, *_ = agent.get_action_and_value(
                        torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device),
                        torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(g["role"], dtype=torch.long, device=device),
                        torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                        torch.as_tensor(np.stack([share_l[i] for i in ai]), dtype=torch.float32, device=device),
                        relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                        deterministic=True,
                    )
                    act = actions.cpu().numpy()
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
                    rew_l[env_i] += float(np.sum(rew))
                    step_l[env_i].append(info)
                    role_l[env_i] = np.asarray(graph_l[env_i]["role"], dtype=np.int64)[: envs[env_i].num_agents]
                    if np.all(done):
                        rows.append(build_raw_row(
                            method=method, train_seed=seed, cell=cell,
                            episode_id=batch_eps[env_i], args=a, checkpoint_sha=ck_sha,
                            step_infos=step_l[env_i], final=info, reward_sum=rew_l[env_i],
                        ))
                        active[env_i] = False
    return rows


def completeness_audit(rows: list[dict]) -> dict:
    """Mechanical completeness check (no performance comparison)."""
    keys = [(r["method"], r["train_seed"], r["cell"], r["episode_id"]) for r in rows]
    expected = {(m, s, c, e)
                for m in PRIMARY_METHODS for s in TRAIN_SEEDS
                for c in CELLS for e in range(EPISODES_PER_CELL)}
    key_set = set(keys)
    missing = sorted(expected - key_set)
    duplicates = len(keys) - len(key_set)
    sha_bad = [k for k in set((r["method"], r["train_seed"]) for r in rows)
               if any(r["checkpoint_sha256"] == "" for r in rows if (r["method"], r["train_seed"]) == k)]
    return {
        "rows": len(rows),
        "expected_rows": 4 * 3 * 7 * EPISODES_PER_CELL,
        "unique_cells": len(set((r["method"], r["train_seed"], r["cell"]) for r in rows)),
        "missing": missing,
        "duplicates": duplicates,
        "empty_sha_methods": sha_bad,
        "exposure_violations": sum(1 for r in rows if float(r["failure_exposed"]) < 0.5),
        "runtime_failures": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--out", default=None, help="raw CSV path (default OUT_ROOT/p3a_ood_raw_results.csv)")
    args = parser.parse_args()
    device = args.device

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else OUT_ROOT / "p3a_ood_raw_results.csv"

    all_rows: list[dict] = []
    for method in PRIMARY_METHODS:
        for seed in TRAIN_SEEDS:
            for cell in sorted(CELLS):
                rows = run_cell(method, seed, cell, device, args.eval_batch_size)
                all_rows.extend(rows)
                # completion-only log; NO performance endpoint may be shown here
                print(f"{method} s{seed} {cell}: {len(rows)}/100 completed", flush=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RAW_COLUMNS)
        w.writeheader()
        w.writerows(all_rows)

    audit = completeness_audit(all_rows)
    print(f"\nrows={audit['rows']} expected={audit['expected_rows']} "
          f"unique_cells={audit['unique_cells']} missing={len(audit['missing'])} "
          f"duplicates={audit['duplicates']} exposure_violations={audit['exposure_violations']}")
    if audit["missing"] or audit["duplicates"] or audit["empty_sha_methods"] or audit["exposure_violations"]:
        print("COMPLETENESS AUDIT FAILED")
        return 1
    print("COMPLETENESS AUDIT PASS — raw results locked (analysis deferred to P3-A.3b)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
