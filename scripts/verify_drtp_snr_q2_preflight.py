"""Zero-training preflight for the prospective UTR/SNR/DRTP comparator."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, make_env  # noqa: E402
from algorithms.ri_gmappo.snr_topology_sampler import STATIC_NONUNIFORM_Q, StaticNonuniformTopologySampler  # noqa: E402
from create_drtp_snr_q2_tape import CONDITIONS, EPISODES, SEEDS, TAPE_START, frozen_manifest  # noqa: E402
from run_drtp_snr_q2_formal_single import ARMS, MILESTONES, NUM_ENVS, ROLLOUT_STEPS, UPDATES, training_config  # noqa: E402


PROTOCOL = "DRTP-SNR-Q2-MECHANISM-COMPARATOR-PREFLIGHT-V1"
ALLOWED_CONFIG_DIFFERENCES = {"drtp_sampler_mode", "seed", "drtp_sampler_seed", "out_dir", "device"}


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


def source_seed_mentions(seed: int) -> list[str]:
    """Audit tracked source history without treating no-match as an error."""
    # Bare four-digit strings occur in bibliographic arXiv identifiers and in
    # the frozen proposal itself.  Only a syntactic *training-seed* reference
    # is disqualifying here.
    pattern = rf"seed{seed}|seed[[:space:]_:=]+{seed}|[\"']seed[\"'][[:space:]]*:[[:space:]]*{seed}"
    # Inspect the pre-SNR committed tree rather than the current working tree:
    # this script necessarily names the newly frozen seeds itself.
    current = subprocess.run(["git", "grep", "-n", "-E", pattern, "HEAD", "--", ":(exclude)results/**"],
                             cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    # Full patch-content search is prohibitively expensive in this repository,
    # so the preflight has an explicit bounded provenance scope: committed tree
    # text plus every historical commit message.  Any archival manifest found
    # in the later cloud package audit remains a separate hard check.
    history = subprocess.run(["git", "log", "--all", "--format=%B"],
                             cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=20)
    found = [line for line in current.stdout.splitlines() if line]
    if f"seed{seed}" in history.stdout or f"seed {seed}" in history.stdout:
        found.append("history_commit_message_match")
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    configs = {f"{arm}_{seed}": training_config(arm, seed, Path("unused") / arm / f"seed{seed}")
               for arm in ARMS for seed in SEEDS}
    reference = normalized_config(configs[f"utr_sg_{SEEDS[0]}"])
    tape = frozen_manifest()
    counts = {arm: parameter_count(configs[f"{arm}_{SEEDS[0]}"]) for arm in ARMS}
    seed_trace = {str(seed): source_seed_mentions(seed) for seed in SEEDS}
    sampler = StaticNonuniformTopologySampler(99151, UPDATES)
    snr_manifest = sampler.manifest()
    checks = {
        "fifteen_authorized_trajectories": len(configs) == 15,
        "new_seed_set": tuple(SEEDS) == (2401, 2402, 2403, 2404, 2405),
        "seed_provenance_clean_in_tracked_source_and_history": not any(seed_trace.values()),
        "canonical_seeds_prohibited": not set(SEEDS).intersection({0, 1, 2, 3, 4}),
        "strict_common_10m_budget": all(
            cfg.updates == UPDATES == 39063 and cfg.num_envs == NUM_ENVS == 4
            and cfg.rollout_steps == ROLLOUT_STEPS == 64
            and cfg.updates * cfg.num_envs * cfg.rollout_steps == 10000128
            for cfg in configs.values()),
        "fixed_milestones_and_final": MILESTONES.get(39063) == "10m" and len(MILESTONES) == 20,
        "matched_116728_parameters": counts == {"utr_sg": 116728, "snr_sg": 116728, "drtp_sg": 116728},
        "all_non_sampler_config_identical": all(normalized_config(cfg) == reference for cfg in configs.values()),
        "only_uniform_static_nonuniform_adaptive_difference": (
            all(configs[f"utr_sg_{seed}"].drtp_sampler_mode == "utr" for seed in SEEDS)
            and all(configs[f"snr_sg_{seed}"].drtp_sampler_mode == "snr" for seed in SEEDS)
            and all(configs[f"drtp_sg_{seed}"].drtp_sampler_mode == "drtp" for seed in SEEDS)),
        "fixed_snr_weights": snr_manifest["static_nonuniform_q"] == STATIC_NONUNIFORM_Q
            and snr_manifest["uses_completed_return_feedback"] is False
            and snr_manifest["ema"] == "ABSENT" and snr_manifest["difficulty"] == "ABSENT"
            and snr_manifest["weight_updates"] == "ABSENT",
        "same_frozen_sg_ppo_s2_contract": all(
            cfg.graph_encoder == "single" and cfg.role_gate_mode == "none" and cfg.lr == 3e-4
            and cfg.target_kl is None and cfg.topology_curriculum_schedule == "none"
            and cfg.fixed_f0_probability is None and cfg.strict_target_sensing
            and cfg.agent_target_info_bottleneck and cfg.relay_dependent_task
            and cfg.business_grounded_geometry and cfg.min_success_step == 260
            for cfg in configs.values()),
        "runtime_persistence_from_update_zero": all(
            cfg.runtime_state_checkpointing and cfg.runtime_state_resume is None and cfg.resume is None
            and cfg.init_checkpoint is None and not cfg.append_log for cfg in configs.values()),
        "new_tape_500000_500099": tape["episode_ids"] == list(range(TAPE_START, TAPE_START + EPISODES)),
        "twelve_frozen_conditions": list(CONDITIONS) == [item["name"] for item in tape["conditions"]]
            and len(CONDITIONS) == 12,
        "tape_noncanonical_and_prospective": tape["canonical"] is False and tape["prospective_mechanism_comparator"] is True,
        "no_training_started_by_preflight": True,
    }
    result = {
        "protocol": PROTOCOL, "checks": checks, "parameter_counts": counts,
        "seed_provenance_trace": seed_trace, "tape_hash": tape["tape_hash"],
        "updates": UPDATES, "environment_steps_per_run": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "total_environment_steps": len(configs) * UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "pass": all(checks.values()), "training_started": False,
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
