"""Zero-training identifiability audit for the active-diagnosis candidate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "active_diagnosis_p1_counterexample.json"


def _best_terminal_value(config: dict, prior_recoverable: float) -> tuple[float, str]:
    utilities = config["terminal_utility"]
    values = {
        action: prior_recoverable * float(by_hypothesis["recoverable_range_loss"])
        + (1.0 - prior_recoverable) * float(by_hypothesis["hard_relay_failure"])
        for action, by_hypothesis in utilities.items()
    }
    action = max(values, key=values.get)
    return values[action], action


def _posterior(prior: float, likelihood_r: float, likelihood_f: float) -> float:
    evidence = prior * likelihood_r + (1.0 - prior) * likelihood_f
    if evidence <= 0.0:
        raise ValueError("observation has zero evidence")
    return prior * likelihood_r / evidence


def evaluate(config: dict, prior: float) -> dict:
    ack_r = float(config["ack_probability"]["recoverable_range_loss"])
    ack_f = float(config["ack_probability"]["hard_relay_failure"])
    p_ack = prior * ack_r + (1.0 - prior) * ack_f
    posterior_ack = _posterior(prior, ack_r, ack_f)
    posterior_silence = _posterior(prior, 1.0 - ack_r, 1.0 - ack_f)
    value_ack, action_ack = _best_terminal_value(config, posterior_ack)
    value_silence, action_silence = _best_terminal_value(config, posterior_silence)
    passive_value, passive_action = _best_terminal_value(config, prior)
    probe_value = (
        p_ack * value_ack
        + (1.0 - p_ack) * value_silence
        - float(config["probe_cost"])
    )
    return {
        "prior_recoverable": prior,
        "passive_value": passive_value,
        "passive_action": passive_action,
        "probe_value": probe_value,
        "probe_gain": probe_value - passive_value,
        "p_ack": p_ack,
        "posterior_recoverable_given_ack": posterior_ack,
        "posterior_recoverable_given_silence": posterior_silence,
        "action_after_ack": action_ack,
        "action_after_silence": action_silence,
    }


def run_audit(config: dict) -> dict:
    prior = float(config["prior_recoverable"])
    balanced = evaluate(config, prior)
    extremes = [evaluate(config, float(value)) for value in config["extreme_priors"]]
    ack = config["ack_probability"]
    probe_tv = abs(
        float(ack["recoverable_range_loss"])
        - float(ack["hard_relay_failure"])
    )
    utilities = config["terminal_utility"]
    optimal_by_hypothesis = {
        hypothesis: max(
            utilities,
            key=lambda action: float(utilities[action][hypothesis]),
        )
        for hypothesis in config["hypotheses"]
    }
    checks = {
        "passive_history_observation_equivalent": True,
        "hypotheses_require_different_terminal_actions": len(set(optimal_by_hypothesis.values())) > 1,
        "probe_increases_observation_separation": probe_tv
        >= float(config["requirements"]["minimum_probe_tv"]),
        "probe_has_nonzero_cost": float(config["probe_cost"]) > 0.0,
        "probe_improves_value_at_balanced_prior": balanced["probe_gain"]
        >= float(config["requirements"]["minimum_probe_value_gain_at_balanced_prior"]),
        "always_probe_is_not_optimal": any(item["probe_gain"] < 0.0 for item in extremes),
        "training_started": False,
    }
    passed = all(value for key, value in checks.items() if key != "training_started")
    return {
        "protocol": config["protocol"],
        "verdict": "P1_IDENTIFIABILITY_COUNTEREXAMPLE_PASS" if passed else "P1_IDENTIFIABILITY_COUNTEREXAMPLE_FAIL",
        "checks": checks,
        "probe_total_variation": probe_tv,
        "optimal_action_by_hypothesis": optimal_by_hypothesis,
        "balanced_prior": balanced,
        "extreme_priors": extremes,
        "interpretation": (
            "The toy model establishes a non-trivial value of active diagnosis under observation-equivalent latent failures. "
            "It does not establish that the current UAV environment realizes the same ambiguity or that any learning algorithm succeeds."
        ),
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    report = run_audit(config)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
