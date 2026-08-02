"""Audit training outputs for paper manifest runs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "paper"
DEFAULT_RUN_ROOT = ROOT / "results" / "paper_config_runs"
DEFAULT_METHODS = ("mappo", "single_graph", "param_matched_single", "ea_rg_mappo_gate_prior", "happo")


def load_main_config() -> dict:
    return json.loads((CONFIG_DIR / "main_gate1.yaml").read_text(encoding="utf-8"))


def method_run_name(method: str) -> str:
    path = CONFIG_DIR / f"{method}.yaml"
    if not path.exists():
        return method
    cfg = json.loads(path.read_text(encoding="utf-8"))
    return str(cfg.get("output_method_name", method))


def expected_updates(mode: str) -> int:
    if mode == "smoke":
        return 1
    if mode == "probe_20":
        return 20
    if mode == "freeze_rehearsal":
        updates_1m = int(load_main_config()["rollout"]["updates_for_1m_steps"])
        return max(20, int(round((updates_1m * 0.05) / 20.0)) * 20)
    if mode in {"dev_1m", "formal_bstar"}:
        return int(load_main_config()["rollout"]["updates_for_1m_steps"])
    raise ValueError(f"unsupported mode: {mode}")


def read_last_update(log_path: Path) -> int | None:
    if not log_path.exists():
        return None
    with log_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    for key in ("update", "updates"):
        if key in rows[-1]:
            return int(float(rows[-1][key]))
    return None


def audit_method_seed(run_root: Path, mode: str, method: str, seed: int, min_update: int) -> list[str]:
    errors: list[str] = []
    run_dir = run_root / mode / "runs" / method_run_name(method) / f"bc_ppo_seed{seed}"
    if not run_dir.exists():
        return [f"missing run dir: {run_dir}"]
    log_path = run_dir / "train_log.csv"
    if not log_path.exists():
        errors.append(f"missing train_log.csv: {run_dir}")
    else:
        last_update = read_last_update(log_path)
        if last_update is None:
            errors.append(f"cannot read last update from {log_path}")
        elif last_update < min_update:
            errors.append(f"{method} seed {seed} ended at update {last_update}, expected >= {min_update}")

    if method == "happo":
        latest = run_dir / "happo_latest.pt"
        snapshots = sorted(run_dir.glob("happo_update_*.pt"))
    else:
        latest = run_dir / "actor_critic_latest.pt"
        snapshots = sorted(run_dir.glob("actor_critic_update_*.pt"))
        if not (run_dir / "actor_critic_best.pt").exists():
            errors.append(f"missing actor_critic_best.pt: {run_dir}")
    if not latest.exists():
        errors.append(f"missing latest checkpoint: {latest}")
    if not snapshots:
        errors.append(f"missing snapshot checkpoints: {run_dir}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("smoke", "probe_20", "freeze_rehearsal", "dev_1m", "formal_bstar"),
    )
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--min-update", type=int, default=None)
    args = parser.parse_args()

    min_update = args.min_update if args.min_update is not None else expected_updates(args.mode)
    errors: list[str] = []
    checked = 0
    for method in args.methods:
        for seed in args.seeds:
            checked += 1
            errors.extend(audit_method_seed(args.run_root, args.mode, method, seed, min_update))

    print(f"checked runs: {checked}")
    print(f"minimum update: {min_update}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("training output audit passed")


if __name__ == "__main__":
    main()
