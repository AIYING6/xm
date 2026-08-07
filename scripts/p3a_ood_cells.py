# p3a_ood_cells.py — P3-A OOD protocol v1.1: single code-level source of the 7 cells,
# frozen methods, evaluation parameters, and the checkpoint manifest (held-out
# truth source). Do NOT edit frozen values here; any change requires a new protocol
# version. Checkpoint provenance is read from the copied frozen held-out manifest
# (docs/statistics/p3a_ood_results_v1_1/held_out_split_manifest.csv), NOT from
# hard-coded update numbers.
from __future__ import annotations

import csv
from pathlib import Path

# --- frozen evaluation parameters (p3a_ood_protocol_v1_1) ---
EVAL_BASE_SEED = 1208607
EPISODES_PER_CELL = 100
FAILED_BLUE_AGENT = 1  # relay
FAILURE_START = 25
FAILURE_DURATION = 80
HORIZON = 260
EXPOSURE_GATE = 0.99

# --- v1.1 output root (NOT v1_0) ---
OUT_ROOT = Path("docs/statistics/p3a_ood_results_v1_1")

# --- copied frozen held-out manifest (single truth source for checkpoints) ---
HELD_OUT_MANIFEST_CSV = OUT_ROOT / "held_out_split_manifest.csv"

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

# method -> (run-dir template, filename prefix)
_METHOD_DIR = {
    "full_ea_rg": ("ppo_seed{S}_1m", "actor_critic_update_"),
    "happo": ("ppo_seed{S}_1m", "happo_update_"),
    "param_matched_single": ("ppo_seed{S}_1m", "actor_critic_update_"),
    "mappo": ("ppo_seed{S}", "actor_critic_update_"),
    "w_o_task_support": ("ppo_seed{S}_1m", "actor_critic_update_"),
}

TRAIN_SEEDS = ["0", "1", "2"]


def load_held_out_manifest() -> dict[tuple[str, str], dict]:
    """Read the copied frozen held-out manifest -> {(method, seed): row}.

    Columns (frozen asset): method, train_seed, selected_checkpoint_update,
    checkpoint_abs, file_sha256, manifest_sha256, match, base_seed,
    episodes_per_scenario, scenarios. P3-A reuses exactly these
    validation-selected checkpoints (zero-shot; no reselection).
    """
    if not HELD_OUT_MANIFEST_CSV.exists():
        raise FileNotFoundError(
            f"frozen held-out manifest missing: {HELD_OUT_MANIFEST_CSV} "
            f"(copy from the v1.5 worktree: docs/held_out_v1_5_assets/held_out_split_manifest.csv)"
        )
    manifest: dict[tuple[str, str], dict] = {}
    with HELD_OUT_MANIFEST_CSV.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            method = row["method"]
            if method not in _METHOD_DIR:
                continue
            manifest[(method, row["train_seed"])] = {
                "update": int(row["selected_checkpoint_update"]),
                "path": Path(row["checkpoint_abs"]),
                "sha256": row["file_sha256"].strip().upper(),
                "manifest_sha256": row["manifest_sha256"].strip().upper(),
                "match": row["match"],
            }
    return manifest


def checkpoint_path(method: str, seed: str) -> Path:
    """Path of the frozen validation-selected checkpoint for (method, seed)."""
    manifest = load_held_out_manifest()
    return manifest[(method, str(seed))]["path"]


def checkpoint_update(method: str, seed: str) -> int:
    manifest = load_held_out_manifest()
    return manifest[(method, str(seed))]["update"]


def cell_overrides(cell: str) -> dict:
    return dict(CELLS[cell])


def common_eval_overrides() -> dict:
    return {
        "failed_blue_agent": FAILED_BLUE_AGENT,
        "node_failure_start_step": FAILURE_START,
        "node_failure_duration_steps": FAILURE_DURATION,
        "max_steps": HORIZON,
    }
