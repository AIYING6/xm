# gen_gpt_package_v1_5.py — build a maximally informative zip for the GPT web client.
# Excludes only: .git, .pt checkpoints, per-episode metric CSVs (huge, aggregated in
# canonical), __pycache__/.pyc, .pytest_cache, _tmp_* scratch, files > 100 MB.
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

MAIN = Path(r"D:/Code/Codex/ri_gmappo_uav")
MAPP = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5")
ABLA = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
OUT = Path(r"D:/ri_gmappo_uav_for_gpt_full.zip")
MAX_BYTES = 100 * 1024 * 1024

EXCLUDE_DIR = {".git", "__pycache__", ".pytest_cache"}
EXCLUDE_SUBSTR = ("_tmp_", ".pyc")
EXCLUDE_SUFFIX = {".pt"}
EXCLUDE_NAME = {".DS_Store"}


def wanted(p: Path) -> bool:
    if p.name in EXCLUDE_NAME or p.suffix in EXCLUDE_SUFFIX:
        return False
    if any(x in p.name for x in EXCLUDE_SUBSTR):
        return False
    try:
        if p.stat().st_size > MAX_BYTES:
            return False
    except OSError:
        return False
    return True


def walk(base: Path, arc_root: str) -> list[tuple[str, str]]:
    items = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR]
        rp = Path(root).relative_to(base)
        for fn in files:
            fp = Path(root) / fn
            if not wanted(fp):
                continue
            arc = f"{arc_root}/{rp / fn}"
            items.append((str(fp), arc))
    return items


def main():
    entries = []
    # main worktree: everything except excluded
    entries += walk(MAIN, "main")
    # mappo worktree: held-out/robustness/efficiency audit + raw summaries + validation + protocol
    for sub in ("results/paper_config_runs/formal_held_out_v1_5_10800_20260807",
                "results/paper_config_runs/formal_robustness_v1.5_10500_20260807",
                "results/paper_config_runs/formal_efficiency_v1.5_20260807",
                "results/paper_config_runs/formal_mappo_v1.5_ppo_977_20260806",
                "results/paper_config_runs/formal_mappo_v1.5_validation_selector_v1.5.1_20260806",
                "results/paper_config_runs/formal_mappo_v1.5_bc_freeze",
                "docs"):
        base = MAPP / sub
        if base.exists():
            entries += walk(base, f"mappo/{sub}")
    # ablation worktree: raw training logs + validation + docs
    for sub in ("results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804",
                "results/paper_config_runs/formal_ablation_v1.5_validation_selector_v1.5.1_20260805",
                "docs"):
        base = ABLA / sub
        if base.exists():
            entries += walk(base, f"ablation/{sub}")

    # de-dup by arc (mappo/docs may overlap mappo main paths)
    seen = {}
    for src, arc in entries:
        if arc not in seen:
            seen[arc] = src

    n = 0
    tot = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for arc in sorted(seen):
            src = seen[arc]
            try:
                z.write(src, arc)
                n += 1
                tot += os.path.getsize(src)
            except OSError:
                continue
    print(f"files: {n}  uncompressed MB: {tot/1e6:.1f}  zip MB: {OUT.stat().st_size/1e6:.1f}")
    print(f"output: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
