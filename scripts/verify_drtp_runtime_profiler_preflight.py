"""Verify that a runtime profiler would use the exact frozen DRTP source."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path


SOURCE_MAP = {
    "sampler": Path("algorithms/ri_gmappo/drtp_topology_sampler.py"),
    "learner": Path("algorithms/ri_gmappo/simple_ri_gmappo.py"),
    "environment": Path("envs/uav_intercept_3d_env.py"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_source_hashes(archive_path: Path) -> dict[str, str]:
    with tarfile.open(archive_path, "r:gz") as archive:
        candidates = [m for m in archive.getmembers() if m.isfile() and m.name.endswith("preflight/DRTP_STABILIZATION_FINAL_FREEZE.json")]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one freeze manifest, found {len(candidates)}")
        raw = archive.extractfile(candidates[0])
        if raw is None:
            raise RuntimeError("Cannot read freeze manifest")
        return json.loads(raw.read().decode("utf-8"))["source_sha256"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-archive", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    expected = frozen_source_hashes(args.final_archive)
    checks = {}
    for name, relative in SOURCE_MAP.items():
        path = args.source_root / relative
        actual = sha256(path) if path.is_file() else None
        checks[name] = {"path": str(relative), "expected_sha256": expected.get(name), "actual_sha256": actual, "exact": actual == expected.get(name)}
    exact = all(item["exact"] for item in checks.values())
    report = {
        "protocol": "DRTP-RUNTIME-PROFILER-PREFLIGHT-V1",
        "final_archive": str(args.final_archive),
        "source_root": str(args.source_root),
        "checks": checks,
        "verdict": "RUNTIME_PROFILER_READY" if exact else "RUNTIME_PROFILER_BLOCKED_SOURCE_MISMATCH",
        "training_started": False,
        "evaluation_started": False,
        "allowed_next_step": "Run matched UTR/DRTP short-window profiler on one GPU only after all source hashes match." if exact else "Recover the exact frozen learner source/package; do not publish or compare runtime from this source tree.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(report["verdict"])


if __name__ == "__main__":
    main()
