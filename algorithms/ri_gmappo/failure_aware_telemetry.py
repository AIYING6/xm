"""Read-only failure-aware training telemetry.

The writer observes an environment *after* the production transition and the
actor-legal graph that was used before that transition.  It never returns a
value to the policy, critic, sampler, reward function, or termination logic.
It is deliberately a JSONL evidence sink so a partial run remains inspectable.
"""
from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from envs.uav_intercept_3d_env import velocity_from_state


PROTOCOL = "DRTP-TRAINING-FAILURE-MECHANISM-V1"
SCHEMA_VERSION = 1
DEFAULT_PSEUDO_ONSET = 44
DEFAULT_PRE_STEPS = 20
DEFAULT_POST_STEPS = 60


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def canonical_line(value: dict[str, Any]) -> str:
    return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


class FailureAwareTelemetryWriter:
    """Write episode summaries and failure-relative event windows."""

    def __init__(
        self,
        output_dir: str | Path,
        *,
        training_seed: int,
        method: str,
        pre_steps: int = DEFAULT_PRE_STEPS,
        post_steps: int = DEFAULT_POST_STEPS,
        pseudo_onset: int = DEFAULT_PSEUDO_ONSET,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.training_seed = int(training_seed)
        self.method = str(method)
        self.pre_steps = int(pre_steps)
        self.post_steps = int(post_steps)
        self.pseudo_onset = int(pseudo_onset)
        self.states: dict[int, dict[str, Any]] = {}
        self.summary_path = self.output_dir / "episode_summary.jsonl"
        self.window_path = self.output_dir / "failure_event_window.jsonl"
        self._summary_file = self.summary_path.open("a", encoding="utf-8", newline="\n")
        self._window_file = self.window_path.open("a", encoding="utf-8", newline="\n")
        manifest = {
            "protocol": PROTOCOL,
            "schema_version": SCHEMA_VERSION,
            "training_seed": self.training_seed,
            "method": self.method,
            "pre_steps": self.pre_steps,
            "post_steps": self.post_steps,
            "pseudo_onset": self.pseudo_onset,
            "diagnostic_only": True,
            "actor_critic_input_unchanged": True,
            "summary_file": self.summary_path.name,
            "event_window_file": self.window_path.name,
        }
        (self.output_dir / "telemetry_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _new_state(self, env_index: int, episode_index: int, selection: Any) -> dict[str, Any]:
        group = str(getattr(selection, "group", "N")) if selection is not None else "N"
        condition = str(getattr(selection, "condition", "nominal")) if selection is not None else "nominal"
        onset = int(getattr(selection, "failure_start_step", self.pseudo_onset)) if selection is not None else self.pseudo_onset
        duration = int(getattr(selection, "failure_duration_steps", 0)) if selection is not None else 0
        failed_agent = int(getattr(selection, "failed_blue_agent", -1)) if selection is not None else -1
        if group == "N":
            onset, duration = self.pseudo_onset, 0
            condition = "nominal_pseudo_onset"
        return {
            "run_id": f"{self.method}_seed{self.training_seed}",
            "method": self.method,
            "training_seed": self.training_seed,
            "env_index": int(env_index),
            "episode_index": int(episode_index),
            "episode_id": int(self.training_seed * 1_000_000 + env_index * 10_000 + episode_index),
            "scenario_group": group,
            "scenario_member": condition,
            "failed_blue_agent": failed_agent,
            "scheduled_failure": bool(group != "N"),
            "scheduled_failure_onset": onset,
            "scheduled_failure_duration": duration,
            "step_count": 0,
            "total_reward": 0.0,
            "reward_components_sum": defaultdict(float),
            "failure_active_ever": False,
            "failure_triggered": False,
            "survived_to_onset": False,
            "terminal": False,
            "terminal_step": None,
            "termination_reason": None,
            "success": 0,
            "collision": 0,
            "timeout": 0,
            "constraint_violation": 0,
            "event_rows": [],
        }

    @staticmethod
    def _termination_reason(info: dict[str, Any]) -> str | None:
        if float(info.get("success", 0.0) or 0.0) > 0.5:
            return "success"
        if float(info.get("collision", 0.0) or 0.0) > 0.5:
            return "collision"
        if float(info.get("constraint_violation", 0.0) or 0.0) > 0.5:
            return "constraint_violation"
        if float(info.get("timeout", 0.0) or 0.0) > 0.5:
            return "timeout"
        return None

    def _row(
        self,
        state: dict[str, Any],
        *,
        update: int,
        env_step: int,
        pre_step: int,
        env: Any,
        graph_before: dict[str, Any],
        action: np.ndarray,
        reward: np.ndarray,
        policy_entropy: float | None,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        onset = int(state["scheduled_failure_onset"])
        rel = int(env_step - onset)
        blue_velocity = np.asarray(
            [velocity_from_state(speed, heading, gamma) for speed, heading, gamma in zip(env.blue_speed, env.blue_heading, env.blue_gamma)],
            dtype=np.float32,
        )
        failure_active = bool(float(info.get("node_failure_active", 0.0) or 0.0) > 0.5)
        # Every telemetry value is an immutable snapshot.  ``np.asarray``
        # alone may retain an environment-owned buffer, which would corrupt a
        # previously buffered event row after later transitions or a resume.
        blue_position = np.asarray(env.blue_pos, dtype=np.float32).copy()
        target_position = np.asarray(getattr(env, "red_pos", np.zeros((1, 3), dtype=np.float32))[0], dtype=np.float32).copy()
        def distance(left: int, right: int) -> float:
            return float(np.linalg.norm(blue_position[left] - blue_position[right]))
        direct_available = bool(float(info.get("attacker_direct_target_information_t", 0.0) or 0.0) > 0.5)
        # The environment represents a usable relay route as a path string
        # (for example ``"0-1-2"``), not as a numeric indicator.  Preserve
        # that semantic representation rather than coercing it to float.
        relay_path = info.get("attacker_cache_paths_t")
        relay_available = bool(relay_path) and str(relay_path).lower() not in {"none", "null", "nan", "0"}
        information_path_state = "direct" if direct_available else "relay" if relay_available else "no_path"
        cache_age = getattr(env, "target_cache_delivery_step", None)
        if cache_age is not None:
            cache_age = (int(env_step) - np.asarray(cache_age, dtype=np.int64)).tolist()
        return {
            "protocol": PROTOCOL,
            "schema_version": SCHEMA_VERSION,
            "method": self.method,
            "training_seed": self.training_seed,
            "update": int(update),
            "env_index": int(state["env_index"]),
            "episode_index": int(state["episode_index"]),
            "episode_id": int(state["episode_id"]),
            "episode_step": int(pre_step),
            "env_step": int(env_step),
            "scenario_group": state["scenario_group"],
            "scenario_member": state["scenario_member"],
            "scheduled_failure": state["scheduled_failure"],
            "scheduled_failure_onset": onset,
            "scheduled_failure_duration": int(state["scheduled_failure_duration"]),
            "failure_active": failure_active,
            "failure_relative_step": rel,
            "blue_position": blue_position,
            "blue_velocity": blue_velocity,
            "blue_heading": np.asarray(env.blue_heading, dtype=np.float32).copy(),
            "blue_gamma": np.asarray(env.blue_gamma, dtype=np.float32).copy(),
            "target_position": target_position,
            "pairwise_geometry": {
                "scout_relay_distance": distance(0, 1),
                "relay_attacker_distance": distance(1, 2),
                "scout_attacker_distance": distance(0, 2),
                "scout_target_distance": float(np.linalg.norm(blue_position[0] - target_position)),
                "relay_target_distance": float(np.linalg.norm(blue_position[1] - target_position)),
                "attacker_target_distance": float(np.linalg.norm(blue_position[2] - target_position)),
            },
            "legal_communication_edges": np.asarray(graph_before.get("relation_adj", np.zeros((3, 4, 4)))[1]).copy(),
            "legal_union_edges": np.asarray(graph_before.get("adj", np.zeros((4, 4))).copy()),
            "direct_information_path": {
                "state": information_path_state,
                "attacker_direct_target_information": info.get("attacker_direct_target_information_t"),
                "attacker_direct_recovery_path": info.get("attacker_direct_recovery_path_t"),
                "attacker_window_direct_info": info.get("attacker_window_direct_info"),
            },
            "relay_information_path": {
                "attacker_cache_paths": info.get("attacker_cache_paths_t"),
                "relay_required_fresh_information": info.get("attacker_relay_required_fresh_information_t"),
                "relay1_in_cache_path": info.get("attacker_cache_path_includes_relay1_t"),
                "relay1_required_for_support": info.get("attacker_support_path_relay1_required_t"),
                "attacker_window_comm_info": info.get("attacker_window_comm_info"),
            },
            "scout_detection": np.asarray(getattr(env, "detected_by", []), dtype=np.float32).copy(),
            "attacker_valid_target_information": info.get("attacker_legal_target_information_t"),
            "attacker_has_fresh_target_information": info.get("attacker_has_fresh_target_info"),
            "cache_source": np.asarray(getattr(env, "target_cache_source", []), dtype=np.int64).copy(),
            "cache_freshness": {
                "age_by_agent": cache_age,
                "mean_age": info.get("target_cache_age_mean"),
                "confidence_mean": info.get("target_cache_confidence_mean"),
                "stale_rate": info.get("target_cache_stale_rate"),
            },
            "attack_window_state": np.asarray(getattr(env, "attack_window", []), dtype=np.float32).copy(),
            "task_support_state": {
                "chain_support": info.get("chain_support_t"),
                "chain_closed": info.get("chain_closed"),
                "relay_dependency_eligible": info.get("relay_dependency_eligible_t"),
            },
            "action": np.asarray(action, dtype=np.int64).copy(),
            "policy_entropy": policy_entropy,
            "reward": np.asarray(reward, dtype=np.float32).copy(),
            "reward_components": info.get("reward_components", {}),
            "cumulative_return": float(state["total_reward"] + float(np.asarray(reward).sum())),
            "success": info.get("success"),
            "collision": info.get("collision"),
            "timeout": info.get("timeout"),
            "constraint_violation": info.get("constraint_violation"),
            "termination_reason": self._termination_reason(info),
            "terminal": self._termination_reason(info) is not None,
        }

    def record_step(
        self,
        *,
        update: int,
        env_index: int,
        episode_index: int,
        env_step: int,
        pre_step: int,
        env: Any,
        graph_before: dict[str, Any],
        action: np.ndarray,
        reward: np.ndarray,
        policy_entropy: float | None,
        info: dict[str, Any],
        selection: Any,
    ) -> None:
        state = self.states.get(int(env_index))
        expected_id = int(self.training_seed * 1_000_000 + env_index * 10_000 + episode_index)
        if state is None or int(state["episode_id"]) != expected_id:
            if state is not None:
                self._finalize(env_index, state, partial=True)
            state = self._new_state(env_index, episode_index, selection)
            self.states[int(env_index)] = state
        row = self._row(
            state, update=update, env_step=env_step, pre_step=pre_step, env=env,
            graph_before=graph_before, action=action, reward=reward,
            policy_entropy=policy_entropy, info=info,
        )
        state["step_count"] += 1
        state["total_reward"] += float(np.asarray(reward, dtype=np.float32).sum())
        components = info.get("reward_components", {})
        if isinstance(components, dict):
            for key, value in components.items():
                if isinstance(value, (int, float, np.number)):
                    state["reward_components_sum"][str(key)] += float(value)
        state["failure_active_ever"] = bool(state["failure_active_ever"] or row["failure_active"])
        state["failure_triggered"] = bool(state["failure_triggered"] or row["failure_active"])
        state["survived_to_onset"] = bool(state["survived_to_onset"] or row["failure_relative_step"] >= 0)
        if -self.pre_steps <= row["failure_relative_step"] <= self.post_steps:
            state["event_rows"].append(row)
        reason = row["termination_reason"]
        if reason is not None:
            state.update({
                "terminal": True, "terminal_step": int(env_step), "termination_reason": reason,
                "success": int(float(info.get("success", 0.0) or 0.0) > 0.5),
                "collision": int(float(info.get("collision", 0.0) or 0.0) > 0.5),
                "timeout": int(float(info.get("timeout", 0.0) or 0.0) > 0.5),
                "constraint_violation": int(float(info.get("constraint_violation", 0.0) or 0.0) > 0.5),
            })

    def finalize_episode(self, env_index: int) -> None:
        state = self.states.pop(int(env_index), None)
        if state is not None:
            self._finalize(env_index, state, partial=False)

    def _finalize(self, env_index: int, state: dict[str, Any], *, partial: bool) -> None:
        for row in state["event_rows"]:
            self._window_file.write(canonical_line(row) + "\n")
        summary = {key: value for key, value in state.items() if key != "event_rows"}
        summary["summary_status"] = "training_boundary_partial" if partial and not state["terminal"] else "completed"
        summary["reward_components_sum"] = dict(state["reward_components_sum"])
        summary["event_window_step_count"] = len(state["event_rows"])
        self._summary_file.write(canonical_line(summary) + "\n")
        self._summary_file.flush()
        self._window_file.flush()

    def state_dict(self) -> dict[str, Any]:
        return {"states": copy.deepcopy(self.states)}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if not isinstance(state, dict) or not isinstance(state.get("states"), dict):
            raise ValueError("invalid failure-aware telemetry runtime state")
        restored = copy.deepcopy(state["states"])
        for item in restored.values():
            item["reward_components_sum"] = defaultdict(float, item.get("reward_components_sum", {}))
        self.states = {int(key): value for key, value in restored.items()}

    def close(self) -> None:
        for env_index, state in list(self.states.items()):
            self._finalize(env_index, state, partial=True)
        self.states.clear()
        self._summary_file.close()
        self._window_file.close()
