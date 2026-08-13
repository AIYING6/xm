"""Read-only S3 development-smoke provenance and decision audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def checkpoint_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--out-csv", type=Path, required=True)
    a = p.parse_args()
    rows = []
    expected_ids: dict[str, tuple[int, int]] = {}
    for method_dir in sorted(a.input_root.iterdir()):
        for seed_dir in sorted(method_dir.iterdir()):
            manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
            pairs = pd.read_csv(seed_dir / "paired_metrics.csv")
            ckpt = seed_dir / "actor_critic_latest.pt"
            rows.append(
                {
                    "method": method_dir.name,
                "seed": int(seed_dir.name.replace("seed", "", 1)),
                    "status": manifest["status"],
                    "environment_steps": manifest["environment_steps"],
                    "checkpoint_hash_matches_manifest": checkpoint_hash(ckpt) == manifest["checkpoint_sha256"],
                    "episodes": len(pairs),
                    "id_min": int(pairs.development_episode_id.min()),
                    "id_max": int(pairs.development_episode_id.max()),
                    "J_nominal": pairs.J_nominal.mean(),
                    "J_failure": pairs.J_failure.mean(),
                    "delta_J": pairs.delta_J.mean(),
                    "failure_exposure": pairs.failure_exposed.mean(),
                    "success_nominal": pairs.success_nominal.mean(),
                    "success_failure": pairs.success_failure.mean(),
                }
            )
        sample = pd.read_csv(sorted(method_dir.iterdir())[0] / "paired_metrics.csv")
        expected_ids[method_dir.name] = (int(sample.development_episode_id.min()), int(sample.development_episode_id.max()))
    out = pd.DataFrame(rows).sort_values(["method", "seed"])
    a.out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out_csv, index=False)
    print(out.to_csv(index=False))
    print(json.dumps({"method_episode_id_ranges": expected_ids}, indent=2))


if __name__ == "__main__":
    main()
