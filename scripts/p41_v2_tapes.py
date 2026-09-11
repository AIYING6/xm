"""Deterministic scenario-tape generation for the P41 v2 T4 contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_v2_env import FutureForecast, KnownRequest, P41V2Scenario


FAMILIES = ("commit_now_like", "defer_for_value_like", "reroute_before_outage_like")


def scenario_to_dict(scenario: P41V2Scenario, family: str) -> dict:
    return {
        "family": family,
        "name": scenario.name,
        "known": {"site": scenario.known.site, "value": scenario.known.value, "deadline": scenario.known.deadline},
        "forecast": {
            "site": scenario.forecast.site,
            "probability": scenario.forecast.probability,
            "value": scenario.forecast.value,
            "release": scenario.forecast.release,
            "deadline": scenario.forecast.deadline,
            "realized": scenario.forecast.realized,
        },
        "outage": {"site": scenario.outage_site, "start": scenario.outage_start, "duration": scenario.outage_duration},
    }


def scenario_from_dict(row: dict) -> P41V2Scenario:
    known = row["known"]; forecast = row["forecast"]; outage = row["outage"]
    return P41V2Scenario(
        name=str(row["name"]),
        known=KnownRequest(site=int(known["site"]), value=float(known["value"]), deadline=int(known["deadline"])),
        forecast=FutureForecast(
            site=int(forecast["site"]), probability=float(forecast["probability"]), value=float(forecast["value"]),
            release=int(forecast["release"]), deadline=int(forecast["deadline"]), realized=bool(forecast["realized"]),
        ),
        outage_site=int(outage["site"]), outage_start=int(outage["start"]), outage_duration=int(outage["duration"]),
    )


def _make_scenario(family: str, rng: np.random.Generator, index: int) -> P41V2Scenario:
    if family == "commit_now_like":
        known_value = float(rng.integers(6, 9))
        return P41V2Scenario(
            f"commit_now_{index}", KnownRequest(0, known_value, int(rng.integers(5, 7))),
            FutureForecast(1, float(rng.choice((0.75, 0.85, 0.95))), float(rng.integers(10, 13)), 2, 8, False),
            outage_site=1, outage_start=7, outage_duration=1,
        )
    if family == "defer_for_value_like":
        return P41V2Scenario(
            f"defer_value_{index}", KnownRequest(0, float(rng.integers(3, 6)), int(rng.integers(5, 7))),
            FutureForecast(1, float(rng.choice((0.75, 0.85, 0.95))), float(rng.integers(10, 13)), 2, 8, True),
            outage_site=0, outage_start=7, outage_duration=1,
        )
    if family == "reroute_before_outage_like":
        return P41V2Scenario(
            f"reroute_{index}", KnownRequest(0, float(rng.integers(7, 10)), int(rng.integers(6, 7))),
            FutureForecast(1, float(rng.choice((0.55, 0.65, 0.75))), float(rng.integers(11, 14)), 2, 8, True),
            outage_site=0, outage_start=1, outage_duration=int(rng.choice((3, 4))),
        )
    raise ValueError(f"unknown P41 family: {family}")


def make_tape(seed: int, episodes: int) -> dict:
    if episodes <= 0 or episodes % len(FAMILIES) != 0:
        raise ValueError("episode count must be a positive multiple of the three P41 families")
    rng = np.random.default_rng(seed)
    labels = list(FAMILIES) * (episodes // len(FAMILIES))
    rng.shuffle(labels)
    return {
        "protocol": "P41-V2-SCENARIO-TAPE-V1",
        "seed": int(seed),
        "episodes": [scenario_to_dict(_make_scenario(label, rng, index), label) for index, label in enumerate(labels)],
        "families": list(FAMILIES),
        "actor_future_realization_access": False,
    }


def _write_tape(path: Path, seed: int, episodes: int) -> str:
    payload = make_tape(seed, episodes)
    encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to create tapes without --execute")
    out = args.output_root
    out.mkdir(parents=True, exist_ok=False)
    specs = (("training", 951000, 960), ("validation", 951100, 240), ("final", 951200, 360))
    hashes = {name: _write_tape(out / f"{name}_tape.json", seed, episodes) for name, seed, episodes in specs}
    manifest = {"protocol": "P41-V2-TAPE-MANIFEST-V1", "hashes": hashes, "training_started": False}
    (out / "tape_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
