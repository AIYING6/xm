from __future__ import annotations

import argparse
import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import GROUP_MEMBERS  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


FREEZE = ROOT / "configs" / "capd_p05_signal_freeze.json"
ACTION = 13
EPS = 1e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_bytes((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def architecture_signature(state: dict[str, torch.Tensor]) -> list[tuple[str, tuple[int, ...], str]]:
    return [(key, tuple(value.shape), str(value.dtype)) for key, value in state.items()]


def build_agent(checkpoint: Path, probe: tuple[np.ndarray, np.ndarray, dict]) -> RIGMAPPOAgent:
    obs, share, graph = probe
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1],
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1],
        action_dim=27,
        num_agents=obs.shape[0],
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=115,
        role_dim=8,
        intent_dim=8,
        graph_encoder="single",
        role_gate_mode="none",
        use_intent_context=False,
    )
    agent.load_state_dict(state, strict=True)
    agent.eval()
    return agent


def make_env(seed: int, group: str, episode_index: int) -> UAVIntercept3DEnv:
    condition, onset, duration = GROUP_MEMBERS[group][episode_index % len(GROUP_MEMBERS[group])]
    del condition
    return UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed,
            target_policy="straight",
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            business_grounded_geometry=True,
            communication_range_scale=1.0,
            communication_dropout_prob=0.0,
            message_delay_steps=0,
            radar_dropout_prob=0.0,
            max_steps=260,
            min_success_step=260,
            failed_blue_agent=-1 if group == "N" else 1,
            node_failure_start_step=onset,
            node_failure_duration_steps=duration,
        )
    )


def state_tape(freeze: dict[str, Any]) -> tuple[list[dict[str, Any]], str, int]:
    spec = freeze["state_tape"]
    captures = set(int(step) for step in spec["capture_steps"])
    states: list[dict[str, Any]] = []
    environment_steps = 0
    hasher = hashlib.sha256()
    for group_index, group in enumerate(spec["groups"]):
        for episode_index in range(int(spec["episodes_per_group"])):
            episode_seed = int(spec["namespace_start"]) + group_index * 100 + episode_index
            env = make_env(episode_seed, group, episode_index)
            obs, share, graph = env.reset()
            for step in range(max(captures) + 1):
                if step in captures:
                    item = {
                        "group": group,
                        "episode_seed": episode_seed,
                        "step": step,
                        "obs": np.asarray(obs, dtype=np.float32).copy(),
                        "share": np.asarray(share, dtype=np.float32).copy(),
                        "graph": {key: np.asarray(value).copy() for key, value in graph.items()},
                    }
                    for value in (item["obs"], item["share"], *item["graph"].values()):
                        hasher.update(np.ascontiguousarray(value).tobytes())
                    hasher.update(f"{group}:{episode_seed}:{step}".encode())
                    states.append(item)
                actions = np.full(env.num_agents, ACTION, dtype=np.int64)
                obs, share, graph, _, dones, _ = env.step(actions)
                environment_steps += 1
                if np.all(dones):
                    break
    return states, hasher.hexdigest(), environment_steps


def policy_probabilities(agent: RIGMAPPOAgent, states: list[dict[str, Any]]) -> np.ndarray:
    obs = np.stack([item["obs"] for item in states])
    packed = stack_graphs([item["graph"] for item in states])
    with torch.no_grad():
        logits, _, _ = agent.actor(
            torch.as_tensor(obs, dtype=torch.float32),
            torch.as_tensor(packed["node_feat"], dtype=torch.float32),
            torch.as_tensor(packed["edge_feat"], dtype=torch.float32),
            torch.as_tensor(packed["role"], dtype=torch.long),
            torch.as_tensor(packed["adj"], dtype=torch.float32),
            agent.num_agents,
            relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32),
            intent_label=torch.as_tensor(packed["intent_label"], dtype=torch.long),
        )
        return torch.softmax(logits, dim=-1).cpu().numpy()


