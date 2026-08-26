"""Run one frozen MAPPO-NoGraph external-reference 10M trajectory."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env, train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as base  # noqa: E402


PROTOCOL = "DRTP-MAPPO-NOGRAPH-EXTERNAL-REFERENCE-5SEED-TRAINING-V1"
ARM = "mappo_ng"
SEEDS = (2301, 2302, 2303, 2304, 2305)
UPDATES, MILESTONES = base.UPDATES, base.MILESTONES
NUM_ENVS, ROLLOUT_STEPS = base.NUM_ENVS, base.ROLLOUT_STEPS
HIDDEN_DIM = 64


def training_config(seed: int, out_dir: Path):
    if seed not in SEEDS:
        raise ValueError("unauthorized external-reference seed")
    probe = base.training_config("utr_sg", base.SEEDS[0], out_dir)
    # The training distribution remains UTR's fixed 50% nominal + uniform six-failure groups.
    return replace(
        probe, seed=seed, drtp_sampler_seed=seed, out_dir=str(out_dir),
        hidden_dim=HIDDEN_DIM, graph_encoder="no_graph", drtp_sampler_mode="utr",
    )


def parameter_count(cfg) -> int:
    env = make_env(cfg, cfg.seed, training=False)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim, intent_dim=cfg.intent_dim, graph_encoder=cfg.graph_encoder,
        role_gate_mode=cfg.role_gate_mode, use_intent_context=False,
    )
    return sum(item.numel() for item in agent.parameters() if item.requires_grad)


def run_one(seed: int, output_root: Path) -> dict:
    out_dir = output_root / "runs" / ARM / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(seed, out_dir)
    count = parameter_count(cfg)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": ARM, "seed": seed,
        "reference_method_name": "MAPPO-NoGraph", "external_reference": True,
        "not_a_causal_ablation": True, "graph_encoder": "no_graph",
        "hidden_dim": HIDDEN_DIM, "parameter_count": count,
        "updates": UPDATES, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES, "milestones_for_curve_only": True,
        "final_checkpoint_selection": "10m_final_only", "from_scratch": True,
        "strict_continuous_trajectory": True, "runtime_resume_used": False,
        "warm_restart_used": False, "early_stopping": False, "checkpoint_promotion": False,
        "seed_exclusion": False, "canonical_seeds_used": False, "held_out_seeds_used": False,
        "prospective_formal_external_reference": True,
        "sampler_mode": "utr_fixed_uniform", "nominal_anchor": 0.5,
        "topology_group_universe": ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "runtime_state_checkpointing": True, "runtime_state_format": "ri_gmappo_runtime_state_v1",
        "config_hash": base.config_hash(cfg), "config": cfg.__dict__,
    }
    path = out_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint, runtime = out_dir / "actor_critic_latest.pt", out_dir / "actor_critic_runtime_state_latest.pt"
    if not checkpoint.exists() or not runtime.exists():
        raise FileNotFoundError("missing final model/runtime-state checkpoint")
    models, runtimes = {}, {}
    for label in MILESTONES.values():
        model = out_dir / f"actor_critic_milestone_{label}.pt"
        state = out_dir / f"actor_critic_runtime_state_milestone_{label}.pt"
        if not model.exists() or not state.exists():
            raise FileNotFoundError(f"missing fixed milestone {label}")
        models[label], runtimes[label] = base.sha256(model), base.sha256(state)
    sampler_log = out_dir / "drtp_topology_sampler_log.csv"
    if not sampler_log.exists():
        raise FileNotFoundError(sampler_log)
    manifest.update({
        "status": "completed", "final_checkpoint": str(checkpoint),
        "final_checkpoint_sha256": base.sha256(checkpoint),
        "final_runtime_state_sha256": base.sha256(runtime),
        "milestone_checkpoint_sha256": models, "milestone_runtime_state_sha256": runtimes,
        "sampler_log": str(sampler_log),
    })
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "seed": seed, "checkpoint": manifest["final_checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", choices=SEEDS, type=int)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify-config", action="store_true")
    args = parser.parse_args()
    if args.verify_config:
        cfg = training_config(SEEDS[0], args.output_root / "config_probe")
        print(json.dumps({"config": cfg.__dict__, "parameter_count": parameter_count(cfg)}, indent=2, default=str))
        return
    if not args.execute or args.seed is None:
        raise SystemExit("NO-GO: --execute and --seed are required")
    run_one(args.seed, args.output_root)


if __name__ == "__main__":
    main()
