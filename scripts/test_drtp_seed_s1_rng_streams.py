"""Regression tests for the opt-in DRTP-SEED-S1 RNG decomposition."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.ri_gmappo.rng_streams import RNGSeedTuple, RNGStreams


def main() -> None:
    base = RNGStreams.from_master(1902)
    altered = RNGStreams(
        RNGSeedTuple(
            init_seed=base.seeds.init_seed,
            env_seed=base.seeds.env_seed,
            action_seed=base.seeds.action_seed,
            minibatch_seed=base.seeds.minibatch_seed,
            topology_seed=base.seeds.topology_seed + 1,
            eval_seed=base.seeds.eval_seed,
        )
    )
    base_probe = base.probe()
    altered_probe = altered.probe()
    for stream in ("init", "env", "action", "minibatch", "eval"):
        assert base_probe[stream] == altered_probe[stream], stream
    assert base_probe["topology"] != altered_probe["topology"]
    manifest = base.manifest()
    assert manifest["format"] == "drtp_seed_s1_rng_tuple_v1"
    assert set(manifest["streams"]) == {"init", "env", "action", "minibatch", "topology", "eval"}
    out = Path("artifacts/drtp_seed_s1")
    out.mkdir(parents=True, exist_ok=True)
    (out / "rng_stream_regression.json").write_text(
        json.dumps({"status": "PASS", "single_stream_isolation": True, "manifest": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    print("DRTP-SEED-S1 RNG stream isolation: PASS")


if __name__ == "__main__":
    main()
