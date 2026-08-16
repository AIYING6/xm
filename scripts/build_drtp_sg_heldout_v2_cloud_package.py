"""Package the separately authorized DRTP held-out confirmation v2 controller."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {output}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="drtp_heldout_v2_cloud_") as temporary:
        stage, archive = Path(temporary) / "EA_RG_MAPPO_DRTP_HELDOUT_V2", Path(temporary) / "source.zip"
        stage.mkdir()
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit], cwd=root, check=True)
        with zipfile.ZipFile(archive) as source:
            source.extractall(stage)
        provenance = {
            "protocol": "DRTP-SG-MAPPO-HELDOUT-CONFIRMATION-V2-CLOUD-PACKAGE-V1", "commit": commit, "branch": branch,
            "authorized_arms": ["utr_sg", "drtp_sg"], "held_out_seeds": [2001, 2002, 2003],
            "from_scratch_strict_continuous_budget": "39063 updates / 10000128 steps", "runtime_persistence": "enabled from update zero",
            "heldout_tape_generated_on_launch": "430000-430099", "canonical_prohibited": True,
            "formal_five_seed_ablation_and_follow_on_ood_prohibited": True,
        }
        (stage / "DRTP_HELDOUT_V2_CLOUD_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in stage.rglob("*"):
                if path.is_file():
                    bundle.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"package": str(output), "sha256": sha256(output), "commit": commit, "branch": branch}, indent=2))


if __name__ == "__main__":
    main()
