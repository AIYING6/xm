"""Write an immutable CUDA runtime manifest before a v1.9 D1 pilot."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import torch


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--protocol-version",
        default="V1_9_D1_ENGINEERING_PILOT",
        help="Immutable protocol identifier recorded in the runtime manifest.",
    )
    parser.add_argument(
        "--source-commit",
        default=None,
        help="Optional immutable source commit when the code was deployed from a source archive.",
    )
    parser.add_argument(
        "--source-archive-sha256",
        default=None,
        help="Optional SHA256 of the immutable source archive used for deployment.",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite runtime manifest: {args.output}")
    if args.source_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise ValueError("--source-commit must be a 40-character lowercase hexadecimal commit id")
    if args.source_archive_sha256 is not None and not re.fullmatch(
        r"[0-9A-Fa-f]{64}", args.source_archive_sha256
    ):
        raise ValueError("--source-archive-sha256 must be a 64-character hexadecimal SHA256")
    if not torch.cuda.is_available():
        raise RuntimeError("D1 requires CUDA, but torch.cuda.is_available() is false")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gpu_names = [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())]
    try:
        nvidia_smi = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            text=True,
        ).strip().splitlines()
    except (OSError, subprocess.CalledProcessError):
        nvidia_smi = []
    manifest = {
        "protocol_version": args.protocol_version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "source_archive_provenance": {
            "commit": args.source_commit,
            "archive_sha256": (
                args.source_archive_sha256.upper()
                if args.source_archive_sha256 is not None
                else None
            ),
        },
        "python_torch": torch.__version__,
        "cuda_available": True,
        "cuda_version": torch.version.cuda,
        "device_count": torch.cuda.device_count(),
        "gpu_names": gpu_names,
        "nvidia_smi": nvidia_smi,
    }
    args.output.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
