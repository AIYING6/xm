"""Evaluate the four mature specialists and two MSR Mixed-50 checkpoints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402


PROTOCOL = "PHASE-MSR-UNIFIED-EVALUATION-V1"
TAPE_START = 380000
EPISODES = 100
SEEDS = (1801, 1802)
GROUPS = ("fl_nominal_expert", "fl_f0_expert", "mixed50_sg")


def evaluate_checkpoint(group: str, seed: int, checkpoint: Path, output_root: Path,
                        source_manifest: dict, tape: dict) -> dict:
    out_dir = output_root / "evaluations" / group / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    fl.PROTOCOL = PROTOCOL
    fl.TAPE_START = TAPE_START
    fl.EPISODES = EPISODES
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    fl.evaluate(agent, group, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "completed", "group": group, "seed": seed,
        "checkpoint": str(checkpoint), "checkpoint_sha256": fl.sha256(checkpoint),
        "source_protocol": source_manifest.get("protocol"),
        "source_training_condition": source_manifest.get("training_condition"),
        "tape_start": TAPE_START, "episodes_per_condition": EPISODES,
        "tape_hash": tape["tape_hash"], "raw_rows": 2 * EPISODES, "paired_rows": EPISODES,
    }
    (out_dir / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--specialist-root", type=Path, required=True)
    args = parser.parse_args()
    tape = json.loads((args.output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape["episode_ids"] != list(range(TAPE_START, TAPE_START + EPISODES)):
        raise RuntimeError("MSR tape is not the frozen 380000-380099 tape")
    manifests = []
    for group in GROUPS:
        for seed in SEEDS:
            if group == "mixed50_sg":
                source_dir = args.output_root / "runs" / group / f"seed{seed}"
                source_manifest = json.loads((source_dir / "run_manifest.json").read_text(encoding="utf-8"))
            else:
                source_dir = args.specialist_root / group / f"seed{seed}"
                source_manifest = json.loads((source_dir / "run_manifest.json").read_text(encoding="utf-8"))
            if source_manifest.get("status") != "completed":
                raise RuntimeError(f"incomplete source checkpoint: {source_dir}")
            checkpoint = source_dir / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            expected = source_manifest.get("checkpoint_sha256")
            observed = fl.sha256(checkpoint)
            if expected and expected != observed:
                raise RuntimeError(f"checkpoint hash mismatch: {checkpoint}")
            manifests.append(evaluate_checkpoint(group, seed, checkpoint, args.output_root, source_manifest, tape))
    (args.output_root / "unified_evaluation_manifest.json").write_text(
        json.dumps({"protocol": PROTOCOL, "status": "completed", "evaluations": manifests}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", "evaluations": len(manifests)}, indent=2))


if __name__ == "__main__":
    main()
