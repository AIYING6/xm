"""Trajectory-level legacy-v1.6 vs corrected-v1.8 no-graph invariance audit."""
from __future__ import annotations

import dataclasses
import subprocess
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


LEGACY_REV = "f0c7f57"
SEEDS = (431, 517, 809)


def _load_legacy_module() -> types.ModuleType:
    source = subprocess.check_output(
        ["git", "show", f"{LEGACY_REV}:envs/uav_intercept_3d_env.py"],
        cwd=ROOT,
        text=True,
    )
    module = types.ModuleType("legacy_uav_intercept_3d_env")
    module.__file__ = str(ROOT / "envs/uav_intercept_3d_env.py")
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def _config_kwargs(cls):
    names = {field.name for field in dataclasses.fields(cls)}
    requested = {
        "communication_dropout_prob": 0.30,
        "message_delay_steps": 2,
        "radar_dropout_prob": 0.10,
        "strict_target_sensing": True,
        "agent_target_info_bottleneck": True,
        "failed_blue_agent": 1,
        "node_failure_start_step": 40,
        "node_failure_duration_steps": 80,
    }
    return {key: value for key, value in requested.items() if key in names}


def _snapshot(env, obs, share_obs, rewards=None, dones=None, infos=None):
    if env.success:
        termination_reason = "success"
    elif env.collision:
        termination_reason = "collision"
    elif env.constraint_violation:
        termination_reason = "constraint_violation"
    elif env.done:
        termination_reason = "timeout"
    else:
        termination_reason = "running"
    state = {
        "blue_pos": env.blue_pos.copy(),
        "blue_speed": env.blue_speed.copy(),
        "blue_heading": env.blue_heading.copy(),
        "blue_gamma": env.blue_gamma.copy(),
        "blue_energy": env.blue_energy.copy(),
        "red_pos": env.red_pos.copy(),
        "red_speed": env.red_speed.copy(),
        "red_heading": env.red_heading.copy(),
        "red_gamma": env.red_gamma.copy(),
        "detected_by": env.detected_by.copy(),
        "attack_window": env.attack_window.copy(),
        "success": bool(env.success),
        "done": bool(env.done),
        "collision": bool(env.collision),
        "constraint_violation": bool(env.constraint_violation),
        "termination_reason": termination_reason,
        "step_count": int(env.step_count),
    }
    if hasattr(env, "_is_comm_failed"):
        state["relay_failure"] = np.asarray(
            [float(env._is_comm_failed(i)) for i in range(env.config.num_blue)],
            dtype=np.float32,
        )
    return {"obs": obs.copy(), "share_obs": share_obs.copy(), "state": state,
            "rewards": None if rewards is None else rewards.copy(),
            "dones": None if dones is None else dones.copy(),
            "infos": None if infos is None else dict(infos)}


def _compare(a, b, label, failures):
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        if not (isinstance(a, np.ndarray) and isinstance(b, np.ndarray)
                and a.shape == b.shape and np.array_equal(a, b)):
            failures.append(label)
    elif isinstance(a, dict) or isinstance(b, dict):
        if set(a) != set(b):
            failures.append(f"{label}.keys")
        else:
            for key in a:
                _compare(a[key], b[key], f"{label}.{key}", failures)
    elif isinstance(a, float) or isinstance(b, float):
        if not np.isclose(float(a), float(b), atol=1e-6, rtol=0.0, equal_nan=True):
            failures.append(label)
    elif a != b:
        failures.append(label)


def run_one(seed: int, horizon: int = 64):
    legacy = _load_legacy_module()
    new_args = _config_kwargs(UAVIntercept3DConfig); new_args["seed"] = seed
    old_args = _config_kwargs(legacy.UAVIntercept3DConfig); old_args["seed"] = seed
    new_cfg = UAVIntercept3DConfig(**new_args)
    old_cfg = legacy.UAVIntercept3DConfig(**old_args)
    new_env = UAVIntercept3DEnv(new_cfg)
    old_env = legacy.UAVIntercept3DEnv(old_cfg)
    new_obs, new_share, _ = new_env.reset()
    old_obs, old_share, _ = old_env.reset()
    failures: list[str] = []
    _compare(old_obs, new_obs, "reset.obs", failures)
    _compare(old_share, new_share, "reset.share_obs", failures)
    actions = np.random.default_rng(seed + 9000).integers(0, new_env.action_dim, size=(horizon, new_env.num_agents))
    for step, action in enumerate(actions, start=1):
        old_obs, old_share, _, old_rewards, old_dones, old_infos = old_env.step(action)
        new_obs, new_share, _, new_rewards, new_dones, new_infos = new_env.step(action)
        old_snap = _snapshot(old_env, old_obs, old_share, old_rewards, old_dones, old_infos)
        new_snap = _snapshot(new_env, new_obs, new_share, new_rewards, new_dones, new_infos)
        _compare(old_snap, new_snap, f"step[{step}]", failures)
        if old_env.done or new_env.done:
            break
    return failures, step


def main() -> int:
    all_failures = []
    transitions = 0
    for seed in SEEDS:
        failures, count = run_one(seed)
        transitions += count
        all_failures.extend([f"seed={seed}:{item}" for item in failures])
    failures = all_failures
    if failures:
        print("NO_GRAPH_BASELINE_INVARIANCE_AUDIT_V1_8: FAIL")
        for item in failures[:40]:
            print(f"  {item}")
        return 1
    print(f"NO_GRAPH_BASELINE_INVARIANCE_AUDIT_V1_8: PASS ({transitions} transitions, seeds={SEEDS}, formal stochastic config)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
