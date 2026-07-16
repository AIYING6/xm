from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / "results" / "reproducibility_checksum_manifest.csv"
OUT_CSV = ROOT / "results" / "reproducibility_checksum_verification.csv"
OUT_MD = ROOT / "docs" / "reproducibility_checksum_verification.md"


@dataclass(frozen=True)
class VerificationRow:
    path: str
    artifact_group: str
    expected_size_bytes: int
    actual_size_bytes: str
    expected_sha256: str
    actual_sha256: str
    status: str
    notes: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest() -> list[dict[str, str]]:
    if not IN_CSV.exists() or IN_CSV.stat().st_size <= 0:
        raise FileNotFoundError(f"missing checksum manifest: {IN_CSV}")
    with IN_CSV.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verify_row(row: dict[str, str]) -> VerificationRow:
    rel = row["path"]
    path = ROOT / rel
    expected_size = int(row["size_bytes"])
    expected_sha256 = row["sha256"]
    if not path.exists():
        return VerificationRow(
            path=rel,
            artifact_group=row["artifact_group"],
            expected_size_bytes=expected_size,
            actual_size_bytes="missing",
            expected_sha256=expected_sha256,
            actual_sha256="missing",
            status="FAIL",
            notes="file is missing",
        )

    actual_size = path.stat().st_size
    actual_sha256 = sha256_file(path)
    mismatches = []
    if actual_size != expected_size:
        mismatches.append("size mismatch")
    if actual_sha256 != expected_sha256:
        mismatches.append("sha256 mismatch")
    status = "FAIL" if mismatches else "OK"
    return VerificationRow(
        path=rel,
        artifact_group=row["artifact_group"],
        expected_size_bytes=expected_size,
        actual_size_bytes=str(actual_size),
        expected_sha256=expected_sha256,
        actual_sha256=actual_sha256,
        status=status,
        notes="; ".join(mismatches) if mismatches else "verified",
    )


def write_csv(rows: list[VerificationRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(VerificationRow.__dataclass_fields__.keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_markdown(rows: list[VerificationRow]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failed = [row for row in rows if row.status != "OK"]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.artifact_group] = counts.get(row.artifact_group, 0) + 1

    lines = [
        "# Reproducibility Checksum Verification",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Verify that stable reproducibility package artifacts still match the recorded SHA256 hashes and file sizes.",
        "Run this after moving, archiving, or unpacking the project before relying on the evidence package.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"artifacts_verified = {len(rows)}",
        f"failures = {len(failed)}",
        *[f"{key} = {counts[key]}" for key in sorted(counts)],
        "```",
        "",
        "## Verification Table",
        "",
        "| Group | Files |",
        "|---|---:|",
    ]
    for group in sorted(counts):
        lines.append(f"| {group} | {counts[group]} |")

    if failed:
        lines.extend(["", "## Failures", ""])
        for row in failed:
            lines.append(f"- `{row.path}`: {row.notes}")
    else:
        lines.extend(["", "All manifest entries matched their recorded file sizes and SHA256 hashes.", ""])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [verify_row(row) for row in read_manifest()]
    write_csv(rows)
    write_markdown(rows)
    failures = [row for row in rows if row.status != "OK"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"artifacts verified: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
