"""Zero-training integrity audit for the frozen B1 branch experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

# Cloud checkpoints produced under NumPy 2 use the ``numpy._core`` pickle
# module path.  The local cac environment is NumPy 1.x; this compatibility
# alias changes no tensor or RNG data and is inert under NumPy 2.
sys.modules.setdefault("numpy._core", np.core)
sys.modules.setdefault("numpy._core.multiarray", np.core.multiarray)


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from scripts.run_drtp_b1_update_sensitivity_branch import ARMS, COHORTS, source_config  # noqa: E402


FREEZE = ROOT / "configs" / "drtp_b1_update_sensitivity_freeze.json"
TAPE = ROOT / "configs" / "drtp_b1_update_sensitivity_tape.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-root", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    asset_manifest = json.loads((args.assets_root / "B1_ASSET_MANIFEST.json").read_text(encoding="utf-8"))
    if freeze["status"] != "PREPARED_NOT_AUTHORIZED" or freeze["automatic_training_authorized"] is not False:
        raise RuntimeError("invalid B1 authorization boundary")
    if tape["canonical"] is not False or tape["checkpoint_promotion"] is not False:
        raise RuntimeError("invalid B1 development tape")
    if asset_manifest.get("runtime_checkpoints") != 40 or asset_manifest.get("source_checkpoint") != "500k":
        raise RuntimeError("invalid B1 slim asset manifest")
    checks = []
    for cohort, seeds in COHORTS.items():
        for arm in ARMS:
            for seed in seeds:
                source = args.assets_root / cohort / arm / f"seed{seed}"
                manifest_path = source / "run_manifest.json"
                runtime_path = source / "actor_critic_runtime_state_milestone_500k.pt"
                cfg = source_config(manifest_path)
                payload = torch.load(runtime_path, map_location="cpu", weights_only=False)
                expected_mode = "utr" if arm == "utr_sg" else "drtp"
                sampler = payload.get("drtp_sampler_state") or {}
                result = {
                    "cohort": cohort, "arm": arm, "seed": seed,
                    "update_1953": int(payload.get("update", -1)) == 1953,
                    "sampler_mode": sampler.get("mode") == expected_mode,
                    "sampler_seed": int(sampler.get("seed", -1)) == seed,
                    "model_state": isinstance(payload.get("model_state"), dict),
                    "optimizer_state": isinstance(payload.get("optimizer_state"), dict),
                    "environment_count": len(payload.get("environment_states", [])) == 4,
                    "config_arm": cfg.drtp_sampler_mode == expected_mode,
                    "config_graph_encoder": cfg.graph_encoder == "single",
                    "config_hidden_dim": int(cfg.hidden_dim) == 115,
                    "runtime_sha256": sha256(runtime_path),
                }
                if not all(value for key, value in result.items() if key not in {"cohort", "arm", "seed", "runtime_sha256"}):
                    raise RuntimeError(f"B1 source checkpoint failed audit: {result}")
                checks.append(result)
    report = {
        "status": "B1_TECHNICAL_PREFLIGHT_PASS",
        "source_checkpoints": len(checks),
        "freeze_sha256": sha256(FREEZE),
        "tape_sha256": sha256(TAPE),
        "assets_manifest_sha256": sha256(args.assets_root / "B1_ASSET_MANIFEST.json"),
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
        "training_started": False,
        "algorithm_modified": False,
        "mainline_a_modified": False,
        "checks": checks,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
