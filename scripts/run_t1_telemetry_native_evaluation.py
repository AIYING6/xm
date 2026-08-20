"""Evaluate completed T1 reference checkpoints through the raw T0 evidence path."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.create_t1_telemetry_native_tape import EPISODES, TAPE_START  # noqa: E402
from scripts.run_t1_telemetry_native_single import ENVIRONMENT_STEPS, SEEDS  # noqa: E402
from scripts.telemetry_native_t0 import FailureScenario  # noqa: E402
from scripts.telemetry_native_t1 import write_checkpoint_evidence_bundle  # noqa: E402


PROTOCOL = "T1-TELEMETRY-NATIVE-FINAL-EVALUATION-V1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def plans_from_tape(tape: dict) -> list[tuple[int, FailureScenario]]:
    result = []
    for condition in tape["conditions"]:
        scenario = FailureScenario(
            str(condition["name"]), int(condition["failed_blue_agent"]),
            int(condition["start_step"]), int(condition["duration_steps"]),
        )
        result.extend((int(episode_id), scenario) for episode_id in tape["episode_ids"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    tape = json.loads((args.output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + EPISODES)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid frozen T1 tape")
    evaluation_root = args.output_root / "evaluations" / "final_1m"
    if evaluation_root.exists() and any(evaluation_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite T1 final evaluation: {evaluation_root}")
    plans = plans_from_tape(tape)
    entries = []
    for completed, seed in enumerate(SEEDS, start=1):
        run_dir = args.output_root / "runs" / "utr_sg" / f"seed{seed}"
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        required = {
            "status": "completed", "parameter_count": 116728, "graph_encoder": "single",
            "actor_gradient_mode": "utr", "environment_steps": ENVIRONMENT_STEPS,
            "from_scratch": True, "strict_continuous": True, "final_checkpoint_only": True,
            "canonical_seeds_used": False, "held_out_seeds_used": False,
        }
        if any(manifest.get(key) != value for key, value in required.items()) or manifest.get("tape_hash") != tape["tape_hash"]:
            raise RuntimeError(f"T1 training-contract violation: {run_dir}")
        checkpoint = run_dir / "actor_critic_latest.pt"
        if not checkpoint.exists() or sha256(checkpoint) != manifest.get("final_checkpoint_sha256"):
            raise RuntimeError(f"invalid final checkpoint: {run_dir}")
        bundle_root = evaluation_root / "utr_sg" / f"seed{seed}"
        bundle = write_checkpoint_evidence_bundle(bundle_root, checkpoint, construction_seed=seed, plans=plans, device=args.device)
        entries.append({"seed": seed, "checkpoint_sha256": manifest["final_checkpoint_sha256"], "bundle_manifest": bundle})
        print(f"T1 evaluation progress {completed}/{len(SEEDS)} ({100 * completed / len(SEEDS):.2f}%)", flush=True)
    evaluation_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "protocol": PROTOCOL, "status": "completed", "method": "UTR-SG-MAPPO", "tape_hash": tape["tape_hash"],
        "episodes_per_seed": len(plans), "raw_telemetry_source": "per-seed raw_step_telemetry.jsonl",
        "historical_aggregate_reuse": False, "device": args.device, "entries": entries,
    }
    (evaluation_root / "evaluation_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "seeds": len(entries), "evaluation_root": str(evaluation_root)}, indent=2))


if __name__ == "__main__":
    main()
