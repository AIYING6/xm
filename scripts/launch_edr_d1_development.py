"""Launch the one-shot EDR-D1 five-seed run, then frozen evaluation/aggregation."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_edr_d1_single import SEEDS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--max-parallel", type=int, default=3)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.max_parallel < 1:
        raise ValueError("max-parallel must be positive")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite EDR-D1 output root: {args.output_root}")
    args.output_root.mkdir(parents=True, exist_ok=False)

    pending = list(SEEDS)
    active: dict[int, subprocess.Popen] = {}
    logs = args.output_root / "launcher_logs"
    logs.mkdir()
    while pending or active:
        while pending and len(active) < args.max_parallel:
            seed = pending.pop(0)
            stdout = (logs / f"seed{seed}.out").open("w", encoding="utf-8")
            stderr = (logs / f"seed{seed}.err").open("w", encoding="utf-8")
            command = [sys.executable, "scripts/run_edr_d1_single.py", "--seed", str(seed), "--output-root", str(args.output_root), "--t1-root", str(args.t1_root), "--execute"]
            active[seed] = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr, env=os.environ.copy())
            print(f"launched EDR-D1 seed{seed} pid={active[seed].pid}", flush=True)
        finished = []
        for seed, process in active.items():
            code = process.poll()
            if code is not None:
                if code != 0:
                    raise RuntimeError(f"EDR-D1 seed{seed} failed with exit code {code}; inspect {logs}")
                print(f"completed EDR-D1 seed{seed}", flush=True)
                finished.append(seed)
        for seed in finished:
            active.pop(seed)
        if active:
            time.sleep(5)

    evaluation = [sys.executable, "scripts/run_edr_d1_evaluation.py", "--output-root", str(args.output_root), "--t1-root", str(args.t1_root), "--device", args.device, "--execute"]
    subprocess.run(evaluation, cwd=ROOT, check=True)
    aggregate = [sys.executable, "scripts/aggregate_edr_d1.py", "--edr-root", str(args.output_root), "--t1-root", str(args.t1_root), "--execute"]
    subprocess.run(aggregate, cwd=ROOT, check=True)
    print("EDR-D1 training, evaluation, and aggregate completed", flush=True)


if __name__ == "__main__":
    main()
