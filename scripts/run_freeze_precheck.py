from __future__ import annotations

import csv
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "freeze_precheck_audit.csv"
OUT_MD = ROOT / "docs" / "FREEZE_PRECHECK_REPORT.md"

REQUIRED_PROTOCOL_DOCS = {
    "docs/INFORMATION_BOUNDARY_AUDIT.md": ("Purpose", "Freeze", "Failure"),
    "docs/BASELINE_FAIRNESS_PROTOCOL.md": ("Purpose", "Fairness", "Freeze"),
    "docs/TRAINING_EVALUATION_PROTOCOL.md": ("Purpose", "Change Control", "Go/No-Go"),
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    category: str
    command: str
    status: str
    returncode: int
    stdout_tail: str
    stderr_tail: str
    notes: str


def tail(text: str, max_lines: int = 20) -> str:
    lines = text.strip().splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join([*lines[:5], "...", *lines[-max_lines + 6 :]])


def run_command(name: str, category: str, args: list[str], timeout: int = 180) -> CheckResult:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    status = "PASS" if result.returncode == 0 else "FAIL"
    return CheckResult(
        name=name,
        category=category,
        command=" ".join(args),
        status=status,
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
        notes="ok" if status == "PASS" else "nonzero exit",
    )


def check_required_doc(rel: str, markers: tuple[str, ...]) -> CheckResult:
    path = ROOT / rel
    errors = []
    if not path.exists():
        errors.append("missing")
    elif path.stat().st_size <= 0:
        errors.append("empty")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    for marker in markers:
        if marker not in text:
            errors.append(f"missing_marker:{marker}")
    return CheckResult(
        name=rel,
        category="protocol_doc",
        command="file check",
        status="PASS" if not errors else "FAIL",
        returncode=0 if not errors else 1,
        stdout_tail="",
        stderr_tail="",
        notes="ok" if not errors else ";".join(errors),
    )


def git_status_check() -> CheckResult:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    dirty = bool(result.stdout.strip())
    return CheckResult(
        name="git status clean",
        category="git",
        command="git status --short",
        status="PASS" if result.returncode == 0 and not dirty else "WARN",
        returncode=result.returncode,
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
        notes="clean" if not dirty else "working tree has local changes; commit before formal freeze",
    )


def write_csv(rows: list[CheckResult]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "category",
                "command",
                "status",
                "returncode",
                "stdout_tail",
                "stderr_tail",
                "notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_markdown(rows: list[CheckResult]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row.status == "FAIL"]
    warnings = [row for row in rows if row.status == "WARN"]
    lines = [
        "# Freeze Precheck Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Run the non-training checks required before freeze rehearsal or formal experiment freeze.",
        "FAIL blocks freeze. WARN requires review before creating a freeze tag.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Checks | {len(rows)} |",
        f"| Failures | {len(failures)} |",
        f"| Warnings | {len(warnings)} |",
        "",
        "## Checks",
        "",
        "| Name | Category | Status | Notes |",
        "|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(f"| `{row.name}` | {row.category} | {row.status} | {row.notes} |")
    if failures or warnings:
        lines.extend(["", "## Attention Items", ""])
        for row in [*failures, *warnings]:
            lines.extend(
                [
                    f"### {row.name}",
                    "",
                    f"Status: `{row.status}`",
                    "",
                    "Command:",
                    "",
                    "```text",
                    row.command,
                    "```",
                    "",
                    "stdout:",
                    "",
                    "```text",
                    row.stdout_tail,
                    "```",
                    "",
                    "stderr:",
                    "",
                    "```text",
                    row.stderr_tail,
                    "```",
                    "",
                ]
            )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows: list[CheckResult] = []
    rows.extend(
        check_required_doc(rel, markers)
        for rel, markers in REQUIRED_PROTOCOL_DOCS.items()
    )
    rows.extend(
        [
            run_command(
                "paper config audit",
                "config",
                [sys.executable, "scripts/audit_paper_configs.py"],
            ),
            run_command(
                "checkpoint selection schema audit",
                "config",
                [sys.executable, "scripts/audit_checkpoint_selection_schema.py"],
            ),
            run_command(
                "information boundary tests",
                "test",
                [sys.executable, "-m", "pytest", "tests/test_gate1_communication_feasibility.py", "-q"],
                timeout=300,
            ),
            run_command(
                "reproducibility artifact gate",
                "artifact",
                [sys.executable, "scripts/check_reproducibility_artifacts.py"],
            ),
            git_status_check(),
        ]
    )
    write_csv(rows)
    write_markdown(rows)
    failures = [row for row in rows if row.status == "FAIL"]
    warnings = [row for row in rows if row.status == "WARN"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"checks: {len(rows)}")
    print(f"failures: {len(failures)}")
    print(f"warnings: {len(warnings)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
