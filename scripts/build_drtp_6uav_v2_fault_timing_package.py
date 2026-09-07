"""Build the source-only formal 6-UAV v2 cloud package.

The v2 package differs from the invalid v1 run only in the frozen fault onset
(step 3 rather than step 9), a fresh reserved five-seed cohort, and endpoint
telemetry that refuses to aggregate if a non-nominal fault was not injected.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "DRTP_6UAV_CROSS_SCALE_FORMAL_10M_V2_FAULTSTEP3"
STAGE = "DRTP_6UAV_CROSS_SCALE_FORMAL_V2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_exact(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"package patch anchor not found: {old!r}")
    return text.replace(old, new)


def patch_runner(stage: Path) -> None:
    path = stage / "scripts" / "run_drtp_6uav_cross_scale_formal.py"
    text = path.read_text(encoding="utf-8")
    text = replace_exact(text, 'PROTOCOL = "DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-V1"', 'PROTOCOL = "DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-V2-FAULTSTEP3"')
    text = replace_exact(text, 'FREEZE = ROOT / "configs/drtp_6uav_cross_scale_formal_freeze_20260906.json"', 'FREEZE = ROOT / "configs/drtp_6uav_cross_scale_formal_v2_faultstep3_freeze_20260907.json"')
    text = replace_exact(text, 'SEEDS = (69011, 69012, 69013, 69014, 69015)', 'SEEDS = (69021, 69022, 69023, 69024, 69025)\nFAULT_STEP = 3')
    text = replace_exact(text, 'if tuple(training["seeds"]) != SEEDS or training["environment_steps_per_trajectory"] != STEPS:', 'if tuple(training["seeds"]) != SEEDS or training["environment_steps_per_trajectory"] != STEPS or spec["condition_interface"]["failure_onset"] != FAULT_STEP:')
    anchor = 'EVALUATION_EPISODES = 100\n\n\ndef digest'
    helper = '''EVALUATION_EPISODES = 100


def maybe_fault_v2(env) -> None:
    """Inject the frozen in-mission fault and retain auditable event metadata."""
    if env._p2_group != "nominal" and env.step_count == FAULT_STEP:
        before = int(env.active_adjacency().sum())
        spec = fault_spec(env, env._p2_group)
        env.set_failure(spec["edges"], spec["nodes"])
        env._v2_fault_injected = True
        env._v2_fault_injected_at = int(env.step_count)
        env._v2_active_edges_before = before
        env._v2_active_edges_after = int(env.active_adjacency().sum())


def fault_telemetry(env) -> dict:
    return {
        "fault_step": FAULT_STEP,
        "fault_injected": int(bool(getattr(env, "_v2_fault_injected", False))),
        "fault_injected_at": getattr(env, "_v2_fault_injected_at", ""),
        "active_edges_before": getattr(env, "_v2_active_edges_before", int(env.active_adjacency().sum())),
        "active_edges_after": getattr(env, "_v2_active_edges_after", int(env.active_adjacency().sum())),
    }


def digest'''
    text = replace_exact(text, anchor, helper)
    text = text.replace('maybe_fault(env)', 'maybe_fault_v2(env)')
    old_return = 'return {"group": group, "score": total, "success": int(info["success"]), "collision": float(info["collision_pair"]), "timeout": int(info["timeout"])}'
    new_return = 'return {"group": group, "score": total, "success": int(info["success"]), "collision": float(info["collision_pair"]), "timeout": int(info["timeout"]), "episode_steps": int(env.step_count), **fault_telemetry(env)}'
    text = replace_exact(text, old_return, new_return)
    old_validation = 'raw = []\n    for file in files:\n        with file.open(newline="", encoding="utf-8") as handle: raw.extend(csv.DictReader(handle))'
    new_validation = '''raw = []
    for file in files:
        with file.open(newline="", encoding="utf-8") as handle: raw.extend(csv.DictReader(handle))
    faulty = [row for row in raw if row["group"] != "nominal"]
    if not faulty or not all(int(row["fault_injected"]) == 1 and int(row["fault_injected_at"]) == FAULT_STEP and int(row["active_edges_after"]) < int(row["active_edges_before"]) and int(row["episode_steps"]) > FAULT_STEP for row in faulty):
        raise RuntimeError("v2 endpoint integrity failure: a non-nominal episode lacked an effective step-3 fault")
    if not all(int(row["fault_injected"]) == 0 for row in raw if row["group"] == "nominal"):
        raise RuntimeError("v2 endpoint integrity failure: nominal episode was faulted")'''
    text = replace_exact(text, old_validation, new_validation)
    path.write_text(text, encoding="utf-8")


def patch_launcher(stage: Path) -> None:
    path = stage / "scripts" / "launch_drtp_6uav_cross_scale_formal_autodl.sh"
    text = path.read_text(encoding="utf-8")
    text = text.replace('drtp_6uav_cross_scale_formal', 'drtp_6uav_cross_scale_formal_v2_faultstep3')
    text = text.replace('69011 69012 69013 69014 69015', '69021 69022 69023 69024 69025')
    text = text.replace('run_drtp_6uav_cross_scale_formal.py', 'run_drtp_6uav_cross_scale_formal.py')
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_freeze(stage: Path) -> None:
    old = stage / "configs" / "drtp_6uav_cross_scale_formal_freeze_20260906.json"
    spec = json.loads(old.read_text(encoding="utf-8"))
    spec["protocol"] = "DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-FREEZE-V2-FAULTSTEP3"
    spec["status"] = "FROZEN_FOR_FORMAL_V2_NOT_LAUNCHED"
    spec["training"]["seeds"] = [69021, 69022, 69023, 69024, 69025]
    spec["training"]["reserved_independent_replication_seeds"] = []
    spec["condition_interface"]["failure_onset"] = 3
    spec["condition_interface"]["failure_onset_semantics"] = "after three nominal transitions and before transition four"
    spec["condition_interface"]["endpoint_fault_integrity_required"] = True
    old.unlink()
    (stage / "configs" / "drtp_6uav_cross_scale_formal_v2_faultstep3_freeze_20260907.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")


def patch_preflight(stage: Path) -> None:
    path = stage / "scripts" / "verify_drtp_plr_and_6uav_formal_preflight.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace('drtp_6uav_cross_scale_formal_freeze_20260906.json', 'drtp_6uav_cross_scale_formal_v2_faultstep3_freeze_20260907.json')
    old = '"six_uav_fresh_seed_ranges_disjoint": set(six["training"]["seeds"]).isdisjoint(six["training"]["reserved_independent_replication_seeds"]),'
    new = '"six_uav_v2_fresh_seeds_exact": tuple(six["training"]["seeds"]) == (69021, 69022, 69023, 69024, 69025),\n            "six_uav_v2_fault_step_exact": six["condition_interface"]["failure_onset"] == 3,'
    text = replace_exact(text, old, new)
    path.write_text(text, encoding="utf-8")


def build() -> Path:
    output = ROOT / "output" / f"{PACKAGE}.zip"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = ("algorithms", "envs", "scripts", "configs/drtp_6uav_cross_scale_formal_freeze_20260906.json", "requirements.txt", "README.md")
    with tempfile.TemporaryDirectory(prefix="drtp_6uav_v2_") as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / "source.zip"
        stage = tmp_path / STAGE
        subprocess.run(["git", "archive", "--format=zip", f"--output={archive}", commit, "--", *paths], cwd=ROOT, check=True)
        stage.mkdir()
        with zipfile.ZipFile(archive) as handle:
            handle.extractall(stage)
        patch_freeze(stage)
        patch_runner(stage)
        patch_launcher(stage)
        patch_preflight(stage)
        (stage / "CLOUD_PROVENANCE.json").write_text(json.dumps({"commit": commit, "protocol": "DRTP-6UAV-CROSS-SCALE-FORMAL-V2-FAULTSTEP3", "fault_step": 3, "seeds": [69021, 69022, 69023, 69024, 69025], "training_started": False}, indent=2) + "\n", encoding="utf-8")
        (stage / "README_AUTODL.txt").write_text("Formal 6-UAV v2. The only experimental change from the invalid v1 is in-mission fault onset step=3. Endpoint aggregation refuses any missing/non-effective non-nominal fault.\n", encoding="utf-8")
        if output.exists():
            output.unlink()
        shutil.make_archive(str(output.with_suffix("")), "zip", tmp_path, STAGE)
    output.with_suffix(".zip.sha256").write_text(f"{sha256(output)}  {output.name}\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(build())
