"""Build a provenance manifest from frozen config and historical episode metadata."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs/paper"
RAW = ROOT / "archival/provenance/legacy_e02a753/results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/test_episode_metrics.csv"
OUT = ROOT / "archival/provenance/baseline_identity_manifest_v2.csv"

CONFIGS = {
    "multi_relation": ("EA-RG-MAPPO", "ea_rg_mappo.yaml"),
    "no_graph": ("No-Graph (internal ablation)", "mappo.yaml"),
    "single": ("Single-Graph GAT-MAPPO", "single_graph.yaml"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with RAW.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    unique = {(row["graph_encoder"], row["train_seed"], row["checkpoint_update"]) for row in rows}
    output = []
    for encoder, seed, update in sorted(unique):
        canonical, config_name = CONFIGS.get(encoder, (encoder, ""))
        config_path = CONFIG_DIR / config_name
        matching = next(row for row in rows if (row["graph_encoder"], row["train_seed"], row["checkpoint_update"]) == (encoder, seed, update))
        output.append(
            {
                "canonical_method_name": canonical,
                "architecture_family": "RI-MAPPO" if encoder == "no_graph" else "graph-MAPPO",
                "graph_encoder": encoder,
                "config": f"configs/paper/{config_name}",
                "config_sha256": sha256(config_path) if config_path.exists() else "MISSING",
                "seed": seed,
                "checkpoint_update": update,
                "checkpoint_path_as_recorded": matching.get("checkpoint", ""),
                "checkpoint_sha256": "MISSING_CHECKPOINT_BYTES",
                "training_budget": "formal protocol e02a753; update 60; see archived protocol.md",
                "bc_initialization": "true per paper config; historical run manifest required for byte-level confirmation",
                "validation_selection": "fixed_update60_selected_checkpoints.csv / validation artifacts",
                "evaluation_protocol": "archival e02a753 formal test; not canonical",
                "raw_episode_source": "archival/provenance/legacy_e02a753/.../merged/test_episode_metrics.csv",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(f"wrote {len(output)} identity rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
