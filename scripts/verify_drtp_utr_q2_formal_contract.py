"""Zero-training preflight for the prospective paired five-seed confirmation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env  # noqa: E402
from create_drtp_utr_q2_formal_tape import CONDITIONS, EPISODES, SEEDS, TAPE_START, frozen_manifest  # noqa: E402
from run_drtp_utr_q2_formal_single import (  # noqa: E402
    ARMS, MILESTONES, NUM_ENVS, ROLLOUT_STEPS, UPDATES, training_config,
)


PROTOCOL = "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-PREFLIGHT-V1"
ALLOWED_CONFIG_DIFFERENCES = {"drtp_sampler_mode", "seed", "drtp_sampler_seed", "out_dir"}


def parameter_count(cfg) -> int:
    env = make_env(cfg, cfg.seed, training=False)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False,
    )
    return sum(parameter.numel() for parameter in agent.parameters() if parameter.requires_grad)


def normalized_config(cfg) -> dict:
    data = asdict(cfg)
    for key in ALLOWED_CONFIG_DIFFERENCES:
        data.pop(key, None)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    configs = {
        f"{arm}_{seed}": training_config(arm, seed, Path("unused") / arm / f"seed{seed}")
        for arm in ARMS for seed in SEEDS
    }
    reference = normalized_config(configs[f"utr_sg_{SEEDS[0]}"])
    tape = frozen_manifest()
    counts = {
        arm: parameter_count(configs[f"{arm}_{SEEDS[0]}"])
        for arm in ARMS
    }
    checks = {
        "ten_authorized_trajectories": len(configs) == 10,
        "prospective_seed_set": tuple(SEEDS) == (2301, 2302, 2303, 2304, 2305),
        "canonical_seeds_prohibited": not set(SEEDS).intersection({0, 1, 2, 3, 4}),
        "strict_common_10m_budget": all(
            cfg.updates == UPDATES == 39063
            and cfg.num_envs == NUM_ENVS == 4
            and cfg.rollout_steps == ROLLOUT_STEPS == 64
            and cfg.updates * cfg.num_envs * cfg.rollout_steps == 10000128
            for cfg in configs.values()
        ),
        "fixed_milestones_and_final": MILESTONES.get(39063) == "10m" and len(MILESTONES) == 20,
        "matched_116728_parameters": counts == {"utr_sg": 116728, "drtp_sg": 116728},
        "all_non_sampler_config_identical": all(normalized_config(cfg) == reference for cfg in configs.values()),
        "only_uniform_vs_adaptive_sampler": (
            all(configs[f"utr_sg_{seed}"].drtp_sampler_mode == "utr" for seed in SEEDS)
            and all(configs[f"drtp_sg_{seed}"].drtp_sampler_mode == "drtp" for seed in SEEDS)
        ),
        "same_frozen_sg_ppo_s2_contract": all(
            cfg.graph_encoder == "single" and cfg.role_gate_mode == "none" and cfg.lr == 3e-4
            and cfg.target_kl is None and cfg.topology_curriculum_schedule == "none"
            and cfg.fixed_f0_probability is None and cfg.strict_target_sensing
            and cfg.agent_target_info_bottleneck and cfg.relay_dependent_task
            and cfg.business_grounded_geometry and cfg.min_success_step == 260
            for cfg in configs.values()
        ),
        "runtime_persistence_from_update_zero": all(
            cfg.runtime_state_checkpointing and cfg.runtime_state_resume is None
            and cfg.resume is None and cfg.init_checkpoint is None and not cfg.append_log
            for cfg in configs.values()
        ),
        "formal_tape_490000_490099": tape["episode_ids"] == list(range(TAPE_START, TAPE_START + EPISODES)),
        "twelve_frozen_conditions": list(CONDITIONS) == [item["name"] for item in tape["conditions"]]
            and len(CONDITIONS) == 12,
        "tape_noncanonical_and_prospective": tape["canonical"] is False
            and tape["prospective_formal_confirmation"] is True,
        "no_training_started_by_preflight": True,
    }
    result = {
        "protocol": PROTOCOL,
        "checks": checks,
        "parameter_counts": counts,
        "tape_hash": tape["tape_hash"],
        "updates": UPDATES,
        "environment_steps_per_run": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "total_environment_steps": len(configs) * UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "pass": all(checks.values()),
        "training_started": False,
    }
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
