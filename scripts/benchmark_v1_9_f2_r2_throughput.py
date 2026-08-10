"""Engineering-only worker-count benchmark before F2-R2 is opened.

It deliberately uses random PCRF-R2 weights and seeds outside the frozen F2
bank.  It writes wall-clock throughput only: no F1 checkpoint, F2 episode,
endpoint, or method comparison is accessed or recorded.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy  # noqa: E402
from evaluate_v1_9_f2_r2 import build_agent, f2_config  # noqa: E402
from f2_r2_common import write_new_json  # noqa: E402


BENCHMARK_PROTOCOL = "V1_9_F2_R2_ENGINEERING_THROUGHPUT_BENCHMARK"
BENCHMARK_SEED_BASE = 520_000  # disjoint from frozen F2 seeds 510000--510299
WORKER_COUNTS = (1, 2, 4)


def worker(output: Path, worker_index: int, episodes: int, device: str) -> None:
    if not torch.cuda.is_available() and device.startswith("cuda"):
        raise SystemExit("throughput benchmark requires CUDA")
    # Random, untrained PCRF weights exercise the same evaluator compute path
    # without reading frozen F1 weights or revealing a formal endpoint.
    torch.manual_seed(BENCHMARK_SEED_BASE + worker_index)
    cfg = f2_config("pcrf_r2", "pcrf_r2", 128, BENCHMARK_SEED_BASE + worker_index, device)
    cfg.eval_episodes = episodes
    cfg.eval_base_seed = BENCHMARK_SEED_BASE + 10_000 * worker_index
    agent = build_agent(cfg)
    started = time.perf_counter()
    eval_policy(agent, cfg, base_seed=cfg.eval_base_seed, return_event_records=False)
    elapsed = time.perf_counter() - started
    write_new_json(output, {
        "protocol_version": BENCHMARK_PROTOCOL,
        "worker_index": worker_index,
        "episodes": episodes,
        "episode_seed_base": cfg.eval_base_seed,
        "uses_f1_checkpoint": False,
        "uses_f2_episode_bank": False,
        "elapsed_seconds": elapsed,
    })


def controller(output_root: Path, episodes: int, device: str) -> None:
    if output_root.exists():
        raise SystemExit(f"refusing to reuse throughput benchmark output: {output_root}")
    output_root.mkdir(parents=True)
    candidates = []
    for worker_count in WORKER_COUNTS:
        candidate_root = output_root / f"workers_{worker_count}"
        candidate_root.mkdir()
        started = time.perf_counter()
        processes = []
        for worker_index in range(worker_count):
            worker_output = candidate_root / f"worker_{worker_index}.json"
            command = [
                sys.executable, str(Path(__file__).resolve()), "--worker",
                "--output", str(worker_output), "--worker-index", str(worker_index),
                "--episodes", str(episodes), "--device", device,
            ]
            environment = os.environ.copy()
            environment["OMP_NUM_THREADS"] = "1"
            processes.append(subprocess.Popen(command, env=environment))
        for process in processes:
            if process.wait() != 0:
                raise RuntimeError(f"throughput benchmark worker failed for workers={worker_count}")
        elapsed = time.perf_counter() - started
        total_episodes = episodes * worker_count
        candidates.append({
            "workers": worker_count,
            "episodes_per_worker": episodes,
            "total_episodes": total_episodes,
            "wall_seconds": elapsed,
            "episodes_per_second": total_episodes / elapsed,
        })
    # Choose solely by aggregate non-evidentiary throughput. Ties prefer fewer
    # workers to reduce infrastructure and CPU-contention risk.
    recommended = max(candidates, key=lambda row: (row["episodes_per_second"], -row["workers"]))["workers"]
    write_new_json(output_root / "F2_R2_THROUGHPUT_BENCHMARK_MANIFEST.json", {
        "status": "F2_R2_ENGINEERING_THROUGHPUT_BENCHMARK_COMPLETE",
        "protocol_version": BENCHMARK_PROTOCOL,
        "uses_f1_checkpoint": False,
        "uses_f2_episode_bank": False,
        "benchmark_seed_base": BENCHMARK_SEED_BASE,
        "candidates": candidates,
        "recommended_f2_workers": recommended,
    })
    print(f"F2 throughput benchmark complete; recommended F2_WORKERS={recommended}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--episodes", type=int, default=8)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--worker-index", type=int)
    args = parser.parse_args()
    if args.episodes <= 0:
        raise SystemExit("benchmark episodes must be positive")
    if args.worker:
        if args.output is None or args.worker_index is None:
            raise SystemExit("worker mode requires --output and --worker-index")
        worker(args.output, args.worker_index, args.episodes, args.device)
    else:
        if args.output_root is None:
            raise SystemExit("controller mode requires --output-root")
        controller(args.output_root, args.episodes, args.device)


if __name__ == "__main__":
    main()
