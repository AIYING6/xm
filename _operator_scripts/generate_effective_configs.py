"""Generate 4 effective configs (full_reference + 3 ablations) and audit them.

Outputs to _operator_notes/effective_config_audit_v1.5.1/:
  full_reference.effective.yaml / w_o_gate_prior.effective.yaml /
  w_o_task_support.effective.yaml / w_o_role_pair_gate.effective.yaml
  effective_config_diff_report.md
  effective_config_sha256.csv
  parameter_count_report.csv
  state_dict_key_comparison.csv
  effective_config_audit.txt

Single-variable whitelist:
  w/o Gate Prior     : role_gate_prior_strength only
  w/o Task-Support   : graph_relation_ablation (-> disable_task_support)
  w/o Role-Pair Gate : graph_message_ablation + role_pair_gate_fixed_value
                       (one atomic intervention -> use_role_pair_gate=False)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import MultiRelationGraphEncoder  # noqa: E402

OUT = ROOT / "_operator_notes" / "effective_config_audit_v1.5.1"
SIGMOID_04 = 0.598687660112452  # full precision

# ---- common (BC + PPO + env + rewards) ----
COMMON = {
    # BC
    "bc_episodes": 120, "bc_epochs": 20, "bc_batch_size": 256,
    "bc_data_source": "full_v1.4_ea_rg_mappo_s_gate_prior_same_protocol",
    # training budget
    "updates": 977,
    "checkpoint_save_nodes": [100, 200, 300, 400, 500, 600, 700, 800, 900, 977],
    "audit_nodes": [100, 400, 600, 800, 977],
    # seeds
    "train_seeds": [0, 1, 2],
    "validation_base_seed": "641939 (frozen v1.5 split; NOT used in BC/PPO RNG)",
    # network
    "hidden_dim": 64, "role_dim": 8, "intent_dim": 8,
    "graph_encoder": "multi_relation", "num_relations": 3,
    "graph_input_ablation": "none",
    # PPO
    "actor_lr": 5e-5, "critic_lr": 1e-4, "clip_coef": 0.1,
    "ppo_epochs": 2, "target_kl": 0.01, "entropy_coef": 0.003,
    "max_grad_norm": 0.5, "critic_warmup_updates": 20,
    "eval_interval": 100, "eval_episodes": 5, "save_interval": 100,
    # env / scenario
    "env_name": "3d_intercept", "target_policy": "straight",
    "strict_target_sensing": True, "agent_target_info_bottleneck": True,
    "target_prior_position": [10000.0, 0.0, 5000.0],
    "max_target_message_age_steps": 80, "min_target_confidence": 0.2,
    "communication_dropout_prob": 0.30, "message_delay_steps": 2,
    "radar_dropout_prob": 0.0, "failed_blue_agent": 1,
    "node_failure_start_random_min": 25, "node_failure_start_random_max": 70,
    "node_failure_duration_steps": 80, "attack_hold_steps": 4,
    "min_success_step": 80,
    # rewards
    "post_loss_chain_reclosure_reward_weight": 0.5,
    "post_loss_chain_reclosure_min_step": 80,
    "safety_proximity_distance": 2500, "safety_proximity_penalty_weight": 0.5,
    # optimizer / rng
    "optimizer": "adam", "seed_rng": "per-task fixed train seed; validation seed excluded",
}

FULL = {
    **COMMON,
    "role_gate_prior_strength": 0.4,
    "graph_relation_ablation": "none",
    "graph_message_ablation": "none",
    "role_pair_gate_fixed_value": 0.5,  # not used in forward when gate enabled
    "_derived": {"disable_task_support": False, "use_role_pair_gate": True},
}

W_O_GATE_PRIOR = {**FULL, "role_gate_prior_strength": 0.0}

W_O_TASK_SUPPORT = {
    **FULL,
    "graph_relation_ablation": "no_task_support",
    "_derived": {**FULL["_derived"], "disable_task_support": True},
}

W_O_ROLE_PAIR_GATE = {
    **FULL,
    "graph_message_ablation": "no_role_pair_gate",
    "role_pair_gate_fixed_value": SIGMOID_04,
    "_derived": {**FULL["_derived"], "use_role_pair_gate": False},
}

CONFIGS = {
    "full_reference": FULL,
    "w_o_gate_prior": W_O_GATE_PRIOR,
    "w_o_task_support": W_O_TASK_SUPPORT,
    "w_o_role_pair_gate": W_O_ROLE_PAIR_GATE,
}

WHITELIST = {
    "w_o_gate_prior": {"role_gate_prior_strength"},
    "w_o_task_support": {"graph_relation_ablation"},
    "w_o_role_pair_gate": {"graph_message_ablation", "role_pair_gate_fixed_value"},
}


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    sha_rows = []

    for name, cfg in CONFIGS.items():
        text = json.dumps(cfg, indent=2, sort_keys=True)
        (OUT / f"{name}.effective.yaml").write_text(text + "\n", encoding="utf-8")
        sha_rows.append({"config": name, "sha256": sha256(text)})
        lines.append(f"{name}: sha256={sha256(text)}")

    # diff report (against full_reference)
    full = FULL
    diff_lines = ["# Effective Config Diff Report (vs full_reference)", ""]
    audit_lines = ["# Effective Config Audit", ""]
    all_ok = True
    for name in ("w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate"):
        cfg = CONFIGS[name]
        differing = sorted(k for k in full if full[k] != cfg[k])
        # _derived is a runtime-derived field of the same atomic intervention,
        # not an independent variable.
        derived_diff = [k for k in differing if k == "_derived"]
        config_diff = [k for k in differing if k != "_derived"]
        allowed = WHITELIST[name]
        diff_lines.append(f"## {name}")
        diff_lines.append(f"- differing fields: {differing}")
        diff_lines.append(f"- derived fields (same intervention, not a variable): {derived_diff}")
        unexpected = [k for k in config_diff if k not in allowed]
        ok = len(unexpected) == 0
        all_ok &= ok
        diff_lines.append(f"- unexpected (outside whitelist): {unexpected}")
        diff_lines.append(f"- single-variable OK: {ok}")
        audit_lines.append(f"{name}: single-variable diff {'PASS' if ok else 'FAIL'}")
        diff_lines.append("")

    # parameter count + state-dict keys (construct the encoder for each config)
    param_lines = ["config,total_params,trainable_params"]
    state_rows = []
    encoders = {}
    for name, cfg in CONFIGS.items():
        enc = MultiRelationGraphEncoder(
            hidden_dim=cfg["hidden_dim"], edge_dim=8, num_roles=8, num_relations=3,
            use_role_pair_gate=cfg["_derived"]["use_role_pair_gate"],
            role_gate_prior_strength=cfg["role_gate_prior_strength"],
            global_residual_weight=1.0,
            disable_task_support=cfg["_derived"]["disable_task_support"],
            role_pair_gate_fixed_value=cfg["role_pair_gate_fixed_value"],
        )
        encoders[name] = enc
        total = sum(p.numel() for p in enc.parameters())
        trainable = sum(p.numel() for p in enc.parameters() if p.requires_grad)
        param_lines.append(f"{name},{total},{trainable}")
        state_rows.append((name, sorted(enc.state_dict().keys())))

    full_keys = state_rows[0][1]
    for name, keys in state_rows:
        same = keys == full_keys
        audit_lines.append(f"{name}: state_dict keys identical to full_reference: {same}")
        all_ok &= same

    (OUT / "effective_config_diff_report.md").write_text("\n".join(diff_lines), encoding="utf-8")
    (OUT / "effective_config_sha256.csv").write_text("config,sha256\n" + "\n".join(f"{r['config']},{r['sha256']}" for r in sha_rows), encoding="utf-8")
    (OUT / "parameter_count_report.csv").write_text("\n".join(param_lines), encoding="utf-8")
    # state_dict key comparison CSV
    with (OUT / "state_dict_key_comparison.csv").open("w", encoding="utf-8", newline="") as f:
        import csv
        w = csv.writer(f)
        w.writerow(["config", "key_count", "keys_identical_to_full"])
        for name, keys in state_rows:
            w.writerow([name, len(keys), keys == full_keys])

    audit_lines.append(f"OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (OUT / "effective_config_audit.txt").write_text("\n".join(lines + [""] + audit_lines), encoding="utf-8")
    print("\n".join(lines))
    print("DIFF/param/key audit:", "PASS" if all_ok else "FAIL")


if __name__ == "__main__":
    main()
