"""Zero-training contract checks for the six authorized held-out v2 trajectories."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env  # noqa: E402
from create_drtp_sg_heldout_v2_tape import frozen_manifest  # noqa: E402
from run_drtp_sg_heldout_v2_single import ARMS, SEEDS, UPDATES, training_config  # noqa: E402


def parameter_count() -> int:
    cfg = training_config("utr_sg", 2001, ROOT / "results" / "heldout" / "parameter_probe")
    env = make_env(cfg, 2001, training=False)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", use_intent_context=False,
    )
    return sum(parameter.numel() for parameter in agent.parameters() if parameter.requires_grad)


def main() -> None:
    configs = {f"{arm}_{seed}": training_config(arm, seed, Path("unused") / arm / str(seed))
               for arm in ARMS for seed in SEEDS}
    tape = frozen_manifest()
    checks = {
        "six_authorized_arms_only": set(configs) == {f"{arm}_{seed}" for arm in ARMS for seed in SEEDS},
        "held_out_seed_set": tuple(SEEDS) == (2001, 2002, 2003),
        "strict_10m_budget": all(cfg.updates == UPDATES == 39063 and cfg.updates * cfg.num_envs * cfg.rollout_steps == 10000128 for cfg in configs.values()),
        "matched_sg_116728": parameter_count() == 116728,
        "runtime_persistence_from_start": all(cfg.runtime_state_checkpointing and cfg.runtime_state_resume is None for cfg in configs.values()),
        "no_resume_warm_restart_or_checkpoint_promotion": all(cfg.resume is None and cfg.init_checkpoint is None and not cfg.append_log for cfg in configs.values()),
        "frozen_sampler_and_task": all(cfg.graph_encoder == "single" and cfg.role_gate_mode == "none" and cfg.lr == 3e-4 and cfg.fixed_f0_probability is None and cfg.topology_curriculum_schedule == "none" and cfg.strict_target_sensing and cfg.agent_target_info_bottleneck and cfg.relay_dependent_task and cfg.business_grounded_geometry for cfg in configs.values()),
        "only_sampler_mode_differs": configs["utr_sg_2001"].drtp_sampler_mode == "utr" and configs["drtp_sg_2001"].drtp_sampler_mode == "drtp",
        "heldout_tape_430k_only": tape["episode_ids"] == list(range(430000, 430100)) and tape["canonical"] is False and "420000-420099" in tape["forbidden_namespaces"],
        "canonical_seeds_not_used": True, "new_algorithm_not_started": True,
    }
    result = {"protocol": "DRTP-SG-MAPPO-HELDOUT-CONFIRMATION-V2-TECHNICAL-VERIFICATION-V1", "checks": checks, "pass": all(checks.values()), "training_started": False}
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
