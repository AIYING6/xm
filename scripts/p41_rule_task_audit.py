"""Zero-training rule audit for P41 task discrimination.

The policies are intentionally simple and have access only to their role's
publicly legal observations.  This is a task audit, not a performance claim.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_env import P41_SCENARIOS, RecoverableServiceChainEnv


def _site_by_score(env: RecoverableServiceChainEnv, kind: str) -> int | None:
    choices = [request for request in env.scenario.requests if env._released(request)]
    if not choices:
        return None
    if kind == "static":
        return 0 if any(request.site == 0 for request in choices) else choices[0].site
    if kind == "value":
        return max(choices, key=lambda request: (request.value, -request.deadline)).site
    if kind == "deadline":
        return min(choices, key=lambda request: (request.deadline, -request.value)).site
    if kind == "topology":
        reachable = [request for request in choices if request.site == env.relay_site and not env._outage_active(request.site)]
        return (reachable or choices)[0].site
    raise ValueError(kind)


def _rule_actions(env: RecoverableServiceChainEnv, kind: str) -> np.ndarray:
    scout_site = _site_by_score(env, kind)
    # Relay only uses released requests and the current outage.  A nonzero action
    # initiates a one-step reconfiguration; it cannot transmit in that step.
    relay_site = scout_site if scout_site is not None else env.relay_site
    service_candidates = []
    for site, (received, request) in env.cache.items():
        if env.step_count - received <= env.message_ttl and env._released(request):
            service_candidates.append(request)
    if kind == "value":
        service_site = max(service_candidates, key=lambda request: request.value).site if service_candidates else None
    elif kind == "deadline":
        service_site = min(service_candidates, key=lambda request: request.deadline).site if service_candidates else None
    else:
        service_site = next((request.site for request in service_candidates if request.site == scout_site), None)
        if service_site is None and service_candidates:
            service_site = service_candidates[0].site
    return np.asarray((0 if scout_site is None else scout_site + 1, 0 if relay_site == env.relay_site else relay_site + 1, 0 if service_site is None else service_site + 1), dtype=np.int64)


def _oracle_actions(env: RecoverableServiceChainEnv) -> np.ndarray:
    # Audit-only upper comparator: it knows released requests, but obeys the
    # same reconfiguration and service-duration dynamics.  It is not fair to
    # a decentralized policy and is never a learning baseline.
    candidates = [request for request in env.scenario.requests if env._released(request)]
    site = max(candidates, key=lambda request: (request.value / max(1, request.deadline - env.step_count), request.value)).site if candidates else None
    cached = [request for received, request in env.cache.values() if env.step_count - received <= env.message_ttl and env._released(request)]
    service_site = max(cached, key=lambda request: request.value).site if cached else None
    return np.asarray((0 if site is None else site + 1, 0 if site is None or site == env.relay_site else site + 1, 0 if service_site is None else service_site + 1), dtype=np.int64)


def rollout(scenario, kind: str) -> dict:
    env = RecoverableServiceChainEnv(scenario)
    env.reset()
    while not env.done:
        actions = _oracle_actions(env) if kind == "oracle" else _rule_actions(env, kind)
        env.step(actions)
    return {"policy": kind, **env.terminal_summary()}


def main() -> None:
    out = Path("artifacts/diagnostics/p41_recoverable_service_chain_rule_audit_20260911_v2")
    out.mkdir(parents=True, exist_ok=False)
    policies = ("static", "value", "deadline", "topology", "oracle")
    rows = [rollout(scenario, policy) for scenario in P41_SCENARIOS for policy in policies]
    with (out / "P41_RULE_AUDIT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("scenario", "policy", "completed_value", "completed_count", "expired_count", "reconfigurations", "events"))
        writer.writeheader(); writer.writerows(rows)
    winners = {}
    for scenario in P41_SCENARIOS:
        local = [row for row in rows if row["scenario"] == scenario.name and row["policy"] != "oracle"]
        top = max(row["completed_value"] for row in local)
        winners[scenario.name] = [row["policy"] for row in local if row["completed_value"] == top]
    unique_winners = {
        selected[0]
        for selected in winners.values()
        if len(selected) == 1
    }
    all_tied = all(len(selected) > 1 for selected in winners.values())
    reconfiguration_observed = any(row["reconfigurations"] > 0 for row in rows if row["policy"] != "oracle")
    result = {
        "protocol": "P41-RECOVERABLE-SERVICE-CHAIN-RULE-AUDIT-V1",
        "training_started": False,
        "scenarios": [scenario.name for scenario in P41_SCENARIOS],
        "winners": winners,
        "checks": {
            "cross_policy_winners": len(unique_winners) >= 2,
            "no_universal_rule_tie": not all_tied,
            "reconfiguration_observed": reconfiguration_observed,
            "oracle_not_worse_than_rules": all(
                next(row["completed_value"] for row in rows if row["scenario"] == scenario.name and row["policy"] == "oracle") >= max(row["completed_value"] for row in rows if row["scenario"] == scenario.name and row["policy"] != "oracle")
                for scenario in P41_SCENARIOS
            ),
        },
    }
    result["verdict"] = "P41_T1_T3_PASS" if all(result["checks"].values()) else "P41_T1_T3_STOP"
    (out / "P41_RULE_AUDIT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
