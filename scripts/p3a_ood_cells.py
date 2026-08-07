# p3a_ood_cells.py — P3-A OOD protocol v1.1: single code-level source of the 7 cells,
# frozen methods/checkpoints, and evaluation parameters. Do NOT edit values here; any
# change requires a new protocol version.
from __future__ import annotations

from pathlib import Path

# --- frozen evaluation parameters (p3a_ood_protocol_v1_1) ---
EVAL_BASE_SEED = 1208607
EPISODES_PER_CELL = 100
FAILED_BLUE_AGENT = 1  # relay
FAILURE_START = 25
FAILURE_DURATION = 80
HORIZON = 260
EXPOSURE_GATE = 0.99

# --- exact OOD cell definitions (protocol v1.1; no e.g. anywhere) ---
CELLS: dict[str, dict] = {
    "G1": {"blue_init_spacing_scale": 1.20, "blue_init_rotation_deg": 20.0},
    "G2": {"target_init_range_scale": 1.40, "target_init_bearing_offset_deg": 25.0},
    "M1": {"target_policy": "weaving"},
    "M2": {"target_policy": "break_turn"},
    "C1": {"comm_topology_mode": "symmetric_longest_prune"},
    "C2": {"comm_topology_mode": "directed_longest_prune"},
    "J1": {"blue_init_spacing_scale": 1.20, "blue_init_rotation_deg": 20.0,
           "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"},
}

# --- frozen methods (4 primary; w/o Task-Support optional, NOT in main gate) ---
PRIMARY_METHODS = ["full_ea_rg", "mappo", "happo", "param_matched_single"]
OPTIONAL_METHODS = ["w_o_task_support"]

# --- frozen checkpoints (zero-shot; must match recorded SHA256 in results manifest) ---
_CHECKPOINT_TMPL = {
    # (base dir, seed pattern, file)
    "full_ea_rg": (
        Path(r"D:/Code/Codex/ri_gmappo_uav/results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/ea_rg_mappo_s_gate_prior"),
        "ppo_seed{S}_1m", "actor_critic_update_0700.pt"),
    "happo": (
        Path(r"D:/Code/Codex/ri_gmappo_uav/results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/happo"),
        "ppo_seed{S}_1m", "happo_update_0300.pt"),
    "param_matched_single": (
        Path(r"D:/Code/Codex/ri_gmappo_uav/results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/param_matched_single"),
        "ppo_seed{S}_1m", "actor_critic_update_0500.pt"),
    "mappo": (
        Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_mappo_v1.5_ppo_977_20260806"),
        "ppo_seed{S}", "actor_critic_update_0600.pt"),
    "w_o_task_support": (
        Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5/results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804/w_o_task_support"),
        "ppo_seed{S}_1m", "actor_critic_update_0100.pt"),
}

TRAIN_SEEDS = ["0", "1", "2"]


def checkpoint_path(method: str, seed: str) -> Path:
    base, pat, fname = _CHECKPOINT_TMPL[method]
    return base / pat.replace("{S}", seed) / fname


def cell_overrides(cell: str) -> dict:
    return dict(CELLS[cell])


def common_eval_overrides() -> dict:
    return {
        "failed_blue_agent": FAILED_BLUE_AGENT,
        "node_failure_start_step": FAILURE_START,
        "node_failure_duration_steps": FAILURE_DURATION,
        "max_steps": HORIZON,
    }
