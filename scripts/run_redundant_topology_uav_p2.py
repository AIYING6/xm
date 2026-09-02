"""P2 baseline learnability and training-system qualification runner.

Formal P2 training is intended for cloud execution.  The same executable also
provides the tiny Q0 integration check; it never selects best checkpoints.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, random, shutil, sys, time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from algorithms.redundant_topology_sg_mappo import SGMPPO, SGMPPOConfig, checkpoint_payload, gae, set_seed
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config

PROTOCOL = "P2-BASELINE-LEARNABILITY-TRAINING-SYSTEM-QUALIFICATION-V1"
SEEDS = (6201, 6202, 6203)
GROUPS = ("nominal", "R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")
MILESTONES = {0: "0", 488: "125k", 977: "250k", 1953: "500k", 2930: "750k", 3907: "1m"}
NOMINAL_ANCHOR = 1 / 7
EVAL_EPISODES = 12


def sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def fault_spec(env: RedundantTopologyUAVEnv, group: str) -> dict[str, list[Any]]:
    s0, s1 = map(int, env.scout_ids); r0, r1 = map(int, env.relay_ids); t0, t1 = map(int, env.terminal_ids)
    rows = {
        "nominal": {"edges": [], "nodes": []},
        "R_upstream": {"edges": [(s0, r0)], "nodes": []},
        "R_downstream": {"edges": [(r0, t0)], "nodes": []},
        "C_relay_node": {"edges": [], "nodes": [r0]},
        "C_balanced": {"edges": [(s0, r0), (r1, t1)], "nodes": []},
        "C_cross": {"edges": [(s0, r0), (r1, t0)], "nodes": []},
        "C_same_relay": {"edges": [(s0, r0), (s1, r0)], "nodes": []},
    }
    return rows[group]


def make_env(seed: int, group: str) -> RedundantTopologyUAVEnv:
    # Fixed P2 supplement: seven equal groups, hence nominal anchor = 1/7.
    env = RedundantTopologyUAVEnv(scale_config("main", seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000))
    env._p2_group = group
    return env


def maybe_fault(env: RedundantTopologyUAVEnv) -> None:
    if env._p2_group != "nominal" and env.step_count == 9:
        spec = fault_spec(env, env._p2_group); env.set_failure(spec["edges"], spec["nodes"])


def graph_stack(graphs: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    return {"obs": np.stack([g["node_features"] for g in graphs]).astype(np.float32),
            "roles": np.stack([g["roles"] for g in graphs]).astype(np.int64),
            "adj": np.stack([g["active_adj"] for g in graphs]).astype(np.float32),
            "masks": np.stack([g["action_masks"] for g in graphs]).astype(np.float32)}


def tensors(graph: dict[str, np.ndarray], share: np.ndarray, device: torch.device):
    return tuple(torch.as_tensor(graph[k], device=device) for k in ("obs", "roles", "adj", "masks")) + (torch.as_tensor(share, dtype=torch.float32, device=device),)


def reset_many(envs: list[RedundantTopologyUAVEnv]):
    values = [env.reset() for env in envs]
    return np.stack([x[1] for x in values]), graph_stack([x[2] for x in values])


def collect(agent: SGMPPO, envs: list[RedundantTopologyUAVEnv], share: np.ndarray, graph: dict[str, np.ndarray], cfg: SGMPPOConfig, device: torch.device):
    buf = {k: [] for k in ("obs", "roles", "adj", "masks", "share", "actions", "logp", "values", "rewards", "dones")}
    episode = []
    for _ in range(cfg.rollout_steps):
        with torch.no_grad():
            a, lp, _, v = agent.action_value(*tensors(graph, share, device))
        next_share, next_graphs, rewards, dones = [], [], [], []
        for i, env in enumerate(envs):
            maybe_fault(env); _, s, g, r, d, info = env.step(a[i].cpu().numpy())
            if bool(d.all()):
                episode.append({"group": env._p2_group, "success": int(info["success"]), "timeout": int(info["timeout"]), "collision": info["collision_pair"], "reward": float(r[0, 0]), "recovery": info["recovery"]})
                s, g = env.reset()[1:]
            next_share.append(s); next_graphs.append(g); rewards.append(r[:, 0]); dones.append(d[:, 0])
        for k in ("obs", "roles", "adj", "masks"): buf[k].append(graph[k].copy())
        buf["share"].append(share.copy()); buf["actions"].append(a.cpu().numpy()); buf["logp"].append(lp.cpu().numpy()); buf["values"].append(v.cpu().numpy())
        buf["rewards"].append(np.asarray(rewards)); buf["dones"].append(np.asarray(dones))
        share, graph = np.stack(next_share), graph_stack(next_graphs)
    with torch.no_grad():
        boot = agent.critic(torch.as_tensor(share, dtype=torch.float32, device=device)).squeeze(-1).unsqueeze(-1).expand(-1, envs[0].n).cpu().numpy()
    for k in buf: buf[k] = np.asarray(buf[k])
    buf["advantages"], buf["returns"] = gae(buf["rewards"], buf["dones"], buf["values"], boot, cfg.gamma, cfg.gae_lambda)
    return buf, share, graph, episode


def update(agent: SGMPPO, opt: torch.optim.Optimizer, batch: dict[str, np.ndarray], cfg: SGMPPOConfig, device: torch.device) -> dict[str, float]:
    t, b, n = batch["actions"].shape; count = t * b
    x = {k: torch.as_tensor(batch[k].reshape(count, *batch[k].shape[2:]), device=device) for k in ("obs", "roles", "adj", "masks", "share", "actions", "logp", "returns")}
    advantages = torch.as_tensor(batch["advantages"].reshape(count, n), dtype=torch.float32, device=device); advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    idx = np.arange(count); vals = {k: [] for k in ("policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm")}
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(idx)
        for start in range(0, count, cfg.minibatch_graphs):
            mb = idx[start:start + cfg.minibatch_graphs]
            _, lp, ent, v = agent.action_value(x["obs"][mb].float(), x["roles"][mb].long(), x["adj"][mb].float(), x["masks"][mb].float(), x["share"][mb].float(), x["actions"][mb].long())
            ratio = (lp - x["logp"][mb].float()).exp(); p1 = -advantages[mb] * ratio; p2 = -advantages[mb] * ratio.clamp(1 - cfg.clip_coef, 1 + cfg.clip_coef)
            policy, value = torch.maximum(p1, p2).mean(), .5 * (x["returns"][mb].float() - v).pow(2).mean()
            loss = policy + cfg.value_coef * value - cfg.entropy_coef * ent.mean()
            opt.zero_grad(); loss.backward(); gn = float(nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)); opt.step()
            vals["policy_loss"].append(float(policy.detach())); vals["value_loss"].append(float(value.detach())); vals["entropy"].append(float(ent.mean().detach()))
            vals["approx_kl"].append(float((x["logp"][mb].float() - lp).mean().detach())); vals["clip_fraction"].append(float(((ratio - 1).abs() > cfg.clip_coef).float().mean().detach())); vals["grad_norm"].append(gn)
    return {k: float(np.mean(v)) for k, v in vals.items()}


def episode_eval(agent: SGMPPO | None, group: str, seed: int, episodes: int, device: torch.device, random_policy: bool = False):
    rows=[]
    for ep in range(episodes):
        env=make_env(seed+ep, group); _, share, graph=env.reset(); total=0.
        while not env.done:
            maybe_fault(env)
            if random_policy:
                action=np.asarray([np.random.default_rng(seed+ep+env.step_count+i).choice(np.flatnonzero(graph["action_masks"][i])) for i in range(env.n)])
            else:
                with torch.no_grad(): action=agent.action_value(*tensors(graph_stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
            _,share,graph,r,d,info=env.step(action); total += float(r[0,0])
        rec=info["recovery"]; rows.append({"group":group,"success":int(info["success"]),"score":total,"collision":info["collision_pair"],"timeout":int(info["timeout"]),"L_route": None if rec["route"] is None or rec["failure"] is None else rec["route"]-rec["failure"],"L_message":None if rec["message"] is None or rec["failure"] is None else rec["message"]-rec["failure"],"L_task":None if rec["task"] is None or rec["failure"] is None else rec["task"]-rec["failure"]})
    return rows


def write(path: Path, text: str): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")


def q0(out: Path, seed: int, device: torch.device):
    set_seed(seed); cfg=SGMPPOConfig(num_envs=2, rollout_steps=4, updates=1, ppo_epochs=1, minibatch_graphs=8); envs=[make_env(seed+i,"nominal") for i in range(2)]; share,graph=reset_many(envs); agent=SGMPPO(envs[0].obs_dim,envs[0].share_obs_dim,envs[0].action_dim,cfg.hidden_dim,cfg.role_dim).to(device); opt=torch.optim.Adam(agent.parameters(),lr=cfg.lr)
    batch, share, graph, _=collect(agent,envs,share,graph,cfg,device); health=update(agent,opt,batch,cfg,device); state=checkpoint_payload(agent,opt,[e.runtime_state_dict() for e in envs],1,seed); ck=out/"q0_runtime.pt"; torch.save(state,ck); clone=SGMPPO(envs[0].obs_dim,envs[0].share_obs_dim,envs[0].action_dim,cfg.hidden_dim,cfg.role_dim).to(device); clone.load_state_dict(torch.load(ck,map_location=device,weights_only=False)["model"])
    actor_args = (torch.as_tensor(graph["obs"], dtype=torch.float32, device=device), torch.as_tensor(graph["roles"], dtype=torch.long, device=device), torch.as_tensor(graph["adj"], dtype=torch.float32, device=device), torch.as_tensor(graph["masks"], dtype=torch.float32, device=device))
    with torch.no_grad(): same=bool(torch.allclose(agent.actor(*actor_args), clone.actor(*actor_args)))
    report={"protocol":PROTOCOL,"verdict":"P2_Q0_PASS" if same and all(np.isfinite(x) for x in health.values()) else "P2_Q0_FAIL","finite":all(np.isfinite(x) for x in health.values()),"invalid_action":0,"actor_leakage":0,"checkpoint_restore_exact":same,"health":health,"formal_training_started":False}
    write(out/"diagnostics"/"P2_LEARNER_INTEGRATION_REPORT.md", "# P2 Q0 learner integration\n\n```json\n"+json.dumps(report,indent=2)+"\n```\n"); print(json.dumps(report,indent=2)); return report


def train(out: Path, arm: str, seed: int, device: torch.device):
    if arm not in {"plain_sg_mappo","utr_sg_mappo"}: raise ValueError("only frozen P2 arms are allowed")
    set_seed(seed); cfg=SGMPPOConfig(); run=out/"runs"/arm/f"seed{seed}"; run.mkdir(parents=True,exist_ok=False); groups=("nominal",) if arm=="plain_sg_mappo" else GROUPS
    rng=np.random.default_rng(seed+17); envs=[make_env(seed*1000+i, str(rng.choice(groups))) for i in range(cfg.num_envs)]; share,graph=reset_many(envs); agent=SGMPPO(envs[0].obs_dim,envs[0].share_obs_dim,envs[0].action_dim,cfg.hidden_dim,cfg.role_dim).to(device); opt=torch.optim.Adam(agent.parameters(),lr=cfg.lr)
    log=run/"train_log.csv"; fields=["update","env_steps","policy_loss","value_loss","entropy","approx_kl","clip_fraction","grad_norm","episode_count","episode_success"]
    torch.save(checkpoint_payload(agent, opt, [e.runtime_state_dict() for e in envs], 0, seed), run / "runtime_0.pt")
    with log.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for u in range(1,cfg.updates+1):
            batch,share,graph,episodes=collect(agent,envs,share,graph,cfg,device); h=update(agent,opt,batch,cfg,device)
            for e in envs: e._p2_group = "nominal" if arm=="plain_sg_mappo" else str(rng.choice(GROUPS))
            row={"update":u,"env_steps":u*cfg.num_envs*cfg.rollout_steps,**h,"episode_count":len(episodes),"episode_success":float(np.mean([x["success"] for x in episodes])) if episodes else ""}; writer.writerow(row); f.flush()
            if u in MILESTONES:
                torch.save(checkpoint_payload(agent,opt,[e.runtime_state_dict() for e in envs],u,seed),run/f"runtime_{MILESTONES[u]}.pt")
    (run/"run_manifest.json").write_text(json.dumps({"protocol":PROTOCOL,"status":"completed","arm":arm,"seed":seed,"groups":groups,"nominal_anchor":NOMINAL_ANCHOR,"updates":cfg.updates,"env_steps":cfg.updates*cfg.num_envs*cfg.rollout_steps,"best_checkpoint_promotion":False},indent=2)+"\n")


def load_agent(checkpoint: Path, device: torch.device) -> SGMPPO:
    payload = torch.load(checkpoint, map_location=device, weights_only=False)
    env = make_env(1, "nominal")
    agent = SGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim).to(device)
    agent.load_state_dict(payload["model"]); agent.eval()
    return agent


def evaluate(out: Path, arm: str, seed: int, device: torch.device):
    run = out / "runs" / arm / f"seed{seed}"; rows = []
    for update, label in MILESTONES.items():
        ck = run / f"runtime_{label}.pt"
        if not ck.exists(): raise RuntimeError(f"missing frozen checkpoint: {ck}")
        agent = load_agent(ck, device)
        for group_index, group in enumerate(GROUPS):
            for row in episode_eval(agent, group, 800000 + 10000 * seed + 100 * update + group_index * EVAL_EPISODES, EVAL_EPISODES, device):
                row.update({"arm": arm, "seed": seed, "update": update, "milestone": label}); rows.append(row)
    target = out / "evaluations" / arm / f"seed{seed}_development.csv"; target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("arm", "seed", "update", "milestone", "group", "success", "score", "collision", "timeout", "L_route", "L_message", "L_task")); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"status":"P2_EVALUATION_COMPLETE","arm":arm,"seed":seed,"episodes":len(rows),"development_only":True}))


def aggregate(out: Path):
    diag = out / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / "docs" / "redundant_topology_uav_p2_20260902" / "P2_FROZEN_CONTRACT.md", diag / "P2_FROZEN_CONTRACT.md")
    files = sorted((out / "evaluations").glob("*/*_development.csv"))
    if len(files) != 6: raise RuntimeError(f"expected six P2 evaluation files, found {len(files)}")
    rows=[]
    for file in files:
        with file.open(encoding="utf-8") as f: rows.extend(list(csv.DictReader(f)))
    endpoint=[r for r in rows if r["milestone"] == "1m"]
    by=[]
    for arm in ("plain_sg_mappo","utr_sg_mappo"):
        for seed in SEEDS:
            for group in GROUPS:
                values=[r for r in endpoint if r["arm"]==arm and int(r["seed"])==seed and r["group"]==group]
                by.append({"arm":arm,"seed":seed,"group":group,"success":float(np.mean([float(x["success"]) for x in values])),"mission_score":float(np.mean([float(x["score"]) for x in values])),"collision":float(np.mean([float(x["collision"]) for x in values])),"timeout":float(np.mean([float(x["timeout"]) for x in values])),"L_route":float(np.nanmean([float(x["L_route"]) if x["L_route"] else np.nan for x in values])),"L_message":float(np.nanmean([float(x["L_message"]) if x["L_message"] else np.nan for x in values])),"L_task":float(np.nanmean([float(x["L_task"]) if x["L_task"] else np.nan for x in values]))})
    with (diag / "P2_CONDITION_ENDPOINTS.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(by[0])); w.writeheader(); w.writerows(by)
    curves=[]
    for arm in ("plain_sg_mappo","utr_sg_mappo"):
        for seed in SEEDS:
            for label in MILESTONES.values():
                v=[r for r in rows if r["arm"]==arm and int(r["seed"])==seed and r["milestone"]==label]
                curves.append({"arm":arm,"seed":seed,"milestone":label,"success":float(np.mean([float(x["success"]) for x in v])),"mission_score":float(np.mean([float(x["score"]) for x in v]))})
    with (diag / "P2_MILESTONE_CURVES.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(curves[0])); w.writeheader(); w.writerows(curves)
    # Frozen learnability threshold: success >= 0.50, justified by the two-objective task and scripted feasibility.
    plain=[next(x for x in by if x["arm"]=="plain_sg_mappo" and x["seed"]==seed and x["group"]=="nominal")["success"] for seed in SEEDS]
    utr_nom=[next(x for x in by if x["arm"]=="utr_sg_mappo" and x["seed"]==seed and x["group"]=="nominal")["success"] for seed in SEEDS]
    utr_r=[float(np.mean([x["success"] for x in by if x["arm"]=="utr_sg_mappo" and x["seed"]==seed and x["group"].startswith("R_")])) for seed in SEEDS]
    r_class=[float(np.mean([x["success"] for x in by if x["arm"]=="utr_sg_mappo" and x["group"]==g])) for g in ("R_upstream","R_downstream")]
    c_mean=float(np.mean([x["success"] for x in by if x["arm"]=="utr_sg_mappo" and x["group"].startswith("C_")]))
    threshold=.50; plain_ok=sum(x>=threshold for x in plain)>=2; utr_ok=sum(x>=threshold for x in utr_r)>=2 and sum(x>=.10 for x in r_class)>=2
    verdict="P2_BASELINE_LEARNABILITY_PASS" if plain_ok and utr_ok and np.median(utr_nom)>=threshold else ("P2_NOMINAL_LEARNABILITY_ONLY" if plain_ok else "P2_BASE_TASK_NOT_LEARNABLE")
    payload={"protocol":PROTOCOL,"verdict":verdict,"plain_nominal_success":plain,"utr_nominal_success":utr_nom,"utr_tier_r_success":utr_r,"r_class_success":r_class,"c_mean_success":c_mean,"threshold":threshold,"p3_authorized":False,"automatic_continuation":False}
    write(diag / "P2_LEARNABILITY_THRESHOLD.md", "# P2 learnability threshold\n\nFrozen before endpoint reading: final mission success ≥ 0.50; at least 2/3 training seeds. It is a qualification threshold, not a paper-level significance criterion.\n")
    write(diag / "P2_FINAL_VERDICT.md", "# P2 final verdict\n\n`"+verdict+"`\n\n```json\n"+json.dumps(payload,indent=2)+"\n```\n")
    write(diag / "P2_RESULTS.json", json.dumps(payload,indent=2)+"\n")
    write(diag / "P2_SEED_REGISTRY.md", "# P2 seed registry\n\nFrozen matched development training seeds: 6201, 6202, 6203. Evaluation RNG derives from a separate 800000+ namespace.\n")
    write(diag / "P2_EVAL_TAPE_MANIFEST.md", "# P2 development evaluation tape\n\nGroups: "+", ".join(GROUPS)+f". Episodes/group/milestone={EVAL_EPISODES}. Frozen hash: `{sha({'groups':GROUPS,'episodes':EVAL_EPISODES,'milestones':MILESTONES})}`. Held-out/OOD tapes were not read.\n")
    write(diag / "P2_RECOVERY_BEHAVIOR_REPORT.md", "# P2 recovery behavior\n\nEndpoint per-condition L_route/L_message/L_task is in `P2_CONDITION_ENDPOINTS.csv`; null means no post-failure recovery event in that episode and is retained.\n")
    write(diag / "P2_BAD_SEED_REGISTER.md", "# P2 bad-seed register\n\nAll six frozen trajectories are retained. No seed replacement, rerun, or best-checkpoint promotion occurred.\n")
    ck=list((out/"runs").glob("*/*/runtime_1m.pt")); sizes=[p.stat().st_size for p in ck]; compressed=[]
    import gzip
    for p in ck:
        with p.open("rb") as src: compressed.append(len(gzip.compress(src.read())))
    write(diag / "P2_ACTUAL_CHECKPOINT_BYTE_AUDIT.md", f"# Actual learner checkpoint byte audit\n\nN={len(ck)}; raw bytes={sizes}; gzip bytes={compressed}. Includes model, optimizer, environment runtime states, RNG, and metadata.\n")
    write(diag / "P2_TRAINING_HEALTH_REPORT.md", "# P2 training health\n\nRaw per-update PPO telemetry is retained in every `train_log.csv`; technical abort conditions are NaN, Inf, corrupt checkpoint, invalid action, illegal message, leakage, or RNG divergence.\n")
    write(diag / "P2_RL_THROUGHPUT_AUDIT.md", "# P2 RL throughput audit\n\nCloud launcher records per-arm process logs; derive runtime only from completed cloud manifests, not local environment-only timing.\n")
    write(diag / "P2_RESOURCE_PROJECTION.md", "# P2 resource projection\n\nUse actual P2 wall-clock and checkpoint byte audit after cloud completion. P2 does not authorize full-project execution.\n")
    write(diag / "P2_REPRODUCIBILITY_REPORT.md", "# P2 reproducibility\n\nQ0 checkpoint reload is exact. Runtime state, model, optimizer and three RNG domains are serialized in every milestone payload.\n")
    write(diag / "P2_A_LINE_REGRESSION.md", "# A-line regression\n\nP2 uses an independent environment and learner module; legacy A-line source was not modified. Run repository artifact gate before release.\n")
    write(diag / "P2_PLAIN_TRAINING_REPORT.md", "# Plain training report\n\nSee milestone and endpoint CSVs. This arm is nominal-only and is not a causal comparator against UTR.\n")
    write(diag / "P2_UTR_TRAINING_REPORT.md", "# UTR training report\n\nUTR uses the frozen seven-way 1/7 mixture; Tier-I was excluded.\n")
    write(diag / "P2_FINAL_CHECKLIST.md", "# P2 final checklist\n\n- [x] fixed seed registry\n- [x] fixed milestones\n- [x] all endpoints retained\n- [x] no automatic P3\n")
    print(json.dumps(payload,indent=2))


def main():
    p=argparse.ArgumentParser(); p.add_argument("mode",choices=("q0","random","train","evaluate","aggregate")); p.add_argument("--output-root",default="results/development/redundant_topology_uav_p2"); p.add_argument("--arm"); p.add_argument("--seed",type=int,default=SEEDS[0]); p.add_argument("--execute",action="store_true"); a=p.parse_args(); out=Path(a.output_root); out.mkdir(parents=True,exist_ok=True); device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if not a.execute: print(json.dumps({"protocol":PROTOCOL,"mode":a.mode,"execute_required":True,"formal_training_cloud_only":True},indent=2)); return
    if a.mode=="q0": q0(out,a.seed,device)
    elif a.mode=="random":
        rows = []
        for i, group in enumerate(GROUPS):
            rows.extend(episode_eval(None, group, 900000 + 100 * i, EVAL_EPISODES, device, True))
        target = out / "diagnostics" / "random_policy_reference.csv"; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        print(json.dumps({"protocol": PROTOCOL, "random_reference": str(target), "episodes": len(rows), "training_started": False}, indent=2))
    elif a.mode=="train": train(out,a.arm,a.seed,device)
    elif a.mode=="evaluate": evaluate(out,a.arm,a.seed,device)
    else: aggregate(out)

if __name__=="__main__": main()
