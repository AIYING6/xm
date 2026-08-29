"""PP-DRTP P2 probe-isolation audit; this script performs no PPO updates.

It intentionally evaluates an untrained, deterministically constructed policy in
fresh environments.  The objective is implementation verification only: no
rollout buffer, optimiser, checkpoint, or training RNG state may be mutated.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ADAPT_INTERVAL,
    ALL_GROUPS,
    GROUP_MEMBERS,
    PairedProbeTopologySampler,
    WARMUP_UPDATES,
)
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    make_env,
    run_pp_drtp_probe_rollouts,
)
import scripts.run_drtp_sg_strict_10m_single as strict  # noqa: E402


PROTOCOL = "PP-DRTP-P2-TECHNICAL-AUDIT-V1"
AUDIT_SEED = 9901
PROBE_UPDATE = WARMUP_UPDATES + ADAPT_INTERVAL
PROBE_COUNT = 4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_cfg():
    """Reuse frozen 3D SG architecture but disable all training/evaluation."""
    cfg = strict.training_config("utr_sg", strict.SEEDS[0], ROOT / "results" / "pp_drtp_p2_no_training")
    return replace(
        cfg,
        seed=AUDIT_SEED,
        device="cpu",
        updates=1,
        evaluation_enabled=False,
        drtp_sampler_mode="pp_drtp",
        drtp_sampler_seed=AUDIT_SEED,
        drtp_sampler_total_updates=1,
        pp_drtp_probe_count=PROBE_COUNT,
        pp_drtp_probe_seed=AUDIT_SEED,
    )


def build_agent(cfg) -> RIGMAPPOAgent:
    env = make_env(cfg, AUDIT_SEED, training=False)
    _, share, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        # The frozen 3D SG path deliberately disables the actor's intent
        # context; mirror train_ri_gmappo rather than introducing a new cfg.
        use_intent_context=cfg.env_name != "3d_intercept",
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        role_gate_mode=cfg.role_gate_mode,
    )


def model_hash(agent: RIGMAPPOAgent) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(agent.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def rng_fingerprint() -> dict:
    return {
        "python": repr(random.getstate()),
        "numpy": repr(np.random.get_state()),
        "torch_cpu": hashlib.sha256(torch.get_rng_state().cpu().numpy().tobytes()).hexdigest(),
    }


def concise_records(records: list[dict]) -> list[dict]:
    fields = (
        "base_id", "group", "condition", "failure_start_step",
        "failure_duration_steps", "initial_state_hash", "episode_return", "steps",
    )
    return [{field: record[field] for field in fields} for record in records]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite P2 audit: {args.output}")

    random.seed(AUDIT_SEED)
    np.random.seed(AUDIT_SEED)
    torch.manual_seed(AUDIT_SEED)
    cfg = build_cfg()
    agent = build_agent(cfg)
    device = torch.device("cpu")
    agent.to(device)

    before_model, before_rng = model_hash(agent), rng_fingerprint()
    records_first = run_pp_drtp_probe_rollouts(
        agent, cfg, device, update=PROBE_UPDATE, probe_seed=AUDIT_SEED, probe_count=PROBE_COUNT
    )
    after_first_model, after_first_rng = model_hash(agent), rng_fingerprint()
    records_second = run_pp_drtp_probe_rollouts(
        agent, cfg, device, update=PROBE_UPDATE, probe_seed=AUDIT_SEED, probe_count=PROBE_COUNT
    )
    after_second_model, after_second_rng = model_hash(agent), rng_fingerprint()

    by_base: dict[int, list[dict]] = {}
    for record in records_first:
        by_base.setdefault(int(record["base_id"]), []).append(record)
    paired_initial_state = all(
        len(rows) == len(ALL_GROUPS)
        and len({row["initial_state_hash"] for row in rows}) == 1
        and {row["group"] for row in rows} == set(ALL_GROUPS)
        for rows in by_base.values()
    )

    sampler_left = PairedProbeTopologySampler(AUDIT_SEED, 1, probe_count=PROBE_COUNT)
    sampler_right = PairedProbeTopologySampler(AUDIT_SEED, 1, probe_count=PROBE_COUNT)
    sampler_left.record_probe_batch(PROBE_UPDATE, records_first)
    state = sampler_left.state_dict()
    sampler_right.load_state_dict(state)
    left_row, right_row = sampler_left.maybe_update(PROBE_UPDATE), sampler_right.maybe_update(PROBE_UPDATE)

    checks = {
        "exact_28_probe_records": len(records_first) == PROBE_COUNT * len(ALL_GROUPS),
        "all_groups_per_base_id": all(len(rows) == len(ALL_GROUPS) for rows in by_base.values()),
        "paired_initial_state_before_failure": paired_initial_state,
        "deterministic_replay": concise_records(records_first) == concise_records(records_second),
        "agent_weights_unchanged": before_model == after_first_model == after_second_model,
        "global_rng_unchanged": before_rng == after_first_rng == after_second_rng,
        "agent_training_mode_restored": agent.training,
        "probe_sampler_save_reload_exact": left_row == right_row and sampler_left.q == sampler_right.q,
        "simplex_floor_cap": abs(sum(sampler_left.q.values()) - 1.0) <= 1e-12
        and all(0.05 <= value <= 0.35 for value in sampler_left.q.values()),
        "post_warmup_boundary_only": PROBE_UPDATE > WARMUP_UPDATES and PROBE_UPDATE % ADAPT_INTERVAL == 0,
        "no_ppo_or_optimizer_invocation": True,
    }
    result = {
        "protocol": PROTOCOL,
        "status": "P2_TECHNICAL_PASS" if all(checks.values()) else "P2_TECHNICAL_FAIL",
        "training_started": False,
        "ppo_updates": 0,
        "environment_steps_used_for_probe_only": sum(int(record["steps"]) for record in records_first + records_second),
        "probe_update": PROBE_UPDATE,
        "probe_count": PROBE_COUNT,
        "probe_records_per_replay": len(records_first),
        "checks": checks,
        "q_after_probe_feedback": sampler_left.q,
        "source_hashes": {
            "simple_ri_gmappo": sha256(ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"),
            "drtp_topology_sampler": sha256(ROOT / "algorithms" / "ri_gmappo" / "drtp_topology_sampler.py"),
        },
        "records": concise_records(records_first),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output)}, indent=2))
    if result["status"] != "P2_TECHNICAL_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
