#!/usr/bin/env python3
"""Build a conservative, read-only evidence-retention inventory.

The inventory never moves or deletes files.  It deliberately assigns ambiguous
archives to ``unresolved`` rather than guessing they are disposable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ACTIVE_TOP_LEVEL = {"algorithms", "envs", "configs", "scripts", "tests"}
TEMP_MARKERS = (".tmp", "__pycache__", ".audit_", "_qa_", "rendered", "pdf_pages")
ACTIVE_DOCUMENT_MARKERS = ("drtp", "canonical", "reproducib", "claim_evidence", "submission", "retention")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path, repo: Path) -> tuple[str, str]:
    try:
        relative = path.relative_to(repo)
        parts = relative.parts
        lower = str(relative).lower()
        if parts and parts[0] in ACTIVE_TOP_LEVEL:
            return "keep_active", "maintained source or configuration asset"
        if any(marker in lower for marker in TEMP_MARKERS):
            return "delete_candidate", "temporary render, cache, or diagnostic workspace"
        if parts and parts[0] == "archival":
            return "keep_archive", "already placed in the archival namespace"
        if parts and parts[0] == "docs":
            if any(marker in lower for marker in ACTIVE_DOCUMENT_MARKERS):
                return "keep_active", "active evidence, reproducibility, or manuscript documentation"
            return "unresolved", "documentation requires provenance review before archival or removal"
        if parts and parts[0] == "results":
            return "unresolved", "results require report-to-contract provenance linkage"
        if parts and parts[0] == "artifacts":
            return "unresolved", "artifact may be final evidence or an intermediate diagnostic"
        if path.suffix.lower() in {".zip", ".gz", ".bundle"}:
            return "unresolved", "cloud/archive package; retain until deduplicated against a final report"
        return "unresolved", "outside automatic safe classification"
    except ValueError:
        return "unresolved", "external historical location; provenance not yet linked to repository evidence"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--scan-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-bytes", type=int, default=0)
    parser.add_argument("--with-sha256", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to inventory without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    repo = args.repo.resolve()
    rows = []
    for root in args.scan_root:
        root = root.resolve()
        if not root.is_dir():
            rows.append({"path": str(root), "bytes": "", "classification": "unresolved", "reason": "scan root unavailable", "sha256": ""})
            continue
        for path in root.rglob("*"):
            # Git object packs and nested third-party repositories are version
            # control internals, not research assets to classify or delete.
            if ".git" in path.parts:
                continue
            if not path.is_file():
                continue
            size = path.stat().st_size
            if size < args.min_bytes:
                continue
            status, reason = classify(path, repo)
            rows.append({"path": str(path), "bytes": size, "classification": status, "reason": reason,
                         "sha256": digest(path) if args.with_sha256 else ""})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "classification", "reason", "sha256"])
        writer.writeheader(); writer.writerows(sorted(rows, key=lambda row: int(row["bytes"] or 0), reverse=True))
    print(f"inventory_rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
