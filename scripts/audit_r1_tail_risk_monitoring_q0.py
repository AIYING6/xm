"""Run the R1 zero-training rule and beam-oracle identifiability audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from envs.tail_risk_persistent_monitoring import TailRiskPersistentMonitoringAudit


def schedule(spec: dict, horizon: int) -> np.ndarray:
    value = np.full((horizon, 4), float(spec["ordinary_windows"][0][2]), dtype=np.float64)
    for start, stop, weight in spec["ordinary_windows"]:
        value[int(start):int(stop), 1:] = float(weight)
    for start, stop, weight in spec["critical_windows"]:
        value[int(start):int(stop), 0] = float(weight)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to run without --execute")
    config = json.loads(args.config.read_text(encoding="utf-8")); horizon = int(config["horizon"])
    records = []
    for family, spec in config["scenario_families"].items():
        env = TailRiskPersistentMonitoringAudit(schedule(spec, horizon), horizon)
        outcomes = {rule: env.rollout_rule(rule) for rule in config["rules"]}
        oracle = env.rollout_beam_oracle()
        for rule, state in outcomes.items():
            records.append({"family": family, "policy": rule, "reward": state.reward, "critical_failure_fraction": state.critical_failure_steps / horizon, "mean_final_age": float(state.age.mean())})
        records.append({"family": family, "policy": "beam_oracle", "reward": oracle.reward, "critical_failure_fraction": oracle.critical_failure_steps / horizon, "mean_final_age": float(oracle.age.mean())})
    rule_rows = [row for row in records if row["policy"] != "beam_oracle"]
    families = list(config["scenario_families"])
    best_rules = {family: max((row for row in rule_rows if row["family"] == family), key=lambda row: row["reward"])["policy"] for family in families}
    oracle_gains = []
    for family in families:
        best_rule = max(row["reward"] for row in rule_rows if row["family"] == family)
        oracle_reward = next(row["reward"] for row in records if row["family"] == family and row["policy"] == "beam_oracle")
        oracle_gains.append(oracle_reward - best_rule)
    critical = [row["critical_failure_fraction"] for row in rule_rows]
    oracle_failures = [row["critical_failure_fraction"] for row in records if row["policy"] == "beam_oracle"]
    gates = config["gates"]
    checks = {
        "critical_failure_nontrivial": gates["critical_failure_nontrivial_min"] <= float(np.mean(critical)) <= gates["critical_failure_nontrivial_max"],
        "rule_crossing_exists": len(set(best_rules.values())) >= gates["distinct_best_rule_count_min"],
        "oracle_gap_exists": min(oracle_gains) >= gates["oracle_gain_min"],
        "oracle_not_perfect_in_every_family": sum(value > 0.0 for value in oracle_failures) >= gates["oracle_nonzero_failure_family_count_min"],
    }
    result = {"protocol": config["protocol"], "verdict": "R1_Q0_PASS" if all(checks.values()) else "R1_Q0_STOP", "records": records, "best_rule_by_family": best_rules, "oracle_gains": oracle_gains, "checks": checks, "training_started": False, "evaluation_started": False}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2), encoding="utf-8"); print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
