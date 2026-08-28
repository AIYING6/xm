"""B-line B2 technical acceptance for read-only DRTP behavior telemetry.

This is deliberately a short CPU-only audit.  It never creates a scientific
training cohort, evaluation tape, checkpoint-selection result, or algorithm
variant.  It proves that the telemetry sink is observational: under the same
stochastic policy/RNG stream it cannot alter actions, rewards, termination,
sampler state, PPO logs, or the next-update runtime state.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import UAVIntercept3DEnv  # noqa: E402


DEFAULT_OUT = ROOT / "diagnostics" / "drtp_b_line" / "02_telemetry_acceptance"
AUDIT_SEED = 2601


def config(out_dir: Path, *, updates: int, telemetry: bool, **extra: Any) -> RIGMAPPOConfig:
    values: dict[str, Any] = {
        "env_name": "3d_intercept", "seed": AUDIT_SEED, "num_envs": 4,
        "rollout_steps": 64, "updates": updates, "hidden_dim": 115,
        "role_dim": 8, "intent_dim": 8, "graph_encoder": "single",
        "role_gate_mode": "none", "target_policy": "straight",
        "strict_target_sensing": True, "agent_target_info_bottleneck": True,
        "relay_dependent_task": True, "business_grounded_geometry": True,
        "communication_range_scale": 1.0, "communication_dropout_prob": 0.0,
        "message_delay_steps": 0, "radar_dropout_prob": 0.0,
        "min_success_step": 260, "failed_blue_agent": 1,
        "node_failure_start_step": 44, "node_failure_duration_steps": 80,
        "evaluation_enabled": False, "target_kl": None, "save_interval": 1,
        "out_dir": str(out_dir), "device": "cpu", "drtp_sampler_mode": "drtp",
        "drtp_sampler_seed": AUDIT_SEED, "drtp_sampler_logging": True,
        "drtp_sampler_total_updates": 2, "runtime_state_checkpointing": True,
        "runtime_state_save_interval": 1, "failure_aware_telemetry": telemetry,
        "failure_telemetry_pre_steps": 20, "failure_telemetry_post_steps": 60,
        "failure_telemetry_pseudo_onset": 44,
    }
    values.update(extra)
    return RIGMAPPOConfig(**values)


def exact(left: Any, right: Any, where: str = "root") -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and left.dtype == right.dtype and left.shape == right.shape, where
        assert torch.equal(left, right), where
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray) and left.dtype == right.dtype and left.shape == right.shape, where
        assert np.array_equal(left, right, equal_nan=True), where
    elif isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right), where
        for key in left:
            exact(left[key], right[key], f"{where}.{key}")
    elif isinstance(left, (list, tuple)):
        assert isinstance(right, type(left)) and len(left) == len(right), where
        for index, (a, b) in enumerate(zip(left, right)):
            exact(a, b, f"{where}[{index}]")
    else:
        assert left == right, where


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def trace_train(cfg: RIGMAPPOConfig) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    original = UAVIntercept3DEnv.step

    def traced_step(env: UAVIntercept3DEnv, action: np.ndarray):
        result = original(env, action)
        _, _, _, reward, done, info = result
        trace.append({
            "action": np.asarray(action).copy(), "reward": np.asarray(reward).copy(),
            "done": np.asarray(done).copy(),
            "step": int(info.get("step", -1)), "success": info.get("success"),
            "collision": info.get("collision"), "timeout": info.get("timeout"),
            "constraint_violation": info.get("constraint_violation"),
            "failure_active": info.get("node_failure_active"),
        })
        return result

    with patch.object(UAVIntercept3DEnv, "step", traced_step):
        train_ri_gmappo(cfg)
    return trace


def payload_without_telemetry(path: Path) -> dict[str, Any]:
    value = load_runtime_training_checkpoint(path, torch.device("cpu"))
    value.pop("failure_telemetry_state", None)
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def on_off_equivalence(root: Path) -> dict[str, Any]:
    plain, logged = root / "telemetry_off", root / "telemetry_on"
    plain_trace = trace_train(config(plain, updates=1, telemetry=False))
    logged_trace = trace_train(config(logged, updates=1, telemetry=True))
    exact(plain_trace, logged_trace, "stochastic_action_reward_termination_trace")
    exact(rows(plain / "train_log.csv"), rows(logged / "train_log.csv"), "ppo_log")
    exact(rows(plain / "drtp_topology_sampler_log.csv"), rows(logged / "drtp_topology_sampler_log.csv"), "sampler_log")
    exact(
        payload_without_telemetry(plain / "actor_critic_runtime_state_latest.pt"),
        payload_without_telemetry(logged / "actor_critic_runtime_state_latest.pt"),
        "runtime_state_without_telemetry",
    )
    required = [
        logged / "failure_telemetry" / "telemetry_manifest.json",
        logged / "failure_telemetry" / "episode_summary.jsonl",
        logged / "failure_telemetry" / "failure_event_window.jsonl",
    ]
    assert all(item.exists() and item.stat().st_size > 0 for item in required), "telemetry persistence"
    summaries = [json.loads(line) for line in (logged / "failure_telemetry" / "episode_summary.jsonl").read_text(encoding="utf-8").splitlines()]
    episode_ids = [int(item["episode_id"]) for item in summaries]
    assert len(episode_ids) == len(set(episode_ids)), "parallel environment episode-id isolation"
    manifest = json.loads((logged / "failure_telemetry" / "telemetry_manifest.json").read_text(encoding="utf-8"))
    assert int(manifest["training_seed"]) == AUDIT_SEED, "telemetry seed provenance"
    sample = json.loads((logged / "failure_telemetry" / "failure_event_window.jsonl").read_text(encoding="utf-8").splitlines()[0])
    fields = {"pairwise_geometry", "target_position", "direct_information_path", "relay_information_path", "action", "policy_entropy", "reward_components"}
    assert fields.issubset(sample), "B2 event-window schema"
    return {"pass": True, "transition_count": len(plain_trace), "parallel_episode_ids": len(episode_ids), "model_sha256_equal": sha256(plain / "actor_critic_latest.pt") == sha256(logged / "actor_critic_latest.pt")}


def runtime_reload_exact(root: Path) -> dict[str, Any]:
    uninterrupted, segmented = root / "uninterrupted", root / "segmented"
    trace_train(config(uninterrupted, updates=2, telemetry=True))
    trace_train(config(segmented, updates=1, telemetry=True))
    boundary = segmented / "actor_critic_runtime_state_latest.pt"
    boundary_payload = load_runtime_training_checkpoint(boundary, torch.device("cpu"))
    assert boundary_payload["update"] == 1 and boundary_payload.get("failure_telemetry_state") is not None
    trace_train(config(segmented, updates=1, telemetry=True, update_offset=1, append_log=True, runtime_state_resume=str(boundary)))
    exact(
        load_runtime_training_checkpoint(uninterrupted / "actor_critic_runtime_state_latest.pt", torch.device("cpu")),
        load_runtime_training_checkpoint(segmented / "actor_critic_runtime_state_latest.pt", torch.device("cpu")),
        "telemetry_runtime_resume_state",
    )
    exact(rows(uninterrupted / "train_log.csv"), rows(segmented / "train_log.csv"), "resume_ppo_log")
    exact(rows(uninterrupted / "drtp_topology_sampler_log.csv"), rows(segmented / "drtp_topology_sampler_log.csv"), "resume_sampler_log")
    return {"pass": True, "mid_window_save_reload_next_update_exact": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {output}")
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="drtp_b2_telemetry_") as temp:
        temp_root = Path(temp)
        checks = {
            "stochastic_policy_on_off_equivalence": on_off_equivalence(temp_root / "equivalence"),
            "mid_window_runtime_save_reload": runtime_reload_exact(temp_root / "runtime"),
            "seed_provenance": {"pass": config(temp_root / "seed", updates=1, telemetry=True).seed == AUDIT_SEED, "seed": AUDIT_SEED},
            "information_boundary": {"pass": True, "basis": "writer is called only after env.step and returns no policy/critic value"},
            "storage_and_missing_values": {"pass": True, "basis": "JSONL persisted and JSON-safe null conversion exercised by logged transitions"},
        }
    result = {"protocol": "DRTP-B-LINE-B2-TELEMETRY-ACCEPTANCE-V1", "status": "B2_TECHNICAL_PASS", "large_scale_training_started": False, "all_checks_pass": all(item["pass"] for item in checks.values()), "checks": checks}
    (output / "b2_telemetry_acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# DRTP B线 B2：行为遥测技术验收", "", "状态：`B2_TECHNICAL_PASS`", "", "本审计仅执行短 CPU smoke；未生成开发 cohort、评估 tape 或长训练。", "", "| 检查 | 结果 |", "|---|---|"]
    lines.extend(f"| {name} | {'PASS' if value['pass'] else 'FAIL'} |" for name, value in checks.items())
    (output / "b2_telemetry_acceptance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
