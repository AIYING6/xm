"""Run the four-method Phase 3A engineering-only smoke test.

The smoke uses one tiny update and one evaluation episode per method. It is
never canonical evidence and cannot be used for model selection.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "canonical_v2" / "smoke"
REQUIRED = {
    "pre_failure_chain_established",
    "chain_lost_after_failure",
    "t_failure",
    "t_loss",
    "post_failure_chain_recovered_after_loss",
    "t_recovery",
    "delta_t_loss_to_recovery",
    "post_failure_chain_first_established",
    "event",
    "censor_time",
}

METHODS = {
    "full": {"method": "EA-RG-MAPPO-S", "graph_encoder": "multi_relation", "residual": "1.0"},
    "mappo": {"method": "MAPPO", "graph_encoder": "no_graph", "residual": "1.0"},
    "single_graph": {"method": "Single-Graph", "graph_encoder": "single", "residual": "1.0"},
    "no_union_residual": {
        "method": "EA-RG-MAPPO-S-no-union-residual",
        "graph_encoder": "multi_relation",
        "residual": "0.0",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def common_train(spec: dict[str, str], seed: int, out_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-B",
        "scripts/train_ri_gmappo.py",
        "--seed", str(seed),
        "--env-name", "3d_intercept",
        "--target-policy", "straight",
        "--strict-target-sensing",
        "--agent-target-info-bottleneck",
        "--communication-dropout-prob", "0.30",
        "--message-delay-steps", "2",
        "--failed-blue-agent", "1",
        "--node-failure-start-step", "40",
        "--node-failure-duration-steps", "80",
        "--graph-encoder", spec["graph_encoder"],
        "--multi-relation-global-residual-weight", spec["residual"],
        "--num-envs", "1",
        "--rollout-steps", "4",
        "--updates", "1",
        "--eval-interval", "1",
        "--eval-episodes", "1",
        "--save-interval", "1",
        "--save-snapshots",
        "--hidden-dim", "64",
        "--device", "cpu",
        "--out-dir", str(out_dir),
    ]


def evaluate(spec: dict[str, str], seed: int, checkpoint: Path, out_csv: Path) -> None:
    command = [
        sys.executable,
        "-B",
        "scripts/evaluate_ri_gmappo_3d.py",
        "--method", spec["method"],
        "--checkpoint", str(checkpoint),
        "--episodes", "1",
        "--base-seed", str(130000 + seed),
        "--target-policy", "straight",
        "--strict-target-sensing",
        "--agent-target-info-bottleneck",
        "--communication-dropout-prob", "0.30",
        "--message-delay-steps", "2",
        "--failed-blue-agent", "1",
        "--node-failure-start-step", "40",
        "--node-failure-duration-steps", "80",
        "--graph-encoder", spec["graph_encoder"],
        "--multi-relation-global-residual-weight", spec["residual"],
        "--device", "cpu",
        "--out-csv", str(out_csv),
        "--summary-md", str(out_csv.with_suffix(".md")),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str | int]] = []
    for key, spec in METHODS.items():
        run_dir = OUT / key / "seed0"
        run_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(common_train(spec, 0, run_dir), cwd=ROOT, check=True)
        checkpoint = run_dir / "actor_critic_latest.pt"
        if not checkpoint.exists():
            raise RuntimeError(f"missing smoke checkpoint: {checkpoint}")
        out_csv = run_dir / "raw_episode_metrics.csv"
        evaluate(spec, 0, checkpoint, out_csv)
        with out_csv.open("r", encoding="utf-8", newline="") as f:
            fields = set(csv.DictReader(f).fieldnames or ())
        missing = sorted(REQUIRED - fields)
        if missing:
            raise RuntimeError(f"{spec['method']} missing v2 fields: {missing}")
        manifest.append({
            "artifact_class": "ENGINEERING_SMOKE_TEST_ONLY",
            "method_key": key,
            "method": spec["method"],
            "seed": 0,
            "checkpoint": str(checkpoint.relative_to(ROOT)),
            "checkpoint_sha256": sha256(checkpoint),
            "raw_episode_csv": str(out_csv.relative_to(ROOT)),
            "raw_episode_sha256": sha256(out_csv),
            "graph_encoder": spec["graph_encoder"],
            "residual_weight": spec["residual"],
        })
    manifest_path = OUT / "smoke_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
