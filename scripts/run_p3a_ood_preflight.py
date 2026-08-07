# run_p3a_ood_preflight.py — P3-A exposure-only preflight (protocol v1.1, impl v1.1.2).
# Checks ONLY failure exposure (steps >= failure_start) across 84 primary cells.
# It must NOT output or summarize success / recovery / t_rec / RMST / reward / rankings.
# Hard gate: exposure_rate >= 0.99 in all 84 cells.
#
# Before any rollout, a Gate-3 asset/load audit runs (12 method x seed checkpoints):
#   - 12/12 files exist
#   - 12/12 SHA256 == copied frozen held-out manifest
#   - agent architecture == held-out architecture (MAPPO -> MAPPOAgent3D STRICT)
#   - load signature == held-out behavior
# Any audit failure => STOP (exit 1) without starting episode 0.
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
    compute_load_signature,
    load_agent_strict,
    role_onehot,
    sha256_file as mappo_sha256,
)
from scripts.p3a_ood_cells import (  # noqa: E402
    EPISODES_PER_CELL, CELLS, EVAL_BASE_SEED, EXPOSURE_GATE, FAILED_BLUE_AGENT,
    FAILURE_DURATION, FAILURE_START, HORIZON, OUT_ROOT, PRIMARY_METHODS, TRAIN_SEEDS,
    checkpoint_path, checkpoint_update, common_eval_overrides, cell_overrides,
    load_held_out_manifest,
)


# graph_encoder per method (matches formal held-out architecture):
#   full_ea_rg           -> multi_relation (EA-RG Full)
#   param_matched_single -> single        (Wider Single-Graph)
#   mappo                -> no_graph      (STRICT MAPPOAgent3D; value irrelevant to loader)
#   happo                -> (HAPPO evaluator; value unused)
_METHOD_GRAPH_ENCODER = {
    "full_ea_rg": "multi_relation",
    "param_matched_single": "single",
    "mappo": "no_graph",
    "happo": "no_graph",
}


def make_args(checkpoint, seed, device, eval_batch_size, overrides, method="full_ea_rg"):
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
        hidden_dim=64, role_dim=8, intent_dim=8,
        graph_encoder=_METHOD_GRAPH_ENCODER[method],
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


