#!/usr/bin/env python3
"""T4 frozen-policy task-support utilization audit; offline only."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, load_matching_state_dict
from envs.uav_intercept_3d_env import ACTION3D_TABLE

PROTOCOL = "T4-SUPPORT-UTILIZATION-GAP-AUDIT-V1"
SEEDS = (2201, 2202, 2203, 2204, 2205)
GOOD, WEAK, INTERMEDIATE = (2202, 2204), (2203, 2205), (2201,)
HORIZON, FRACTION, MAX_GAP, CAP = 16, .75, 4, 1800
RANDOM_SEED = 20260821
SUPPORT_FIELDS = (18, 28, 29, 30, 31)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def family(scenario: str) -> str:
    return "nominal" if scenario == "nominal" else "f0" if scenario.startswith("f0") else "timing" if scenario.startswith("timing") else "duration" if scenario.startswith("duration") else "compound"


def phase(scenario: str, step: int, onset: int) -> str:
    if scenario == "nominal":
        return "nominal"
    delta = step - onset
    return "pre" if delta < 0 else "early" if delta < 20 else "later" if delta < 80 else "post_late"


def zero_run(values: list[float]) -> int:
    longest = current = 0
    for value in values:
        if value <= 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def label(rows: list[dict], index: int) -> int:
    future = [float(rows[k]["legal"]) for k in range(index + 1, index + 1 + HORIZON)]
    return int(np.mean(future) >= FRACTION and zero_run(future) <= MAX_GAP)


def push(heap: list, score: float, item: tuple) -> None:
    entry = (-score, *item)
    if len(heap) < CAP:
        heapq.heappush(heap, entry)
    elif score < -heap[0][0]:
        heapq.heapreplace(heap, entry)


def build_sample(rows: list[dict], index: int, y: int) -> dict:
    row = rows[index]
    actor = row["actor"]
    obs = np.asarray(actor["obs"], dtype=np.float32)
    adj = np.asarray(actor["graph_adj"], dtype=np.float32)
    return {
        "episode_id": row["episode_id"], "scenario": row["scenario"],
        "family": family(row["scenario"]), "phase": phase(row["scenario"], row["post_step"], row["onset"]),
        "y": y, "chain": int(row["chain"] > .5), "legal": int(row["legal"] > .5),
        "progress": int(np.digitize(float(obs[2, 11]), (.2, .4, .6, .8))),
        "topology": f"s{int(adj[0,2]>.5)}r{int(adj[1,2]>.5)}",
        "obs": obs, "node": np.asarray(actor["graph_node_feat"], dtype=np.float32),
        "edge": np.asarray(actor["graph_edge_feat"], dtype=np.float32),
        "role": np.asarray(actor["graph_role"], dtype=np.int64), "adj": adj,
    }


def parse_seed(path: Path, seed: int) -> tuple[list[dict], dict]:
    rng = np.random.default_rng(RANDOM_SEED + seed)
    reservoirs = {0: [], 1: []}
    counts = [0, 0]
    current_key, episode = None, []

    def flush() -> None:
        nonlocal episode
        for index in range(len(episode) - HORIZON):
            y = label(episode, index)
            counts[y] += 1
            push(reservoirs[y], float(rng.random()), (episode[index]["episode_id"], index, episode, y))
        episode = []

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            raw = json.loads(line)
            key = (raw["scenario"], int(raw["episode_id"]))
            if current_key is not None and key != current_key:
                flush()
            current_key = key
            info = raw["diagnostic"]["info"]
            episode.append({
                "episode_id": key[1], "scenario": key[0], "post_step": int(raw["post_step"]),
                "onset": int(raw["scheduled_failure_onset"]), "actor": raw["actor"],
                "legal": float(info["attacker_legal_target_information_t"]),
                "chain": float(info["chain_support_t"]),
            })
    if episode:
        flush()
    samples = [
        build_sample(rows, index, y)
        for y in (0, 1)
        for _score, _eid, index, rows, y in reservoirs[y]
    ]
    rng.shuffle(samples)
    return samples, {
        "seed": seed, "candidate_label_counts": {"0": counts[0], "1": counts[1]},
        "selected_count": len(samples),
        "selected_label_counts": {"0": sum(s["y"] == 0 for s in samples), "1": sum(s["y"] == 1 for s in samples)},
    }


def make_agent(sample: dict, checkpoint: Path, seed: int) -> RIGMAPPOAgent:
    torch.manual_seed(seed)
    agent = RIGMAPPOAgent(
        obs_dim=sample["obs"].shape[-1], node_feat_dim=sample["node"].shape[-1],
        edge_feat_dim=sample["edge"].shape[-1], share_obs_dim=47, action_dim=len(ACTION3D_TABLE),
        num_agents=sample["obs"].shape[0], num_roles=max(4, int(sample["role"].max()) + 1),
        hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single",
        role_gate_mode="none", use_intent_context=False,
    )
    if sum(p.numel() for p in agent.parameters()) != 116728:
        raise RuntimeError("parameter-count mismatch")
    _, exact = load_matching_state_dict(agent, str(checkpoint), torch.device("cpu"))
    if not exact:
        raise RuntimeError(f"non-exact checkpoint load: {checkpoint}")
    return agent.eval()


def run_actor(actor, samples: list[dict], batch_size: int = 192) -> dict[str, np.ndarray]:
    captured = {}
    hooks = [
        actor.gat2.register_forward_hook(lambda _m, _i, out: captured.__setitem__("graph", out[0].detach())),
        actor.policy_head.register_forward_pre_hook(lambda _m, inputs: captured.__setitem__("pre", inputs[0].detach())),
    ]
    values = defaultdict(list)
    try:
        for start in range(0, len(samples), batch_size):
            part = samples[start:start + batch_size]
            tensors = (
                torch.as_tensor(np.stack([s["obs"] for s in part]), dtype=torch.float32),
                torch.as_tensor(np.stack([s["node"] for s in part]), dtype=torch.float32),
                torch.as_tensor(np.stack([s["edge"] for s in part]), dtype=torch.float32),
                torch.as_tensor(np.stack([s["role"] for s in part]), dtype=torch.long),
                torch.as_tensor(np.stack([s["adj"] for s in part]), dtype=torch.float32),
            )
            with torch.no_grad():
                logits, _attn, _intent = actor(*tensors, tensors[0].shape[1])
                prob = torch.softmax(logits, dim=-1)
                entropy = -(prob * torch.log(prob.clamp_min(1e-8))).sum(-1)
                expected = prob @ torch.as_tensor(ACTION3D_TABLE, dtype=torch.float32)
            values["prob"].append(prob.numpy())
            values["entropy"].append(entropy.numpy())
            values["expected"].append(expected.numpy())
            values["graph"].append(captured["graph"].numpy())
            values["pre"].append(captured["pre"].numpy())
    finally:
        for hook in hooks:
            hook.remove()
    return {key: np.concatenate(value) for key, value in values.items()}


def mask_samples(samples: list[dict]) -> list[dict]:
    result = []
    for sample in samples:
        copy = dict(sample)
        copy["obs"] = sample["obs"].copy()
        copy["obs"][2, 18] = 0.
        copy["obs"][2, 28] = 0.
        copy["obs"][2, 29] = 1.
        copy["obs"][2, 30] = 1.
        copy["obs"][2, 31] = 0.
        result.append(copy)
    return result


def permute_samples(samples: list[dict], seed: int) -> list[dict]:
    result, groups = [dict(s) for s in samples], defaultdict(list)
    for i, sample in enumerate(samples):
        groups[(sample["family"], sample["phase"], sample["progress"], sample["topology"])].append(i)
    rng = np.random.default_rng(RANDOM_SEED + 100 * seed)
    for indices in groups.values():
        if len(indices) > 1:
            for target, source in zip(indices, np.asarray(indices)[rng.permutation(len(indices))]):
                obs = samples[target]["obs"].copy()
                obs[2, list(SUPPORT_FIELDS)] = samples[int(source)]["obs"][2, list(SUPPORT_FIELDS)]
                result[target]["obs"] = obs
    return result


def tvd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return .5 * np.abs(a - b).sum(-1)


def average(values) -> float | None:
    vals = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.mean(vals)) if vals else None


def matched_response(samples: list[dict]) -> dict:
    bins = defaultdict(lambda: defaultdict(list))
    for i, s in enumerate(samples):
        key = (s["family"], s["phase"], s["progress"], s["topology"], s["y"], s["chain"], s["legal"])
        bins[key][s["seed"]].append(i)
    rows = []
    for role in range(3):
        gaps, count = defaultdict(list), 0
        for group in bins.values():
            good = [i for seed in GOOD for i in group.get(seed, [])]
            weak = [i for seed in WEAK for i in group.get(seed, [])]
            if not good or not weak:
                continue
            count += 1
            for name, field in (("entropy", "entropy"), ("action_norm", "action_norm"), ("confidence", "confidence")):
                gaps[name].append(float(np.mean([samples[i][field][role] for i in good]) - np.mean([samples[i][field][role] for i in weak])))
            for component, name in enumerate(("turn", "climb", "accel")):
                gaps[f"expected_{name}"].append(float(np.mean([samples[i]["expected"][role, component] for i in good]) - np.mean([samples[i]["expected"][role, component] for i in weak])))
        rows.append({"role": role, "matched_bins": count, **{f"good_minus_weak_{name}": average(values) for name, values in gaps.items()}})
    return {"definition": "family, phase, progress bin, actor-legal topology, future continuity, current chain support, current legal information", "role_rows": rows}


def probe(samples: list[dict], feature: np.ndarray) -> dict:
    rows = []
    for seed in SEEDS:
        indexes = [i for i, s in enumerate(samples) if s["seed"] == seed]
        train = [i for i in indexes if samples[i]["episode_id"] % 5]
        test = [i for i in indexes if not samples[i]["episode_id"] % 5]
        yt, yv = np.asarray([samples[i]["y"] for i in train]), np.asarray([samples[i]["y"] for i in test])
        if len(np.unique(yt)) < 2 or len(np.unique(yv)) < 2:
            rows.append({"seed": seed, "auc": None, "balanced_accuracy": None, "n_train": len(train), "n_test": len(test)})
            continue
        scaler = StandardScaler()
        x_train, x_test = scaler.fit_transform(feature[train]), scaler.transform(feature[test])
        clf = SGDClassifier(loss="log_loss", alpha=1e-4, max_iter=80, tol=1e-3, random_state=RANDOM_SEED + seed)
        clf.fit(x_train, yt)
        p = clf.predict_proba(x_test)[:, 1]
        rows.append({"seed": seed, "auc": float(roc_auc_score(yv, p)), "balanced_accuracy": float(balanced_accuracy_score(yv, p >= .5)), "n_train": len(train), "n_test": len(test)})
    good, weak = average([r["auc"] for r in rows if r["seed"] in GOOD]), average([r["auc"] for r in rows if r["seed"] in WEAK])
    return {"per_seed": rows, "good_mean_auc": good, "weak_mean_auc": weak, "good_minus_weak_auc": None if good is None or weak is None else good - weak}


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3 or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    def rank(x):
        o = np.argsort(x); r = np.empty(len(x)); r[o] = np.arange(len(x)); return r
    return float(np.corrcoef(rank(a), rank(b))[0, 1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--t2-analysis", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    samples, summaries = [], []
    for seed in SEEDS:
        path = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}" / "raw_step_telemetry.jsonl"
        picked, summary = parse_seed(path, seed)
        for sample in picked:
            sample["seed"] = seed
        samples.extend(picked); summaries.append(summary)
        print(f"T4 parsed seed{seed}: {len(picked)} actor-legal samples", flush=True)

    checkpoint_audit = {}
    for seed in SEEDS:
        indexes = [i for i, sample in enumerate(samples) if sample["seed"] == seed]
        subset = [samples[i] for i in indexes]
        checkpoint = args.t1_root / "runs" / "utr_sg" / f"seed{seed}" / "actor_critic_latest.pt"
        agent = make_agent(subset[0], checkpoint, seed)
        base, masked, permuted = run_actor(agent.actor, subset), run_actor(agent.actor, mask_samples(subset)), run_actor(agent.actor, permute_samples(subset, seed))
        mask_tvd, perm_tvd = tvd(base["prob"][:, 2], masked["prob"][:, 2]), tvd(base["prob"][:, 2], permuted["prob"][:, 2])
        for local, global_i in enumerate(indexes):
            sample = samples[global_i]
            sample["entropy"], sample["confidence"] = base["entropy"][local], base["prob"][local].max(-1)
            sample["expected"], sample["action_norm"] = base["expected"][local], np.linalg.norm(base["expected"][local], axis=-1)
            sample["mask_tvd"], sample["perm_tvd"] = float(mask_tvd[local]), float(perm_tvd[local])
            sample["graph_latent"], sample["pre_latent"] = base["graph"][local, 2], base["pre"][local, 2]
        checkpoint_audit[str(seed)] = {"sha256": sha256(checkpoint), "parameter_count": sum(p.numel() for p in agent.parameters())}
        print(f"T4 forwarded frozen seed{seed}", flush=True)

    matched = matched_response(samples)
    seed_rows = []
    for seed in SEEDS:
        failure = [s for s in samples if s["seed"] == seed and s["family"] != "nominal"]
        by_phase = {name: average([s["mask_tvd"] for s in failure if s["phase"] == name]) for name in ("pre", "early", "later", "post_late")}
        seed_rows.append({"seed": seed, "mask_tvd_failure": average([s["mask_tvd"] for s in failure]), "perm_tvd_failure": average([s["perm_tvd"] for s in failure]), "entropy_failure": average([s["entropy"][2] for s in failure]), "confidence_failure": average([s["confidence"][2] for s in failure]), "phase_mask_tvd": by_phase})

    def group(field):
        g, w = average([r[field] for r in seed_rows if r["seed"] in GOOD]), average([r[field] for r in seed_rows if r["seed"] in WEAK])
        return {"good": g, "weak": w, "good_minus_weak": None if g is None or w is None else g-w}
    groups = {name: group(name) for name in ("mask_tvd_failure", "perm_tvd_failure", "entropy_failure", "confidence_failure")}
    topology = {}
    for name in ("pre", "early", "later"):
        g = average([r["phase_mask_tvd"][name] for r in seed_rows if r["seed"] in GOOD])
        w = average([r["phase_mask_tvd"][name] for r in seed_rows if r["seed"] in WEAK])
        topology[name] = {"good": g, "weak": w, "good_minus_weak": None if g is None or w is None else g-w}

    latents = {
        "raw_actor_observation": probe(samples, np.stack([s["obs"][2] for s in samples])),
        "sg_latent": probe(samples, np.stack([s["graph_latent"] for s in samples])),
        "pre_policy_latent": probe(samples, np.stack([s["pre_latent"] for s in samples])),
    }
    performance = {int(r["seed"]): r for r in json.loads(args.t2_analysis.read_text(encoding="utf-8"))["seed_summaries"]}
    seed_use = {r["seed"]: r["mask_tvd_failure"] for r in seed_rows}
    associations = {metric: {"spearman_descriptive": spearman([seed_use[s] for s in SEEDS], [float(performance[s][metric]) for s in SEEDS])} for metric in ("J_F0", "J_OOD_mean", "J_OOD_worst", "timeout")}

    mask_gap, perm_gap = abs(groups["mask_tvd_failure"]["good_minus_weak"]), abs(groups["perm_tvd_failure"]["good_minus_weak"])
    pre, early = topology["pre"]["good_minus_weak"], topology["early"]["good_minus_weak"]
    amplified = pre is not None and early is not None and abs(early) > abs(pre) + .005
    association_count = sum(abs(item["spearman_descriptive"] or 0) >= .7 for item in associations.values())
    if mask_gap >= .02 and perm_gap >= .01 and amplified and association_count >= 2:
        decision, target = "U1 — SUPPORT_UTILIZATION_GAP_IDENTIFIED", "support-conditioned decision coupling"
    elif mask_gap >= .01 and perm_gap >= .005 and (amplified or association_count >= 1):
        decision, target = "U2 — MODERATE_SUPPORT_UTILIZATION_SIGNAL", "support-conditioned decision coupling"
    else:
        decision, target = "U3 — NO_SUPPORT_UTILIZATION_GAP", None

    result = {
        "protocol": PROTOCOL, "offline_only": True, "no_environment_constructed": True, "no_optimizer_update": True,
        "seeds": list(SEEDS), "frozen_groups": {"good": list(GOOD), "weak": list(WEAK), "intermediate": list(INTERMEDIATE)},
        "actor_input": ["actor.obs", "actor.graph_node_feat", "actor.graph_edge_feat", "actor.graph_adj", "actor.graph_relation_adj", "actor.graph_role"],
        "diagnostic_labels": ["future_attacker_continuity_y16", "chain_support_t", "attacker_legal_target_information_t"],
        "forbidden_for_policy": ["diagnostic", "share_obs", "failure_active", "schedule", "terminal", "global_route", "future_outcome"],
        "sample_summaries": summaries, "checkpoint_audit": checkpoint_audit, "matched_response": matched,
        "sensitivity_seed": seed_rows, "sensitivity_groups": groups, "topology_transition": topology,
        "latent_decodability": latents, "seed_level_associations": associations,
        "decision_rule": {"U1_mask_gap": .02, "U1_perm_gap": .01, "topology_margin": .005, "association_abs_spearman": .7},
        "decision": decision, "primary_algorithmic_target": target,
        "boundary": "Offline actor-input perturbations are not environment counterfactuals or policy-performance results.",
    }
    args.output_root.mkdir(parents=True)
    (args.output_root / "t4_utilization_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "decision": decision, "samples": len(samples)}, indent=2))


if __name__ == "__main__":
    main()
