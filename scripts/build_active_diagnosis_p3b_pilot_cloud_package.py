"""Build the self-contained AutoDL package for the conditionally gated P3B pilot."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "ACTIVE_DIAGNOSIS_P3B_STAGED_PILOT_1M_V3"
FILES = (
    "algorithms/__init__.py",
    "algorithms/redundant_topology_sg_mappo.py",
    "algorithms/active_diagnosis/__init__.py",
    "algorithms/active_diagnosis/decision_relevant_probe.py",
    "algorithms/active_diagnosis/pilot_gate_adapter.py",
    "algorithms/active_diagnosis/pilot_runner.py",
    "algorithms/active_diagnosis/recurrent_sg_mappo.py",
    "algorithms/active_diagnosis/task_value_estimator.py",
    "configs/active_diagnosis_p3b_pilot_freeze.json",
    "envs/__init__.py",
    "envs/active_diagnosis_semantic_env.py",
    "envs/active_diagnosis_trainable_uav_env.py",
    "envs/uav_intercept_3d_env.py",
    "envs/uav_pursuit_env.py",
    "scripts/audit_active_diagnosis_p3b_integrated_runner.py",
    "scripts/audit_active_diagnosis_p3b_remaining_components.py",
    "scripts/launch_active_diagnosis_p3b_pilot_autodl.sh",
    "scripts/run_active_diagnosis_p3b_pilot.py",
)


README = """# Active Diagnosis P3B staged pilot

The workflow first enforces the real-environment integrated-runner audit, then
runs three common 0.25M prefixes, a 64-episode factorial task-value calibration
per seed, and applies a hard calibration quality stop. The nine
arm-specific 0.75M branches and fixed endpoint evaluation start only if every
seed passes calibration. A calibration STOP is a scientific stop, not a runner
failure. No return-based checkpoint selection or automatic algorithm revision
is implemented. The task-value gate consumes only the relay actor's local
observation; centralized critic state and latent failure truth are forbidden.
"""


def main() -> None:
    destination = ROOT / f"{PACKAGE_NAME}.zip"
    if destination.exists():
        raise FileExistsError(destination)
    for relative in FILES:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(relative)
    with tempfile.TemporaryDirectory(prefix="active_diag_p3b_") as temporary:
        package_root = Path(temporary) / PACKAGE_NAME
        for relative in FILES:
            target = package_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        (package_root / "README.md").write_text(README, encoding="utf-8")
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(package_root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(Path(temporary)))
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="ascii"
    )
    print(destination)
    print(digest)


if __name__ == "__main__":
    main()
