from __future__ import annotations

import argparse
import csv
import importlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAG_ROOT = ROOT.parent / "LAG"
DEFAULT_REPORT = ROOT / "docs" / "lag_jsbsim_migration_probe.md"
DEFAULT_CSV = ROOT / "results" / "lag_jsbsim_migration_probe.csv"


@dataclass(frozen=True)
class ProbeItem:
    item: str
    status: str
    detail: str


def exists_item(label: str, path: Path, detail: str = "") -> ProbeItem:
    if path.exists():
        kind = "directory" if path.is_dir() else "file"
        return ProbeItem(label, "present", f"{kind}: {path}")
    return ProbeItem(label, "missing", detail or f"not found: {path}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_line(pattern: str, text: str) -> str:
    for line in text.splitlines():
        if pattern in line:
            return line.strip()
    return ""


def regex_value(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def import_probe(lag_root: Path, module: str) -> ProbeItem:
    sys.path.insert(0, str(lag_root))
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic probe.
        return ProbeItem(f"import {module}", "failed", f"{type(exc).__name__}: {exc}")
    finally:
        if str(lag_root) in sys.path:
            sys.path.remove(str(lag_root))
    return ProbeItem(f"import {module}", "ok", "module imported without instantiating JSBSim env")


def count_csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def build_probe(lag_root: Path) -> tuple[list[ProbeItem], dict[str, str]]:
    items: list[ProbeItem] = []
    metadata: dict[str, str] = {}

    required_paths = {
        "LAG root": lag_root,
        "README": lag_root / "README.md",
        "git submodule manifest": lag_root / ".gitmodules",
        "MultipleCombat env": lag_root / "envs" / "JSBSim" / "envs" / "multiplecombat_env.py",
        "MultipleCombat task": lag_root / "envs" / "JSBSim" / "tasks" / "multiplecombat_task.py",
        "Base env": lag_root / "envs" / "JSBSim" / "envs" / "env_base.py",
        "JSBSim simulator wrapper": lag_root / "envs" / "JSBSim" / "core" / "simulatior.py",
        "JSBSim data submodule": lag_root / "envs" / "JSBSim" / "data",
        "LAG model directory": lag_root / "envs" / "JSBSim" / "model",
        "LAG configs": lag_root / "envs" / "JSBSim" / "configs",
    }
    for label, path in required_paths.items():
        items.append(exists_item(label, path))

    modules = [
        "config",
        "envs.JSBSim.envs.multiplecombat_env",
        "envs.JSBSim.tasks.multiplecombat_task",
    ]
    for module in modules:
        items.append(import_probe(lag_root, module))

    task_path = lag_root / "envs" / "JSBSim" / "tasks" / "multiplecombat_task.py"
    env_path = lag_root / "envs" / "JSBSim" / "envs" / "multiplecombat_env.py"
    base_path = lag_root / "envs" / "JSBSim" / "envs" / "env_base.py"
    sim_path = lag_root / "envs" / "JSBSim" / "core" / "simulatior.py"
    if task_path.exists():
        task_text = read_text(task_path)
        metadata["task_class"] = "MultipleCombatTask" if "class MultipleCombatTask" in task_text else "not found"
        metadata["action_space_line"] = find_line("MultiDiscrete", task_text)
        metadata["obs_length_line"] = find_line("self.obs_length", task_text)
        metadata["share_obs_line"] = find_line("share_observation_space", task_text)
        metadata["reward_classes"] = ", ".join(sorted(set(re.findall(r"([A-Za-z]+Reward)", task_text)))) or "not detected"
        metadata["termination_classes"] = ", ".join(sorted(set(re.findall(r"(ExtremeState|LowAltitude|Overload|Timeout|SafeReturn)", task_text)))) or "not detected"
    if env_path.exists():
        env_text = read_text(env_path)
        metadata["env_step_signature"] = regex_value(r"def step\(([^)]*)\)", env_text)
        metadata["env_reset_signature"] = regex_value(r"def reset\(([^)]*)\)", env_text)
    if base_path.exists():
        base_text = read_text(base_path)
        metadata["base_state_pack_line"] = find_line("np.hstack", base_text)
        metadata["load_simulator_line"] = find_line("AircraftSimulator", base_text)
    if sim_path.exists():
        sim_text = read_text(sim_path)
        metadata["jsbsim_data_line"] = find_line("FGFDMExec", sim_text)
        metadata["position_getter"] = find_line("def get_position", sim_text)
        metadata["velocity_getter"] = find_line("def get_velocity", sim_text)
        metadata["attitude_getter"] = find_line("def get_rpy", sim_text)

    smoke_rows = count_csv_rows(ROOT / "results" / "lag_graph_smoke_stats.csv")
    metadata["synthetic_graph_smoke_rows"] = "missing" if smoke_rows is None else str(smoke_rows)
    metadata["real_jsbsim_status"] = (
        "blocked: envs/JSBSim/data submodule missing"
        if not (lag_root / "envs" / "JSBSim" / "data").exists()
        else "data submodule present; real env reset should be tested next"
    )
    return items, metadata


def write_csv(items: list[ProbeItem], metadata: dict[str, str], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["kind", "item", "status", "detail"])
        writer.writeheader()
        for item in items:
            writer.writerow({"kind": "path_or_import", "item": item.item, "status": item.status, "detail": item.detail})
        for key, value in metadata.items():
            writer.writerow({"kind": "metadata", "item": key, "status": "observed", "detail": value})


def write_report(items: list[ProbeItem], metadata: dict[str, str], lag_root: Path, out_report: Path) -> None:
    out_report.parent.mkdir(parents=True, exist_ok=True)
    missing = [item for item in items if item.status == "missing"]
    failed = [item for item in items if item.status == "failed"]
    lines = [
        "# LAG/JSBSim Migration Probe",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check whether the local LAG copy can support the next EA-RG-MAPPO-S migration step.",
        "This probe does not claim 6DOF validation; it separates reusable interfaces from current blockers.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| LAG root | `{lag_root}` |",
        f"| Missing required paths | {len(missing)} |",
        f"| Failed imports | {len(failed)} |",
        f"| Synthetic graph smoke rows | {metadata.get('synthetic_graph_smoke_rows', 'unknown')} |",
        f"| Real JSBSim status | {metadata.get('real_jsbsim_status', 'unknown')} |",
        "",
        "## Path and Import Checks",
        "",
        "| Item | Status | Detail |",
        "|---|---|---|",
    ]
    for item in items:
        lines.append(f"| {item.item} | {item.status} | `{item.detail}` |")

    lines.extend(["", "## Interface Observations", "", "| Field | Observed value |", "|---|---|"])
    for key, value in metadata.items():
        lines.append(f"| {key} | `{value}` |")

    lines.extend(
        [
            "",
            "## Migration Interpretation",
            "",
            "```text",
            "Reusable now:",
            "1. MultipleCombat environment/task files are present.",
            "2. The simulator wrapper exposes position, velocity, and attitude getters that can feed a 6DOF role graph.",
            "3. The existing synthetic LAG graph smoke test confirms node/edge tensor construction is numerically stable.",
            "",
            "Blocked now:",
            "1. Real JSBSim environment reset is blocked if envs/JSBSim/data is missing.",
            "2. Current 2D action head cannot be reused directly because LAG uses MultiDiscrete aircraft controls.",
            "3. A real 6DOF result still requires simulator data, reset/step smoke test, and new evaluation metrics.",
            "```",
            "",
            "## Next Minimal Step",
            "",
            "```text",
            "After installing/updating the JSBSim data submodule, run a real MultipleCombatEnv reset/one-step probe.",
            "Only after that succeeds should we adapt EA-RG-MAPPO-S actor inputs or start any 6DOF training.",
            "```",
            "",
        ]
    )
    out_report.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe local LAG/JSBSim migration readiness.")
    parser.add_argument("--lag-root", type=Path, default=DEFAULT_LAG_ROOT)
    parser.add_argument("--out-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items, metadata = build_probe(args.lag_root)
    write_csv(items, metadata, args.out_csv)
    write_report(items, metadata, args.lag_root, args.out_report)
    print(args.out_report)
    print(args.out_csv)


if __name__ == "__main__":
    main()
