"""NP1B read-only diagnosis of responsibility-reallocation necessity."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_np1_dynamic_capability_calibration import (  # noqa: E402
    HORIZON,
    OUT,
    PROTOCOL,
    SEEDS,
    TRANSITION_STEP,
    DynamicCapabilityAdapter,
    config,
    scripted_guidance,
)


def evidence_snapshot(env: DynamicCapabilityAdapter) -> dict[str, object]:
    rows = []
    for i in range(env.config.num_blue):
        packet_sources = []
        for sender, packet in env.sender_packet_cache[i].items():
            if float(packet.get("validity", 0.0)) > 0.5 and float(packet.get("target_confidence", 0.0)) > 0.0:
                packet_sources.append({
                    "sender": int(sender),
                    "confidence": float(packet.get("target_confidence", 0.0)),
                    "generation_step": int(packet.get("target_generation_step", -1)),
                })
        rows.append({
            "agent": i,
            "detected": float(env.detected_by[i]),
            "has_target_information": bool(env._has_target_information(i)),
            "cache_valid": bool(env.target_cache_valid[i] > 0.5),
            "cache_fresh": bool(env._has_fresh_target_cache(i)),
            "cache_age": float(env._local_target_cache_age(i)),
            "cache_source": int(env.target_cache_source[i]),
            "cache_confidence": float(env.target_cache_confidence[i]),
            "status_target_packets": packet_sources,
        })
    return {"step": int(env.step_count), "agents": rows}


def trace(seed: int, mode: str) -> dict[str, object]:
    env = DynamicCapabilityAdapter(config(seed), transition_step=TRANSITION_STEP)
    obs, _, _ = env.reset()
    pre_actions: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    before = None
    after = None
    info = {"target_neutralized": 0.0, "collision": 0.0, "constraint_violation": 0.0, "target_escape": 0.0}
    while not env.done and env.step_count < HORIZON:
        if mode == "fixed_responsibility" and env.step_count >= TRANSITION_STEP and pre_actions:
            action = pre_actions[-1].copy()
        else:
            action = scripted_guidance(env, obs)
        if env.step_count < TRANSITION_STEP:
            pre_actions.append(action.copy())
        if env.step_count == TRANSITION_STEP - 1:
            before = evidence_snapshot(env)
        obs, _, _, _, dones, info = env.step_guidance(action)
        records.append({
            "step": int(env.step_count),
            "action": action.tolist(),
            "blue_pos": env.blue_pos.tolist(),
            "target_pos": env.red_pos[0].tolist(),
            "evidence": evidence_snapshot(env),
        })
        if env.step_count == TRANSITION_STEP:
            after = records[-1]["evidence"]
        if bool(dones[0, 0]):
            break
    attacker_id = next(i for i, t in enumerate(env.config.blue_types) if t.role == 2)
    post = [r for r in records if int(r["step"]) >= TRANSITION_STEP]
    return {
        "seed": seed,
        "mode": mode,
        "outcome": "NEUTRALIZED" if info.get("target_neutralized", 0.0) > 0.5 else (
            "COLLISION" if info.get("collision", 0.0) > 0.5 else (
                "CONSTRAINT_FAILURE" if info.get("constraint_violation", 0.0) > 0.5 else (
                    "TARGET_ESCAPE" if info.get("target_escape", 0.0) > 0.5 else "TIMEOUT"
                )
            )
        ),
        "steps": int(env.step_count),
        "before": before,
        "after": after,
        "records": records,
        "post_loss_attacker_information_steps": sum(
            bool(r["evidence"]["agents"][attacker_id]["has_target_information"]) for r in post
        ),
        "post_loss_relay_information_steps": sum(
            bool(r["evidence"]["agents"][1]["has_target_information"]) for r in post
        ),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixed = [trace(seed, "fixed_responsibility") for seed in SEEDS]
    realloc = [trace(seed, "reallocated") for seed in SEEDS]
    transition_valid = all(
        r["before"] is not None
        and r["after"] is not None
        and r["before"]["agents"][0]["has_target_information"]
        and not r["after"]["agents"][0]["has_target_information"]
        for r in fixed
    )
    fixed_success = sum(r["outcome"] == "NEUTRALIZED" for r in fixed)
    realloc_success = sum(r["outcome"] == "NEUTRALIZED" for r in realloc)
    if transition_valid and fixed_success < len(fixed) and realloc_success > fixed_success:
        verdict = "NP1_PASS__RESPONSIBILITY_REALLOCATION_PROBLEM_IDENTIFIED__READY_FOR_METHOD_DESIGN"
    elif transition_valid:
        verdict = "NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR"
    else:
        verdict = "NP1_NO_GO__DYNAMIC_CAPABILITY_PROBLEM_NOT_IDENTIFIABLE"
    report = {
        "protocol_version": f"{PROTOCOL}_NP1B",
        "training": False,
        "transition_step": TRANSITION_STEP,
        "horizon": HORIZON,
        "fixed_responsibility": fixed,
        "reallocated": realloc,
        "transition_valid": transition_valid,
        "fixed_responsibility_neutralized": fixed_success,
        "reallocated_neutralized": realloc_success,
        "verdict": verdict,
    }
    (OUT / "NP1B_RESPONSIBILITY_NECESSITY_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "protocol_version": f"{PROTOCOL}_NP1B",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "seeds": list(SEEDS),
        "uses_training": False,
        "uses_new_method": False,
    }
    (OUT / "NP1B_RESPONSIBILITY_NECESSITY_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verdict}: fixed={fixed_success}/{len(fixed)} reallocated={realloc_success}/{len(realloc)} transition_valid={transition_valid}")


if __name__ == "__main__":
    main()
