from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "runtime_environment_report.md"


def tool_version(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        return "not found"
    try:
        result = subprocess.run(
            [name, "--version"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"found at {path}; version check failed: {exc}"
    first_line = (result.stdout or result.stderr).splitlines()
    version = first_line[0] if first_line else "version output empty"
    return f"{path} ({version})"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available and torch.cuda.device_count() > 0 else "not available"
    lines = [
        "# Runtime Environment Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Python",
        "",
        "```text",
        f"executable: {sys.executable}",
        f"version: {sys.version.replace(chr(10), ' ')}",
        f"platform: {platform.platform()}",
        "```",
        "",
        "## PyTorch/CUDA",
        "",
        "```text",
        f"torch: {torch.__version__}",
        f"cuda_available: {cuda_available}",
        f"torch_cuda_version: {torch.version.cuda}",
        f"gpu_count: {torch.cuda.device_count()}",
        f"gpu_name: {gpu_name}",
        "```",
        "",
        "## LaTeX Toolchain",
        "",
        "```text",
        f"xelatex: {tool_version('xelatex')}",
        f"latexmk: {tool_version('latexmk')}",
        f"bibtex: {tool_version('bibtex')}",
        "```",
        "",
        "Interpretation:",
        "",
        "```text",
        "Training/evaluation scripts can run in the current Python environment.",
        "PDF rendering is unavailable unless a LaTeX distribution providing xelatex is installed.",
        "```",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
