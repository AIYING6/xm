"""Build the frozen cloud-only C2-M3 500k-to-1M continuation package."""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ("algorithms", "envs", "scripts", "configs", "requirements.txt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with zipfile.ZipFile(args.output, "x", zipfile.ZIP_DEFLATED) as archive:
        for name in INCLUDE:
            source = ROOT / name
            if source.is_file():
                archive.write(source, source.relative_to(ROOT).as_posix())
            elif source.is_dir():
                for item in source.rglob("*"):
                    if item.is_file() and "__pycache__" not in item.parts:
                        archive.write(item, item.relative_to(ROOT).as_posix())
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="utf-8"
    )
    print(args.output)


if __name__ == "__main__":
    main()
