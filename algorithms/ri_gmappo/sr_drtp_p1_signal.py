"""Write-only PP disagreement signals for the prospective SR-DRTP P1 audit."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from algorithms.ri_gmappo.drtp_topology_sampler import DIFFICULTY_MAX, FAILURE_GROUPS, NOMINAL_GROUP


def _top(values: dict[str, float]) -> str:
    return sorted(FAILURE_GROUPS, key=lambda group: (-float(values[group]), group))[0]


class SRDRTPP1SignalWriter:
    """Training-only PP-versus-online signal recorder.

    The writer is not supplied to PPO or the topology sampler.  Its only
    mutable state tracks whether the immediately preceding scheduled probe
    disagreed, which implements the frozen two-consecutive-observation rule.
    """

    def __init__(self, output_dir: Path, *, append: bool = False):
        self.directory = output_dir / "sr_drtp_p1_signal"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "pp_disagreement.csv"
        self._file = self.path.open("a" if append else "w", newline="", encoding="utf-8")
        self._fields = [
            "update", "training_only", "online_top_risk_group", "pp_top_risk_group",
            "pp_online_disagreement", "previous_scheduled_disagreement", "high_risk",
            "online_difficulty_json", "pp_difficulty_json", "probe_record_count",
            "probe_env_steps", "probe_sha256",
        ]
        self._writer = csv.DictWriter(self._file, fieldnames=self._fields)
        if not append or self.path.stat().st_size == 0:
            self._writer.writeheader()
        self.previous_disagreement = False
        self.row_count = 0

    @staticmethod
    def _pp_difficulty(records: list[dict[str, Any]]) -> dict[str, float]:
        by_group: dict[str, list[float]] = {group: [] for group in (NOMINAL_GROUP, *FAILURE_GROUPS)}
        for record in records:
            by_group[str(record["group"])].append(float(record["episode_return"]))
        if any(not by_group[group] for group in by_group):
            raise ValueError("P1 PP probe must cover nominal and every failure group")
        nominal = sum(by_group[NOMINAL_GROUP]) / len(by_group[NOMINAL_GROUP])
        return {
            group: min(
                DIFFICULTY_MAX,
                max(0.0, (nominal - sum(by_group[group]) / len(by_group[group])) / max(abs(nominal), 1e-8)),
            )
            for group in FAILURE_GROUPS
        }

    def record(self, *, update: int, sampler_state: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
        online = {group: float(sampler_state["last_difficulty"][group]) for group in FAILURE_GROUPS}
        pp = self._pp_difficulty(records)
        online_top, pp_top = _top(online), _top(pp)
        disagreement = online_top != pp_top
        high_risk = bool(self.previous_disagreement and disagreement)
        encoded_records = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        row = {
            "update": int(update), "training_only": True,
            "online_top_risk_group": online_top, "pp_top_risk_group": pp_top,
            "pp_online_disagreement": disagreement,
            "previous_scheduled_disagreement": self.previous_disagreement,
            "high_risk": high_risk,
            "online_difficulty_json": json.dumps(online, sort_keys=True),
            "pp_difficulty_json": json.dumps(pp, sort_keys=True),
            "probe_record_count": len(records),
            "probe_env_steps": sum(int(record["steps"]) for record in records),
            "probe_sha256": hashlib.sha256(encoded_records).hexdigest(),
        }
        self._writer.writerow(row)
        self._file.flush()
        self.previous_disagreement = disagreement
        self.row_count += 1
        return row

    def state_dict(self) -> dict[str, Any]:
        return {"format": "sr_drtp_p1_signal_v1", "previous_disagreement": self.previous_disagreement, "row_count": self.row_count}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("format") != "sr_drtp_p1_signal_v1":
            raise ValueError("unsupported SR-DRTP P1 signal runtime state")
        self.previous_disagreement = bool(state["previous_disagreement"])
        self.row_count = int(state["row_count"])

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()
        (self.directory / "manifest.json").write_text(
            json.dumps({
                "format": "sr_drtp_p1_signal_v1", "status": "COMPLETED", "training_only": True,
                "formal_or_heldout_evaluation_tape_used": False, "actor_or_critic_input": False,
                "sampler_or_ppo_control": False, "row_count": self.row_count,
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
