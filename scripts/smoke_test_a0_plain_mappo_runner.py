"""One-update integration smoke for the A0 plain MAPPO pilot."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_a0_plain_mappo_pilot import train


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="a0_plain_mappo_"))
    try:
        oc_root = root / "oc"
        oc_root.mkdir()
        train(seed=301, updates=1, parallel_envs=3, out=oc_root, arm="oc")
        assert (oc_root / "endpoint.pt").is_file()
        assert (oc_root / "train_log.csv").is_file()
        header = (oc_root / "train_log.csv").read_text(encoding="utf-8").splitlines()[0]
        assert "credit_positive_fraction" in header

        plain_root, zero_root = root / "plain", root / "zero"
        plain_root.mkdir(); zero_root.mkdir()
        train(seed=302, updates=1, parallel_envs=3, out=plain_root, arm="plain")
        train(seed=302, updates=1, parallel_envs=3, out=zero_root, arm="zero_oc")
        plain = torch.load(plain_root / "endpoint.pt", map_location="cpu", weights_only=True)
        zero = torch.load(zero_root / "endpoint.pt", map_location="cpu", weights_only=True)
        assert all(torch.equal(plain["state_dict"][key], zero["state_dict"][key]) for key in plain["state_dict"])
    finally:
        shutil.rmtree(root)
    print("A0_PLAIN_MAPPO_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
