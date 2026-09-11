"""Zero-training discrimination audit for P41 v2."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_v2_env import P41_V2_SCENARIOS, RecoverableServiceChainV2Env


def _known_live(env: RecoverableServiceChainV2Env):
    return env._request_at(env.scenario.known.site)


def _future_live(env: RecoverableServiceChainV2Env):
    return env._request_at(env.scenario.forecast.site)


def _future_expected_value(env: RecoverableServiceChainV2Env) -> float:
    forecast = env.scenario.forecast
    return forecast.probability * forecast.value


def _choice(env: RecoverableServiceChainV2Env, policy: str) -> int | None:
    known = _known_live(env)
    future = _future_live(env)
    if future is not None:
        return future.site
    if policy == "static":
        return known.site if known is not None else None
    if policy == "value":
        if known is not None and _future_expected_value(env) <= known.value:
            return known.site
        return env.scenario.forecast.site
    if policy == "deadline":
        return known.site if known is not None else None
    if policy == "topology":
        # The scheduled outage is public. Prefer the forecast site only when
        # the known service cannot remain chain-supported through its duration.
        if known is not None:
            finish = env.step_count + env.service_duration
            outage_overlap = any(env.scenario.outage_site == known.site and env.scenario.outage_start <= tick < env.scenario.outage_start + env.scenario.outage_duration for tick in range(env.step_count, finish + 1))
            if not outage_overlap:
                return known.site
        return env.scenario.forecast.site
    if policy == "oracle":
        # Audit upper comparator uses tape realization but obeys identical
        # actions, service duration, and chain requirements.
        if env.scenario.forecast.realized:
            return env.scenario.forecast.site
        return known.site if known is not None else None
    raise ValueError(policy)


def _actions(env: RecoverableServiceChainV2Env, policy: str) -> np.ndarray:
    choice = _choice(env, policy)
    if choice is None:
        return np.asarray((0, 0, 0), dtype=np.int64)
    scout = choice + 1
    relay = 0 if env.relay_site == choice else choice + 1
    # Service may act only after a delivered confirmation; this policy reads the
    # same legal cache state that is represented in the service actor input.
    service = choice + 1 if choice in env.cache and env.step_count - env.cache[choice] <= env.message_ttl else 0
    return np.asarray((scout, relay, service), dtype=np.int64)


def rollout(scenario, policy: str) -> dict:
    env = RecoverableServiceChainV2Env(scenario)
    env.reset()
    while not env.done:
        env.step(_actions(env, policy))
    return {"policy": policy, **env.terminal_summary()}


def main() -> None:
    out = Path("artifacts/diagnostics/p41_recoverable_service_chain_v2_rule_audit_20260911_v2")
    out.mkdir(parents=True, exist_ok=False)
    policies = ("static", "value", "deadline", "topology", "oracle")
    rows = [rollout(scenario, policy) for scenario in P41_V2_SCENARIOS for policy in policies]
    with (out / "P41_V2_RULE_AUDIT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("scenario", "policy", "completed_value", "commit_used", "aborted", "reconfigurations", "events"))
        writer.writeheader(); writer.writerows(rows)
    winners = {}
    for scenario in P41_V2_SCENARIOS:
        local = [row for row in rows if row["scenario"] == scenario.name and row["policy"] != "oracle"]
        top = max(row["completed_value"] for row in local)
        winners[scenario.name] = [row["policy"] for row in local if row["completed_value"] == top]
    unique = {selected[0] for selected in winners.values() if len(selected) == 1}
    oracle_by_scenario = {
        scenario.name: next(row["completed_value"] for row in rows if row["scenario"] == scenario.name and row["policy"] == "oracle")
        for scenario in P41_V2_SCENARIOS
    }
    no_single_rule_matches_oracle_all = all(
        any(
            row["completed_value"] < oracle_by_scenario[scenario.name]
            for scenario in P41_V2_SCENARIOS
            for row in rows
            if row["scenario"] == scenario.name and row["policy"] == policy
        )
        for policy in ("static", "value", "deadline", "topology")
    )
    result = {
        "protocol": "P41-RECOVERABLE-SERVICE-CHAIN-V2-RULE-AUDIT-V1",
        "training_started": False,
        "scenarios": [scenario.name for scenario in P41_V2_SCENARIOS],
        "winners": winners,
        "checks": {
            "two_or_more_unique_rule_winners": len(unique) >= 2,
            "every_scenario_has_nonzero_rule_value": all(max(row["completed_value"] for row in rows if row["scenario"] == scenario.name and row["policy"] != "oracle") > 0.0 for scenario in P41_V2_SCENARIOS),
            "no_single_rule_matches_oracle_all": no_single_rule_matches_oracle_all,
            "reconfiguration_has_consequence": any(row["aborted"] for row in rows if row["policy"] != "oracle"),
        },
    }
    result["verdict"] = "P41_V2_T1_T3_PASS" if all(result["checks"].values()) else "P41_V2_T1_T3_STOP"
    (out / "P41_V2_RULE_AUDIT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
