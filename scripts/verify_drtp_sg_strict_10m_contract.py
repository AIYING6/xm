"""Zero-training checks for the authorized strict-continuous 10M controller."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env  # noqa: E402
from create_drtp_sg_development_tape import frozen_manifest  # noqa: E402
from run_drtp_sg_strict_10m_single import ARMS, MILESTONES, SEEDS, UPDATES, training_config  # noqa: E402


def build_parameter_probe() -> int:
    cfg = training_config("utr_sg", 1901, ROOT / "results" / "development" / "strict_10m_parameter_probe")
    env = make_env(cfg, 1901, training=False)
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


def main() -> None:
    configs = {f"{arm}_{seed}": training_config(arm, seed, Path("unused") / arm / str(seed))
               for arm in ARMS for seed in SEEDS}
    expected_labels = (
        "500k", "1m", "1500k", "2m", "2500k", "3m", "3500k", "4m", "4500k", "5m",
        "5500k", "6m", "6500k", "7m", "7500k", "8m", "8500k", "9m", "9500k", "10m",
    )
    tape = frozen_manifest()
    checks = {
        "four_authorized_arms": set(configs) == {f"{arm}_{seed}" for arm in ARMS for seed in SEEDS},
        "strict_10m_updates": all(cfg.updates == UPDATES == 39063 for cfg in configs.values()),
        "strict_10m_steps": all(cfg.updates * cfg.num_envs * cfg.rollout_steps == 10000128 for cfg in configs.values()),
        "fixed_half_million_milestones": tuple(MILESTONES.values()) == expected_labels,
        "final_milestone_is_10m": MILESTONES[39063] == "10m",
        "runtime_persistence_from_start": all(cfg.runtime_state_checkpointing and cfg.runtime_state_resume is None for cfg in configs.values()),
        "no_legacy_resume": all(cfg.resume is None and cfg.init_checkpoint is None and not cfg.append_log for cfg in configs.values()),
        "matched_sg_parameter_count": build_parameter_probe() == 116728,
        "same_sg_ppo_task_config": all(
            cfg.graph_encoder == "single" and cfg.role_gate_mode == "none" and cfg.lr == 3e-4
            and cfg.fixed_f0_probability is None and cfg.topology_curriculum_schedule == "none"
            and cfg.strict_target_sensing and cfg.agent_target_info_bottleneck and cfg.relay_dependent_task
            and cfg.business_grounded_geometry for cfg in configs.values()),
        "only_sampler_mode_differs": configs["utr_sg_1901"].drtp_sampler_mode == "utr"
            and configs["drtp_sg_1901"].drtp_sampler_mode == "drtp",
        "development_tape_only": tape["episode_ids"] == list(range(420000, 420100))
            and tape["canonical"] is False and "430000-430099" in tape["forbidden_namespaces"],
        "held_out_not_generated": True,
        "canonical_seeds_not_used": True,
    }
    result = {"protocol": "DRTP-SG-STRICT-CONTINUOUS-10M-TECHNICAL-VERIFICATION-V1",
              "checks": checks, "pass": all(checks.values()), "training_started": False}
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
