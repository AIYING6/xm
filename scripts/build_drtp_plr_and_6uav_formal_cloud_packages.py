"""Create two source-only, separately launchable formal cloud packages."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LINES = {
    "plr": {"name": "DRTP_PLR_EXTERNAL_FORMAL_10M", "stage": "DRTP_PLR_EXTERNAL_FORMAL", "paths": ("algorithms", "envs", "configs/drtp_plr_external_formal_freeze_20260906.json", "scripts", "requirements.txt", "README.md"), "readme": "Run preflight first. Formal training is a separate authorization: UTR/Original-DRTP/PLR-style × five fresh seeds, then one fixed endpoint evaluation. No adaptive algorithm change is allowed."},
    "6uav": {"name": "DRTP_6UAV_CROSS_SCALE_FORMAL_10M", "stage": "DRTP_6UAV_CROSS_SCALE_FORMAL", "paths": ("algorithms", "envs", "configs/drtp_6uav_cross_scale_formal_freeze_20260906.json", "scripts", "requirements.txt", "README.md"), "readme": "Run preflight first. Formal training is a separate authorization: six-UAV UTR/Original-DRTP × five fresh seeds, then one fixed endpoint evaluation. No adaptive algorithm change is allowed."},
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def build(line: str, commit: str) -> Path:
    spec = LINES[line]; output = ROOT / "output" / f"{spec['name']}.zip"; output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drtp_formal_") as tmp:
        tmp_path, source, stage = Path(tmp), Path(tmp) / "source.zip", Path(tmp) / spec["stage"]
        subprocess.run(["git", "archive", "--format=zip", f"--output={source}", commit, "--", *spec["paths"]], cwd=ROOT, check=True)
        stage.mkdir()
        with zipfile.ZipFile(source) as archive: archive.extractall(stage)
        (stage / "CLOUD_PROVENANCE.json").write_text(json.dumps({"commit": commit, "line": line, "source_only": True, "training_started": False, "automatic_algorithm_revision": False}, indent=2) + "\n", encoding="utf-8")
        (stage / "README_AUTODL.txt").write_text(spec["readme"] + "\n", encoding="utf-8")
        if output.exists(): output.unlink()
        shutil.make_archive(str(output.with_suffix("")), "zip", tmp_path, stage.name)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest(output)}  {output.name}\n", encoding="utf-8")
    return output


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    outputs = [build(line, commit) for line in LINES]
    print(json.dumps({"commit": commit, "packages": [str(path) for path in outputs]}, indent=2))


if __name__ == "__main__": main()
