"""Build the source-only cloud package for the authorized frozen C2 pilot."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite package: {args.output}")
    include = ("algorithms", "envs", "scripts", "configs", "requirements.txt")
    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in include:
            source = ROOT / item
            if source.is_file():
                archive.write(source, source.relative_to(ROOT).as_posix())
            elif source.is_dir():
                for path in source.rglob("*"):
                    if path.is_file() and "__pycache__" not in path.parts:
                        archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("C2_SOURCE_PACKAGE.txt", "Authorized C2 source-only cloud package.\n")
    checksum = args.output.with_suffix(args.output.suffix + ".sha256")
    checksum.write_text(f"{sha256(args.output)}  {args.output.name}\n", encoding="utf-8")
    print(f"package={args.output}")
    print(f"sha256={checksum}")


if __name__ == "__main__":
    main()