def run_checkpoint_audit(device, eval_batch_size) -> tuple[list[dict], bool]:
    """Gate-3 asset/load audit. No rollout is allowed until this passes."""
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_config as ri_build_config  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_agent as ri_build_agent  # noqa: E402
    from scripts.evaluate_happo_3d import build_config as ha_build_config  # noqa: E402
    from scripts.evaluate_happo_3d import build_agent as ha_build_agent  # noqa: E402

    manifest = load_held_out_manifest()
    rows: list[dict] = []
    failures: list[str] = []
    for method in PRIMARY_METHODS:
        for seed in TRAIN_SEEDS:
            ck = checkpoint_path(method, seed)
            man = manifest[(method, seed)]
            exists = ck.exists()
            actual_sha = mappo_sha256(ck) if exists else ""
            sha_match = bool(exists) and actual_sha == man["sha256"]
            a = make_args(ck, seed, device, eval_batch_size, common_eval_overrides(), method=method)
            loader = ""
            agent_class = ""
            matched = partial = skipped = -1
            strict_load = False
            row_ok = exists and sha_match
            if row_ok:
                try:
                    if method == "mappo":
                        cfg = mappo_build_config(a)
                        agent, audit = load_agent_strict(a, cfg)
                        loader = "p3a_mappo_loader.load_agent_strict"
                        agent_class = audit["agent_class"]
                        matched, partial, skipped = audit["matched_tensors"], audit["partial_tensors"], audit["skipped_tensors"]
                        strict_load = True
                    elif method == "happo":
                        cfg = ha_build_config(a)
                        agent, _ = ha_build_agent(a, cfg)
                        sig = compute_load_signature(agent, str(ck), torch.device(device))
                        loader = "evaluate_happo_3d.build_agent"
                        agent_class = type(agent).__name__
                        matched, partial, skipped = sig["matched_tensors"], sig["partial_tensors"], sig["skipped_tensors"]
                    else:
                        cfg = ri_build_config(a)
                        agent, _ = ri_build_agent(a, cfg)
                        sig = compute_load_signature(agent, str(ck), torch.device(device))
                        loader = "evaluate_ri_gmappo_3d.build_agent"
                        agent_class = type(agent).__name__
                        matched, partial, skipped = sig["matched_tensors"], sig["partial_tensors"], sig["skipped_tensors"]
                except Exception as exc:  # noqa: BLE001
                    row_ok = False
                    failures.append(f"{method} seed{seed}: agent/load failed: {exc}")
            if row_ok and strict_load and (partial != 0 or skipped != 0):
                row_ok = False
                failures.append(
                    f"{method} seed{seed}: strict load must have 0 partial/0 skipped, got {partial}/{skipped}")
            if row_ok and not strict_load and (partial != 0 or skipped != 0):
                row_ok = False
                failures.append(
                    f"{method} seed{seed}: held-out load signature must have 0 partial/0 skipped, got {partial}/{skipped}")
            rows.append({
                "method": method, "train_seed": seed, "checkpoint_update": checkpoint_update(method, seed),
                "checkpoint_path": str(ck), "expected_sha256": man["sha256"], "actual_sha256": actual_sha,
                "sha_match": "1" if sha_match else "0", "loader": loader, "agent_class": agent_class,
                "matched_tensors": matched, "partial_tensors": partial, "skipped_tensors": skipped,
                "strict_load": "1" if strict_load else "0", "pass": "1" if row_ok else "0",
            })
            print(
                f"AUDIT {method} s{seed} update={checkpoint_update(method, seed)} "
                f"sha={'OK' if sha_match else 'MISMATCH'} "
                f"{agent_class} {matched}/{partial}/{skipped} "
                f"{'PASS' if row_ok else 'FAIL'}", flush=True)

    audit_path = OUT_ROOT / "p3a_checkpoint_audit.csv"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    all_pass = all(r["pass"] == "1" for r in rows) and not failures
    return rows, all_pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out-root", required=True, help="kept for interface compatibility")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--eval-batch-size", type=int, default=8)
    args = parser.parse_args()
    device = args.device

    # ---- Gate 3: asset/load audit BEFORE any rollout ----
    audit_rows, audit_ok = run_checkpoint_audit(device, args.eval_batch_size)
    if not audit_ok:
        print("\nCHECKPOINT AUDIT FAILED — STOP before episode 0.", flush=True)
        return 1
    print(f"\nCHECKPOINT AUDIT PASS: {len(audit_rows)}/12 assets verified.", flush=True)

    from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_config as ri_build_config  # noqa: E402
    from scripts.evaluate_ri_gmappo_3d import build_agent as ri_build_agent  # noqa: E402
    from scripts.evaluate_happo_3d import build_config as ha_build_config  # noqa: E402
    from scripts.evaluate_happo_3d import build_agent as ha_build_agent  # noqa: E402

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
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
                a = make_args(ck, seed, device, args.eval_batch_size, over, method=method)
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
                exposed = 0
                total = 0
                with torch.no_grad():
                    for batch_start in range(0, EPISODES_PER_CELL, a.eval_batch_size):
                        batch_eps = list(range(batch_start, min(EPISODES_PER_CELL, batch_start + a.eval_batch_size)))
                        envs, obs_l, share_l, graph_l = [], [], [], []
                        role_l = []
                        for ep in batch_eps:
                            env = make_env(cfg, EVAL_BASE_SEED + ep, training=False)
                            obs, so, g = env.reset()
                            envs.append(env); obs_l.append(obs); share_l.append(so); graph_l.append(g)
                            role_l.append(np.asarray(g["role"], dtype=np.int64)[: env.num_agents])
                        active = [True] * len(batch_eps)
                        while any(active):
                            ai = [i for i, ac in enumerate(active) if ac]
                            g = stack_graphs([graph_l[i] for i in ai])
                            n_env = len(ai)
                            if method == "mappo":
                                obs_t = torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device)
                                num_agents = envs[ai[0]].num_agents
                                ro_batch = np.stack([
                                    role_onehot(role_l[i].reshape(1, -1), agent.role_dim)[0] for i in ai])
                                ro_t = torch.as_tensor(ro_batch, dtype=torch.float32, device=device)
                                actor_in = torch.cat([
                                    obs_t.reshape(n_env * num_agents, -1),
                                    ro_t.reshape(n_env * num_agents, -1),
                                ], dim=-1)
                                logits = agent.actor(actor_in)
                                act = torch.argmax(logits, dim=-1).reshape(n_env, num_agents).cpu().numpy()
                            elif method == "happo":
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
                                role_l[env_i] = np.asarray(graph_l[env_i]["role"], dtype=np.int64)[: envs[env_i].num_agents]
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
                    "checkpoint_sha256": mappo_sha256(ck),
                    "checkpoint_update": checkpoint_update(method, seed),
                    "ood_config": str(cell_overrides(cell)),
                })
                if not ok:
                    failures.append(f"{method} seed{seed} {cell}: exposure {rate:.4f} < {EXPOSURE_GATE}")
                print(f"{method} s{seed} {cell}: exposure {rate:.4f} ({exposed}/{total})", flush=True)

    exposure_path = OUT_ROOT / "p3a_preflight_exposure.csv"
    with exposure_path.open("w", encoding="utf-8", newline="") as f:
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
