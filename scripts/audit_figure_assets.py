from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIG_DIR = ROOT / "results" / "figures"
DEFAULT_CSV = ROOT / "results" / "figure_asset_audit.csv"
DEFAULT_REPORT = ROOT / "docs" / "figure_asset_audit.md"


@dataclass(frozen=True)
class FigureAuditRow:
    figure: str
    width: int
    height: int
    file_size_kb: float
    gray_std: float
    sampled_unique_colors: int
    status: str
    notes: str


def sampled_unique_colors(rgb: np.ndarray, max_pixels: int = 120000) -> int:
    pixels = rgb.reshape(-1, rgb.shape[-1])
    if len(pixels) > max_pixels:
        step = max(1, len(pixels) // max_pixels)
        pixels = pixels[::step]
    return int(len(np.unique(pixels, axis=0)))


def audit_figure(path: Path, root: Path) -> FigureAuditRow:
    notes = []
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        rgb_image = image.convert("RGB")
    rgb = np.asarray(rgb_image, dtype=np.uint8)
    gray = np.asarray(rgb_image.convert("L"), dtype=np.float32)
    file_size_kb = path.stat().st_size / 1024.0
    gray_std = float(np.std(gray))
    unique = sampled_unique_colors(rgb)

    if width < 900 or height < 500:
        notes.append("small_dimensions")
    if file_size_kb < 10.0:
        notes.append("small_file")
    if gray_std < 8.0:
        notes.append("low_pixel_variation")
    if unique < 32:
        notes.append("few_unique_colors")
    status = "ok" if not notes else "warning"
    return FigureAuditRow(
        figure=str(path.relative_to(root)).replace("\\", "/"),
        width=width,
        height=height,
        file_size_kb=file_size_kb,
        gray_std=gray_std,
        sampled_unique_colors=unique,
        status=status,
        notes=";".join(notes) if notes else "ok",
    )


def find_figures(fig_dir: Path) -> list[Path]:
    return sorted(path for path in fig_dir.glob("*.png") if path.is_file())


def write_csv(rows: list[FigureAuditRow], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "figure",
        "width",
        "height",
        "file_size_kb",
        "gray_std",
        "sampled_unique_colors",
        "status",
        "notes",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "figure": row.figure,
                    "width": row.width,
                    "height": row.height,
                    "file_size_kb": f"{row.file_size_kb:.3f}",
                    "gray_std": f"{row.gray_std:.3f}",
                    "sampled_unique_colors": row.sampled_unique_colors,
                    "status": row.status,
                    "notes": row.notes,
                }
            )


def write_report(rows: list[FigureAuditRow], out_report: Path) -> None:
    out_report.parent.mkdir(parents=True, exist_ok=True)
    warnings = [row for row in rows if row.status != "ok"]
    lines = [
        "# Figure Asset Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check paper figure assets for missing, tiny, or near-blank PNG outputs.",
        "This is a technical asset audit, not a visual-design or scientific-content review.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| PNG figures checked | {len(rows)} |",
        f"| Warnings | {len(warnings)} |",
        "",
        "## Audit Rows",
        "",
        "| Figure | Size | File KB | Gray std | Unique colors | Status | Notes |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row.figure}` | {row.width}x{row.height} | {row.file_size_kb:.1f} | "
            f"{row.gray_std:.1f} | {row.sampled_unique_colors} | {row.status} | {row.notes} |"
        )
    lines.extend(
        [
            "",
            "## Thresholds",
            "",
            "```text",
            "warning if width < 900 or height < 500",
            "warning if file size < 10 KB",
            "warning if grayscale standard deviation < 8",
            "warning if sampled unique RGB colors < 32",
            "```",
            "",
        ]
    )
    out_report.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated paper figure assets.")
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fig_dir = args.fig_dir if args.fig_dir.is_absolute() else ROOT / args.fig_dir
    figures = find_figures(fig_dir)
    if not figures:
        raise RuntimeError(f"no PNG figures found in {fig_dir}")
    rows = [audit_figure(path, ROOT) for path in figures]
    write_csv(rows, args.out_csv if args.out_csv.is_absolute() else ROOT / args.out_csv)
    write_report(rows, args.report if args.report.is_absolute() else ROOT / args.report)
    hard_failures = [row for row in rows if "low_pixel_variation" in row.notes or "few_unique_colors" in row.notes]
    print(args.out_csv)
    print(args.report)
    print(f"figures checked: {len(rows)}")
    print(f"warnings: {sum(row.status != 'ok' for row in rows)}")
    if hard_failures:
        for row in hard_failures:
            print(f"hard failure: {row.figure} {row.notes}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