def kl(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.sum(left * (np.log(np.clip(left, EPS, 1.0)) - np.log(np.clip(right, EPS, 1.0))), axis=-1)


def js(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    midpoint = 0.5 * (left + right)
    return 0.5 * kl(left, midpoint) + 0.5 * kl(right, midpoint)


def explorer_sets(cohort: list[int]) -> dict[int, list[int]]:
    return {
        anchor: [cohort[index % len(cohort)] for index in (offset, offset + 1, offset + 2)]
        for offset, anchor in enumerate(cohort)
    }


def audit(asset_root: Path, output_dir: Path) -> dict[str, Any]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=False)
    runs_root = asset_root / "results" / "development" / "egtr_double_cohort_simultaneous" / "runs"
    states, tape_hash, environment_steps = state_tape(freeze)
    if len(states) != len(freeze["state_tape"]["groups"]) * freeze["state_tape"]["episodes_per_group"] * len(freeze["state_tape"]["capture_steps"]):
        raise RuntimeError("training-only state tape terminated before all frozen captures")

    checkpoints: dict[tuple[str, int], Path] = {}
    state_dicts: dict[tuple[str, int], dict[str, torch.Tensor]] = {}
    asset_rows: list[dict[str, Any]] = []
    reference_signature = None
    integrity = True
    for arm in freeze["arms"]:
        for cohort, seeds in freeze["cohorts"].items():
            for seed in seeds:
                run = runs_root / arm / f"seed{seed}"
                checkpoint = run / "actor_critic_latest.pt"
                manifest_path = run / "run_manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                checkpoint_hash = sha256(checkpoint)
                state = torch.load(checkpoint, map_location="cpu", weights_only=False)
                signature = architecture_signature(state)
                if reference_signature is None:
                    reference_signature = signature
                row_ok = all(
                    (
                        manifest.get("protocol") == freeze["asset_protocol"],
                        manifest.get("status") == "completed",
                        manifest.get("arm") == arm,
                        int(manifest.get("seed")) == seed,
                        int(manifest.get("updates")) == 39063,
                        int(manifest.get("environment_steps")) == 10000128,
                        manifest.get("checkpoint_sha256") == checkpoint_hash,
                        signature == reference_signature,
                    )
                )
                integrity &= row_ok
                checkpoints[(arm, seed)] = checkpoint
                state_dicts[(arm, seed)] = state
                asset_rows.append(
                    {
                        "cohort": cohort,
                        "arm": arm,
                        "seed": seed,
                        "checkpoint_sha256": checkpoint_hash,
                        "tensor_count": len(signature),
                        "parameter_count": sum(int(value.numel()) for value in state.values()),
                        "integrity_pass": row_ok,
                    }
                )
    unique_checkpoints = len({row["checkpoint_sha256"] for row in asset_rows}) == len(asset_rows)
    integrity &= unique_checkpoints
    write_csv(output_dir / "CAPD_P05_ASSET_INTEGRITY.csv", asset_rows)
    if not integrity:
        verdict = "CAPD_P05_ASSET_INTEGRITY_NO_GO"
        result = {
            "protocol": freeze["protocol"],
            "verdict": verdict,
            "asset_integrity": False,
            "unique_checkpoints": unique_checkpoints,
            "training_only_state_tape_generated": True,
            "state_tape_hash": tape_hash,
            "environment_steps": environment_steps,
            "ppo_updates": 0,
            "evaluation_started": False,
            "student_training_started": False,
            "automatic_continuation": False,
        }
        write_json(output_dir / "CAPD_P05_RESULT.json", result)
        return result

    probe = (states[0]["obs"], states[0]["share"], states[0]["graph"])
    probabilities: dict[tuple[str, int], np.ndarray] = {}
    for key, checkpoint in checkpoints.items():
        probabilities[key] = policy_probabilities(build_agent(checkpoint, probe), states)
    finite_simplex = all(
        np.isfinite(value).all() and np.allclose(value.sum(axis=-1), 1.0, atol=1e-6)
        for value in probabilities.values()
    )
    gate = freeze["signal_gate"]
    unit_rows: list[dict[str, Any]] = []
    meta_rows: list[dict[str, Any]] = []
    for cohort, seeds in freeze["cohorts"].items():
        mapping = explorer_sets(seeds)
        for anchor_seed, explorer_seeds in mapping.items():
            anchor = probabilities[("utr_sg", anchor_seed)]
            explorers = np.stack([probabilities[("egtr_sg", seed)] for seed in explorer_seeds])
            log_centroid = np.mean(np.log(np.clip(explorers, EPS, 1.0)), axis=0)
            centroid = np.exp(log_centroid - np.max(log_centroid, axis=-1, keepdims=True))
            centroid /= centroid.sum(axis=-1, keepdims=True)
            disagreement = np.mean(np.stack([js(policy, centroid) for policy in explorers]), axis=0)
            pairwise = np.mean(np.stack([js(explorers[i], explorers[j]) for i, j in combinations(range(3), 2)]), axis=0)
            anchor_tv = 0.5 * np.sum(np.abs(centroid - anchor), axis=-1)
            anchor_js = js(centroid, anchor)
            signal = (disagreement <= gate["low_explorer_disagreement_js_max"]) & (anchor_tv >= gate["material_centroid_anchor_tv_min"])
            for state_index, item in enumerate(states):
                roles = item["graph"]["role"][: anchor.shape[1]]
                for agent_index in range(anchor.shape[1]):
                    unit_rows.append(
                        {
                            "cohort": cohort,
                            "anchor_seed": anchor_seed,
                            "explorer_seeds": "|".join(str(seed) for seed in explorer_seeds),
                            "group": item["group"],
                            "episode_seed": item["episode_seed"],
                            "step": item["step"],
                            "agent_index": agent_index,
                            "role": int(roles[agent_index]),
                            "explorer_disagreement_js": float(disagreement[state_index, agent_index]),
                            "pairwise_explorer_js": float(pairwise[state_index, agent_index]),
                            "centroid_anchor_tv": float(anchor_tv[state_index, agent_index]),
                            "centroid_anchor_js": float(anchor_js[state_index, agent_index]),
                            "candidate_signal": bool(signal[state_index, agent_index]),
                        }
                    )
            meta_rows.append(
                {
                    "cohort": cohort,
                    "anchor_seed": anchor_seed,
                    "explorer_seeds": "|".join(str(seed) for seed in explorer_seeds),
                    "units": int(signal.size),
                    "signal_fraction": float(np.mean(signal)),
                    "median_explorer_disagreement_js": float(np.median(disagreement)),
                    "median_pairwise_explorer_js": float(np.median(pairwise)),
                    "median_centroid_anchor_tv": float(np.median(anchor_tv)),
                    "support": bool(np.mean(signal) >= gate["minimum_signal_fraction_per_meta_seed"]),
                }
            )
    write_csv(output_dir / "CAPD_P05_POLICY_SIGNAL_LEDGER.csv", unit_rows)
    write_csv(output_dir / "CAPD_P05_META_SEED_SUMMARY.csv", meta_rows)
    cohort_rows: list[dict[str, Any]] = []
    for cohort in freeze["cohorts"]:
        rows = [row for row in meta_rows if row["cohort"] == cohort]
        supporting = sum(bool(row["support"]) for row in rows)
        median_pairwise = float(np.median([row["median_pairwise_explorer_js"] for row in rows]))
        passes = supporting >= gate["minimum_supporting_meta_seeds_per_cohort"] and median_pairwise >= gate["minimum_median_pairwise_explorer_js"]
        cohort_rows.append(
            {
                "cohort": cohort,
                "supporting_meta_seeds": supporting,
                "total_meta_seeds": len(rows),
                "median_signal_fraction": float(np.median([row["signal_fraction"] for row in rows])),
                "median_pairwise_explorer_js": median_pairwise,
                "pass": passes,
            }
        )
    write_csv(output_dir / "CAPD_P05_COHORT_SUMMARY.csv", cohort_rows)
    signal_present = finite_simplex and all(bool(row["pass"]) for row in cohort_rows)
    verdict = "CAPD_P05_CANDIDATE_CONSENSUS_SIGNAL_PRESENT" if signal_present else "CAPD_P05_NO_CANDIDATE_CONSENSUS_SIGNAL"
    result = {
        "protocol": freeze["protocol"],
        "verdict": verdict,
        "asset_integrity": integrity,
        "unique_checkpoints": unique_checkpoints,
        "architecture_identical": True,
        "teacher_runs": len(asset_rows),
        "state_count": len(states),
        "agent_state_units_per_meta_seed": len(states) * probabilities[("utr_sg", freeze["cohorts"]["A"][0])].shape[1],
        "state_tape_hash": tape_hash,
        "state_tape_namespace_start": freeze["state_tape"]["namespace_start"],
        "finite_probability_simplexes": finite_simplex,
        "cohorts": cohort_rows,
        "interpretation": freeze["interpretation"],
        "evaluation_tape_read": False,
        "outcome_metrics_read": False,
        "checkpoint_selection_by_outcome": False,
        "environment_steps": environment_steps,
        "ppo_updates": 0,
        "student_training_started": False,
        "implementation_authorized": False,
        "automatic_continuation": False,
    }
    write_json(output_dir / "CAPD_P05_RESULT.json", result)
    report = [
        "# CAPD P0.5 training-only teacher-signal audit",
        "",
        f"**Verdict:** `{verdict}`.",
        "",
        f"All `{len(asset_rows)}` frozen UTR/EGTR checkpoints passed manifest hash and exact architecture checks. The diagnostic generated `{len(states)}` fixed, outcome-free training states (`{environment_steps}` environment steps) and performed no PPO update or student training.",
        "",
        "The signal gate asks only whether three predeclared EGTR policies sometimes agree with one another while their geometric centroid differs materially from the matched UTR anchor. It does not test whether that direction is correct, safe or high-return.",
        "",
        "## Cohort results",
        "",
        *[
            f"- Cohort {row['cohort']}: supporting meta-seeds `{row['supporting_meta_seeds']}/{row['total_meta_seeds']}`, median signal fraction `{row['median_signal_fraction']:.4f}`, median pairwise EGTR JS `{row['median_pairwise_explorer_js']:.6f}`, pass `{row['pass']}`."
            for row in cohort_rows
        ],
        "",
        "## Boundary",
        "",
        "A positive result authorizes at most a separate formula-freeze and same-state distillation mechanism audit. It does not authorize fresh-seed training, cloud execution or an algorithm-performance claim. A negative result closes CAPD without training a student.",
    ]
    (output_dir / "CAPD_P05_REPORT.md").write_bytes(("\n".join(report) + "\n").encode("utf-8"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    result = audit(args.asset_root, args.output_dir)
    print(json.dumps({"verdict": result["verdict"], "teacher_runs": result.get("teacher_runs", 0)}))


if __name__ == "__main__":
    main()
