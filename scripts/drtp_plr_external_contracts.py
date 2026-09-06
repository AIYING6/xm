"""Frozen contracts for the 3-UAV external PLR-style comparator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs/drtp_plr_external_formal_freeze_20260906.json"
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp", "plr_style_sg": "plr"}
SEEDS = (79011, 79012, 79013, 79014, 79015)
UPDATES, NUM_ENVS, ROLLOUT = 39063, 4, 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT
MILESTONES = {3907: "1m", 11719: "3m", 39063: "10m"}
CONDITIONS = (
    ("nominal", -1, 0, 0), ("F0", 1, 44, 80), ("TE", 1, 28, 80),
    ("TL", 1, 52, 80), ("DS", 1, 44, 40), ("DL", 1, 44, 100), ("CP", 1, 28, 120),
)


def freeze() -> dict:
    value = json.loads(FREEZE.read_text(encoding="utf-8"))
    if tuple(value["methods"]) != tuple(ARMS) or tuple(value["training"]["seeds"]) != SEEDS:
        raise RuntimeError("PLR external comparator freeze mismatch")
    return value


def tape_payload() -> dict:
    spec = freeze()["evaluation"]
    body = {
        "protocol": "DRTP-PLR-EXTERNAL-FORMAL-ENDPOINT-TAPE-V1", "training_access": "forbidden",
        "episode_ids": list(range(spec["tape_seed_namespace"][0], spec["tape_seed_namespace"][1] + 1)),
        "conditions": [{"name": name, "failed_blue_agent": agent, "start_step": onset, "duration_steps": duration} for name, agent, onset, duration in CONDITIONS],
        "same_base_ids_across_conditions": True, "endpoint": "10m_only",
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**body, "tape_hash": hashlib.sha256(encoded).hexdigest()}
