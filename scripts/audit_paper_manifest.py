"""Audit the generated paper command manifest before long runs."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "paper"
DEFAULT_MANIFEST = ROOT / "results" / "paper_command_manifest.csv"
DEFAULT_MAIN_CONFIG = CONFIG_DIR / "main_gate1.yaml"
DEFAULT_METHODS = ("mappo", "single_graph", "param_matched_single", "ea_rg_mappo_gate_prior", "happo")
DEFAULT_SEEDS = ("0", "1", "2")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def command_tokens(command: str) -> list[str]:
    return shlex.split(command, posix=True)


def token_value(tokens: list[str], flag: str) -> str | None:
    try:
        return tokens[tokens.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def token_values(tokens: list[str], flag: str) -> list[str]:
    try:
        start = tokens.index(flag) + 1
    except ValueError:
        return []
    values: list[str] = []
    for token in tokens[start:]:
        if token.startswith("--"):
            break
        values.append(token)
    return values


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_main_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_scenarios(main_cfg: dict, split: str) -> list[str]:
    scenario = main_cfg["scenario"]
    return [str(name) for name in scenario.get(f"{split}_scenarios", ["relay_failure"])]


def audit_manifest(
    rows: list[dict[str, str]],
    methods: tuple[str, ...],
    seeds: tuple[str, ...],
    validation_scenarios: list[str],
    test_scenarios: list[str],
) -> list[str]:
    errors: list[str] = []
    counts = Counter((row["kind"], row["method"], row["status"]) for row in rows)
    train_rows = [row for row in rows if row["kind"] == "train"]
    val_rows = [row for row in rows if row["kind"] == "validation_sweep"]
    test_rows = [row for row in rows if row["kind"] == "test_sweep"]

    require(len(train_rows) == len(methods) * len(seeds), "unexpected number of training rows", errors)
    require(len(val_rows) == len(methods), "unexpected number of validation sweep rows", errors)
    require(len(test_rows) == len(methods), "unexpected number of test sweep rows", errors)

    by_method_seed = {(row["method"], row["seed"]) for row in train_rows}
    for method in methods:
        for seed in seeds:
            require((method, seed) in by_method_seed, f"missing training row: method={method} seed={seed}", errors)

    out_dirs: list[str] = []
    train_roots_by_method: dict[str, set[str]] = defaultdict(set)
    for row in train_rows:
        tokens = command_tokens(row.get("command", ""))
        out_dir = token_value(tokens, "--out-dir")
        if out_dir is not None:
            train_roots_by_method[row["method"]].add(str(Path(out_dir).parent).replace("\\", "/"))

    for row_index, row in enumerate(rows):
        command = row.get("command", "")
        tokens = command_tokens(command)
        require(tokens[:2] == ["python", "-B"], f"row {row_index} does not start with python -B", errors)
        require("--strict-target-sensing" in tokens, f"row {row_index} missing strict sensing flag", errors)
        require("--agent-target-info-bottleneck" in tokens, f"row {row_index} missing target-info bottleneck flag", errors)
        require(token_value(tokens, "--target-policy") == "straight", f"row {row_index} unexpected target policy", errors)
        if row["kind"] == "train":
            require(row["status"] == "ready", f"training row {row_index} is not ready", errors)
            require(token_value(tokens, "--failed-blue-agent") == "1", f"row {row_index} unexpected failed blue agent", errors)
            require(token_value(tokens, "--node-failure-start-step") == "40", f"row {row_index} unexpected failure start", errors)
            require(token_value(tokens, "--node-failure-duration-steps") == "80", f"row {row_index} unexpected failure duration", errors)
            out_dir = token_value(tokens, "--out-dir")
            require(out_dir is not None, f"training row {row_index} missing out-dir", errors)
            if out_dir is not None:
                out_dirs.append(out_dir)
        if row["kind"] in {"validation_sweep", "test_sweep"}:
            root_flags = ["--no-graph-root", "--single-root", "--multi-root", "--happo-root"]
            root_values = [token_value(tokens, flag) for flag in root_flags if token_value(tokens, flag) is not None]
            require(len(root_values) == 1, f"sweep row {row_index} must contain exactly one method root", errors)
            if root_values:
                expected_roots = train_roots_by_method.get(row["method"], set())
                actual_root = str(Path(root_values[0]).as_posix())
                require(
                    actual_root in expected_roots,
                    f"sweep row {row_index} root {actual_root} does not match training roots {sorted(expected_roots)}",
                    errors,
                )
        if row["kind"] == "validation_sweep":
            require(row["status"] == "ready_after_training", f"validation row {row_index} unexpected status", errors)
            require(
                token_values(tokens, "--scenarios") == validation_scenarios,
                f"validation row {row_index} unexpected scenarios",
                errors,
            )
            if len(validation_scenarios) > 1:
                require(
                    token_value(tokens, "--selection-group") == "suite",
                    f"validation row {row_index} must use suite checkpoint selection",
                    errors,
                )
            require("--selection-csv" not in tokens, f"validation row {row_index} must not consume selection-csv", errors)
        if row["kind"] == "test_sweep":
            require(row["status"] == "ready_after_training", f"test row {row_index} unexpected status", errors)
            require(
                token_values(tokens, "--scenarios") == test_scenarios,
                f"test row {row_index} unexpected scenarios",
                errors,
            )
            if len(test_scenarios) > 1:
                require(
                    token_value(tokens, "--selection-group") == "suite",
                    f"test row {row_index} must use suite checkpoint selection",
                    errors,
                )
            require("--selection-csv" in tokens, f"test row {row_index} missing validation selection-csv", errors)
            selection_csv = token_value(tokens, "--selection-csv")
            require(
                selection_csv is not None and selection_csv.endswith("validation_selected_checkpoints.csv"),
                f"test row {row_index} selection-csv does not point to validation selection",
                errors,
            )

    duplicates = [item for item, count in Counter(out_dirs).items() if count > 1]
    require(not duplicates, f"duplicate training out-dir values: {duplicates}", errors)

    method_kinds: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        method_kinds[row["method"]].add(row["kind"])
    for method in methods:
        require(method_kinds[method] == {"train", "validation_sweep", "test_sweep"}, f"incomplete row kinds for {method}", errors)

    print(f"manifest rows: {len(rows)}")
    for key, count in sorted(counts.items()):
        print(f"{key}: {count}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--main-config", type=Path, default=DEFAULT_MAIN_CONFIG)
    parser.add_argument("--methods", nargs="*", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", nargs="*", default=DEFAULT_SEEDS)
    args = parser.parse_args()

    main_cfg = load_main_config(args.main_config)
    errors = audit_manifest(
        load_rows(args.manifest),
        tuple(args.methods),
        tuple(args.seeds),
        expected_scenarios(main_cfg, "validation"),
        expected_scenarios(main_cfg, "test"),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("paper manifest audit passed")


if __name__ == "__main__":
    main()
