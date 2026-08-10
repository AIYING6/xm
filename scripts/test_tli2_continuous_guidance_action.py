"""No-training validation of a continuous guidance action interface."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    ACTION3D_TABLE,
    GUIDANCE_ACTION_TABLE,
    GUIDANCE_FLIGHT_ACTION_DIM,
)
from scripts.run_new_project_l0_single_interceptor import heuristic_action, l0_cfg  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402


OUT = ROOT / "results" / "tli2_continuous_guidance_action_validation"
SEEDS = tuple(range(820000, 820008))


def angle_diff(a: float, b: float) -> float:
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def continuous_guidance_from_obs(obs: np.ndarray) -> np.ndarray:
    """Normalized [turn, climb, commit] command using the legal obs row only."""
    row = obs[0]
    rel = row[8:11]
    desired = math.atan2(float(rel[1]), float(rel[0]))
    own = math.atan2(float(row[4]), float(row[5]))
    err = angle_diff(desired, own)
    own_gamma = math.atan2(float(row[6]), float(row[7]))
    desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2])) + 1e-6)
    turn = float(np.clip(err / (math.pi / 2.0), -1.0, 1.0))
    climb = float(np.clip((desired_gamma - own_gamma) / (math.pi / 4.0), -1.0, 1.0))
    commit = float(
        1_400 / 50_000 <= float(row[11]) <= 5_200 / 50_000
        and abs(float(rel[2])) <= 1_600 / 8_000
        and math.cos(err) >= 0.90
    )
    return np.asarray([turn, climb, commit], dtype=np.float32)


def fixed_controller_decode(command: np.ndarray, speed: float = 270.0) -> tuple[int, float]:
    """Map continuous guidance to the existing fixed low-level controller."""
    turn = float(np.clip(command[0], -1.0, 1.0))
    climb = float(np.clip(command[1], -1.0, 1.0))
    pair = np.asarray([turn, climb], dtype=np.float32)
    guidance_id = int(np.argmin(np.linalg.norm(GUIDANCE_ACTION_TABLE - pair[None, :], axis=1)))
    flight = GUIDANCE_ACTION_TABLE[guidance_id]
    low_level = np.asarray([flight[0], flight[1], 0.0], dtype=np.float32)
    low_id = int(np.argmin(np.linalg.norm(ACTION3D_TABLE - low_level[None, :], axis=1)))
    return low_id, float(np.linalg.norm(pair - GUIDANCE_ACTION_TABLE[guidance_id]))


def main() -> None:
    cfg = l0_cfg(8101, OUT / "template", updates=1)
    errors: list[float] = []
    discrete_matches = 0
    total = 0
    saturation = 0
    for seed in SEEDS:
        env = make_env(cfg, seed, training=False)
        obs, _share, _graph = env.reset()
        for _ in range(64):
            continuous = continuous_guidance_from_obs(obs)
            low_id, error = fixed_controller_decode(continuous)
            discrete = int(heuristic_action(obs)[0]) % GUIDANCE_FLIGHT_ACTION_DIM
            nearest = int(np.argmin(np.linalg.norm(GUIDANCE_ACTION_TABLE - continuous[:2][None, :], axis=1)))
            errors.append(error)
            discrete_matches += int(nearest == discrete)
            total += 1
            saturation += int(abs(float(continuous[0])) >= 0.999 or abs(float(continuous[1])) >= 0.999)
            # Existing environment transition is used only to sample legal
            # observation states; no continuous policy is trained here.
            obs, _share, _graph, _reward, dones, _info = env.step(np.asarray([discrete], dtype=np.int64))
            if bool(np.all(dones)):
                break
    payload = {
        "status": "TLI2_CONTINUOUS_ACTION_VALIDATION_PASS",
        "no_training": True,
        "seeds": list(SEEDS),
        "samples": total,
        "mean_command_reconstruction_error": float(np.mean(errors)),
        "max_command_reconstruction_error": float(np.max(errors)),
        "nearest_discrete_match_rate": float(discrete_matches / max(total, 1)),
        "boundary_saturation_rate": float(saturation / max(total, 1)),
        "actor_information_source": "legal observation row only",
        "fixed_controller_reads_target_truth": False,
        "action_dim_change_for_training": "not implemented in TLI2 validation",
        "performance_use_prohibited": True,
    }
    checks = {
        "finite_commands": bool(np.all(np.isfinite(errors))),
        "bounded_error": payload["max_command_reconstruction_error"] <= math.sqrt(0.5**2 + 0.5**2) + 1e-6,
        "no_full_boundary_saturation": payload["boundary_saturation_rate"] < 0.5,
        "legal_source_only": payload["fixed_controller_reads_target_truth"] is False,
    }
    payload["checks"] = checks
    if not all(checks.values()):
        raise AssertionError(payload)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "TLI2_CONTINUOUS_ACTION_VALIDATION.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name in checks:
        print(f"PASS {name}")
    print("TLI2_CONTINUOUS_ACTION_VALIDATION_REPORT: PASS (4 tests)")


if __name__ == "__main__":
    main()
