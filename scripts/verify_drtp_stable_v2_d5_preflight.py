"""Zero-training preflight for the frozen D5 DRTP-KLB pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_stable_v2_d5_single as pilot  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing preflight overwrite: {args.output}")
    tape = json.loads(pilot.TAPE.read_text(encoding="utf-8"))
    freeze_path = ROOT / "configs" / "drtp_stable_v2_d5_pilot_freeze.json"
    seed_path = ROOT / "docs" / "drtp_stable_v2_d5_20260829" / "STABLE_V2_D5_SEED_PROVENANCE.json"
    d4_path = ROOT / "docs" / "drtp_stable_v2_d4_20260829" / "STABLE_V2_D4_TECHNICAL_AUDIT.json"
    source = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))
    d4 = json.loads(d4_path.read_text(encoding="utf-8"))
    tape_payload = dict(tape)
    claimed_hash = tape_payload.pop("tape_hash", None)
    recomputed_hash = hashlib.sha256(
        json.dumps(tape_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    checks = {
        "d4_technical_pass": d4.get("status") == "D4_TECHNICAL_PASS",
        "d4_source_hash_unchanged": sha256(source) == d4.get("sha256", {}).get("algorithms/ri_gmappo/simple_ri_gmappo.py"),
        "seed_provenance_clean": seeds.get("status") == "CLEAN" and seeds.get("candidate_seeds") == list(pilot.SEEDS),
        "tape_hash_frozen": tape.get("tape_hash") == freeze.get("tape_hash"),
        "tape_hash_recomputed": claimed_hash == recomputed_hash,
        "tape_namespace_exact": tape.get("episode_ids") == list(range(560000, 560100)),
        "conditions_exact": [item["name"] for item in tape.get("conditions", [])]
        == ["nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"],
        "budget_exact": pilot.UPDATES * pilot.NUM_ENVS * pilot.ROLLOUT_STEPS == 499968,
        "milestones_exact": pilot.MILESTONES == {976: "250k", 1953: "500k"},
        "candidate_exact": pilot.ARMS["drtp_klb_sg"] == {
            "sampler": "drtp", "guard": "post_step_actor_backtrack", "target_kl": 0.02
        },
        "epsilon_exact": freeze.get("epsilon_J") == 7.874919837916801,
        "no_training_or_continuation": freeze.get("training_started") is False
        and freeze.get("automatic_continuation") is False,
        "mainline_a_untouched": freeze.get("mainline_a_modified") is False,
    }
    trajectories = {}
    for arm in pilot.ARMS:
        for seed in pilot.SEEDS:
            cfg = pilot.training_config(arm, seed, ROOT / "_d5_preflight_no_output")
            expected = pilot.ARMS[arm]
            valid = (
                cfg.updates == 1953
                and cfg.drtp_sampler_mode == expected["sampler"]
                and cfg.drtp_sampler_seed == seed
                and cfg.policy_update_guard_mode == expected["guard"]
                and cfg.target_kl == expected["target_kl"]
                and cfg.evaluation_enabled is False
                and cfg.runtime_state_checkpointing is True
                and cfg.rollout_steps * cfg.num_envs == cfg.minibatch_graphs == 256
            )
            checks[f"trajectory_{arm}_seed{seed}"] = valid
            trajectories[f"{arm}/seed{seed}"] = {
                "sampler": cfg.drtp_sampler_mode,
                "guard": cfg.policy_update_guard_mode,
                "target_kl": cfg.target_kl,
                "updates": cfg.updates,
            }
    status = "D5_READY_FOR_CLOUD_AUTHORIZATION" if all(checks.values()) else "D5_NOT_READY"
    payload = {
        "protocol": "DRTP-STABLE-V2-D5-PREFLIGHT-V1",
        "status": status,
        "checks": checks,
        "trajectories": trajectories,
        "source_sha256": sha256(source),
        "tape_sha256": sha256(pilot.TAPE),
        "freeze_sha256": sha256(freeze_path),
        "seed_audit_sha256": sha256(seed_path),
        "local_training_started": False,
        "environment_created": False,
        "pilot_training_authorized": False,
        "mainline_a_modified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2); handle.write("\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if status == "D5_READY_FOR_CLOUD_AUTHORIZATION" else 1)


if __name__ == "__main__":
    main()
