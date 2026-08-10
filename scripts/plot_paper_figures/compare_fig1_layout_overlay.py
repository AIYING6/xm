"""Render a size-normalized alpha overlay for Fig. 1 layout QA.

This helper only compares pixels.  It does not parse, modify, or access any
experimental output; the reference image is supplied explicitly at runtime.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGBA")
    candidate = Image.open(args.candidate).convert("RGBA")
    # The reference is the geometric master.  No cropping is performed.
    candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.blend(reference, candidate, 0.50).save(args.output)
    print(f"FIG1_LAYOUT_OVERLAY_WRITTEN: {args.output} ({reference.width}x{reference.height})")


if __name__ == "__main__":
    main()
