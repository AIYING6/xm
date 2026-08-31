"""Read-only SR-DRTP training telemetry.

This module deliberately has no dependency on the sampler/controller path.
It records training-side observables for a *future* risk-state audit, but it
cannot alter an action, reward, PPO update, reset selection, or checkpoint
choice.  Keeping this boundary explicit is important: P0 establishes only
instrumentation feasibility, not a new training algorithm.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS, NOMINAL_GROUP, UNIFORM_Q


SCHEMA_VERSION = "sr_drtp_training_telemetry_v1"


class SRDRTPTelemetryWriter:
    """Append fixed-schema, training-only diagnostic rows.

    ``record`` accepts plain values and returns ``None``.  This is intentional:
    a caller has no score to feed into a sampler or a policy-update decision.
    """

    def __init__(self, output_dir: Path, *, append: bool = False) -> None:
        self.output_dir = Path(output_dir)
        self.directory = self.output_dir / "sr_drtp_telemetry"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "training_state.csv"
        self._append = bool(append)
        self._file = self.path.open("a" if append else "w", newline="", encoding="utf-8")
        self._fields = self.fields()
        self._writer = csv.DictWriter(self._file, fieldnames=self._fields)
        if not append or self.path.stat().st_size == 0:
            self._writer.writeheader()
        self.row_count = 0
        self._write_manifest(status="RUNNING")

    @staticmethod
    def fields() -> list[str]:
        fields = [
            "schema_version", "training_only", "update", "sampler_mode",
            "train_avg_reward", "approx_kl", "entropy", "value_loss", "grad_norm",
            "explained_variance", "advantage_mean", "advantage_std",
            "q_uniform_l1", "q_rank_signature", "q_step_l1", "adaptation_count",
            "probe_available", "probe_mean_return", "probe_worst_group_return",
            "probe_online_disagreement",
        ]
        fields += [f"q_{group}" for group in FAILURE_GROUPS]
        fields += [f"ema_{group}" for group in (NOMINAL_GROUP, *FAILURE_GROUPS)]
        fields += [f"difficulty_{group}" for group in FAILURE_GROUPS]
        fields += [f"window_count_{group}" for group in (NOMINAL_GROUP, *FAILURE_GROUPS)]
        return fields

    def _write_manifest(self, *, status: str) -> None:
        payload = {
            "format": SCHEMA_VERSION,
            "status": status,
            "training_only": True,
            "formal_evaluation_tape_used": False,
            "actor_or_critic_input": False,
            "sampler_or_ppo_control": False,
            "row_count": self.row_count,
            "path": str(self.path),
        }
        (self.directory / "manifest.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _rank_signature(q: dict[str, float]) -> str:
        return ">".join(sorted(FAILURE_GROUPS, key=lambda group: (-float(q[group]), group)))

    def record(
        self,
        *,
        update: int,
        sampler_mode: str,
        sampler_state: dict[str, Any] | None,
        train_info: dict[str, Any],
        train_avg_reward: float,
        probe_summary: dict[str, float] | None = None,
    ) -> None:
        """Write one observation without returning a decision variable."""
        state = sampler_state or {}
        q = {group: float(state.get("q", {}).get(group, UNIFORM_Q)) for group in FAILURE_GROUPS}
        ema = state.get("ema", {})
        difficulty = state.get("last_difficulty", {})
        windows = state.get("window_returns", {})
        probe = probe_summary or {}
        row: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "training_only": True,
            "update": int(update),
            "sampler_mode": str(sampler_mode),
            "train_avg_reward": float(train_avg_reward),
            "approx_kl": float(train_info["approx_kl"]),
            "entropy": float(train_info["entropy"]),
            "value_loss": float(train_info["value_loss"]),
            "grad_norm": float(train_info["grad_norm"]),
            "explained_variance": float(train_info["explained_variance"]),
            "advantage_mean": float(train_info.get("advantage_mean", 0.0)),
            "advantage_std": float(train_info.get("advantage_std", 0.0)),
            "q_uniform_l1": sum(abs(q[group] - UNIFORM_Q) for group in FAILURE_GROUPS),
            "q_rank_signature": self._rank_signature(q),
            "q_step_l1": float(state.get("last_q_step_l1", 0.0)),
            "adaptation_count": int(state.get("adaptation_count", 0)),
            "probe_available": bool(probe_summary is not None),
            "probe_mean_return": probe.get("mean_return", ""),
            "probe_worst_group_return": probe.get("worst_group_return", ""),
            "probe_online_disagreement": probe.get("online_disagreement", ""),
        }
        row.update({f"q_{group}": q[group] for group in FAILURE_GROUPS})
        row.update({f"ema_{group}": "" if ema.get(group) is None else float(ema[group]) for group in (NOMINAL_GROUP, *FAILURE_GROUPS)})
        row.update({f"difficulty_{group}": float(difficulty.get(group, 0.0)) for group in FAILURE_GROUPS})
        row.update({f"window_count_{group}": len(windows.get(group, [])) for group in (NOMINAL_GROUP, *FAILURE_GROUPS)})
        self._writer.writerow(row)
        self._file.flush()
        self.row_count += 1

    def state_dict(self) -> dict[str, Any]:
        return {"format": SCHEMA_VERSION, "row_count": int(self.row_count)}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("format") != SCHEMA_VERSION:
            raise ValueError("unsupported SR-DRTP telemetry runtime state")
        self.row_count = int(state["row_count"])

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()
        self._write_manifest(status="COMPLETED")
