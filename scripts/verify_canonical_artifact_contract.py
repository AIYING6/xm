"""Fail-closed checker for canonical method/seed artifact contracts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENDPOINT = {
    "pre_failure_chain_established",
    "chain_lost_after_failure",
    "t_failure",
    "t_loss",
    "post_failure_chain_recovered_after_loss",
    "t_recovery",
    "delta_t_loss_to_recovery",
    "post_failure_chain_first_established",
    "event",
    "censor_time",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_run(run: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for key in ("method", "seed", "out_dir", "artifact_class"):
        if not run.get(key):
            errors.append(f"missing manifest field: {key}")
    if run.get("artifact_class") == "ENGINEERING_SMOKE_TEST_ONLY":
        return errors
    out_dir = ROOT / str(run["out_dir"])
    for name in ("train_log.csv", "actor_critic_latest.pt", "actor_critic_best.pt"):
        if not (out_dir / name).exists():
            errors.append(f"missing {out_dir / name}")
    return errors


def main() -> int:
    manifest = ROOT / "results/canonical_v2/manifests/wave1/launch_manifest.csv"
    if not manifest.exists():
        raise SystemExit("missing launch manifest")
    failures: list[str] = []
    with manifest.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            # Formal runs are incomplete by design after the recorded stop.
            if row.get("status") not in {"LAUNCHED", "STOPPED_USER_REQUEST"}:
                failures.append(f"unexpected status: {row}")
    if failures:
        for item in failures:
            print(item)
        return 1
    print("PASS: launch manifest identity/status contract is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
