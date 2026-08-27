"""Check whether the frozen Chinese DRTP manuscript can be released for submission.

This is deliberately a release gate, not an experiment runner.  It verifies the
local manuscript, PDF and anonymous reproducibility staging package, then
separately reports author-owned metadata and external-hosting requirements.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "q2_final_zh"
PDF = PAPER / "output" / "DRTP_SG_MAPPO_中文论文初稿_投稿证据整合终版.pdf"
PACKAGE = ROOT / "output" / "drtp_relay_failure_anonymous_reproducibility_v1"

AUTHOR_REQUIRED_TEXT_FIELDS = (
    "target_journal",
    "article_type",
    "anonymous_reviewer_repository_url",
    "public_repository_persistent_identifier",
    "licence",
    "checkpoint_access_policy",
    "corresponding_author",
)
AUTHOR_REQUIRED_BOOL_FIELDS = (
    "author_metadata_complete",
    "external_download_and_checksum_verified",
    "target_template_migration_verified",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def has_value(value: object) -> bool:
    return isinstance(value, str) and value.strip() and "待作者填写" not in value


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"nested verification failed: {message}")


def local_checks() -> None:
    run([sys.executable, str(ROOT / "scripts" / "check_q2_final_zh_manuscript.py")])
    require(PDF.is_file() and PDF.stat().st_size > 1_000_000,
            f"submission PDF missing or unexpectedly small: {PDF}")
    require(PACKAGE.is_dir(), f"anonymous reproducibility staging package missing: {PACKAGE}")
    run([
        sys.executable,
        str(ROOT / "scripts" / "check_drtp_anonymous_reproducibility_package.py"),
        "--package-root",
        str(PACKAGE),
    ])
    manifest = json.loads((PAPER / "25_final_evidence_manifest.json").read_text(encoding="utf-8"))
    require(manifest["status"] == "submission_closeout_prepared_author_hosting_required",
            "unexpected evidence-manifest release state")
    require(manifest["new_training_authorized"] is False,
            "release gate must never authorize new training")
    require(len(manifest["evidence_strata"]) == 3,
            "all three evidence strata must remain present")


def author_gaps(path: Path | None) -> list[str]:
    if path is None:
        return ["no private release metadata file supplied"]
    require(path.is_file(), f"release metadata file does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(payload.get("schema") == "drtp-chinese-submission-release-metadata-v1",
            "unexpected release metadata schema")
    gaps = [name for name in AUTHOR_REQUIRED_TEXT_FIELDS if not has_value(payload.get(name))]
    gaps.extend(name for name in AUTHOR_REQUIRED_BOOL_FIELDS if payload.get(name) is not True)
    return gaps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-metadata", type=Path)
    parser.add_argument("--require-author-completion", action="store_true")
    args = parser.parse_args()

    local_checks()
    gaps = author_gaps(args.release_metadata)
    if gaps:
        print("TECHNICAL_READY_AUTHOR_ACTION_REQUIRED")
        print("author-owned unresolved fields:")
        for gap in gaps:
            print(f"- {gap}")
        if args.require_author_completion:
            raise SystemExit(2)
        return
    print("SUBMISSION_RELEASE_READY")
    print("local evidence, PDF, staging package, author metadata and external release checks are complete.")


if __name__ == "__main__":
    main()
