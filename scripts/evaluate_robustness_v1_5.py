# evaluate_robustness_v1_5.py
# Robustness evaluation entrypoint for FORMAL_ROBUSTNESS_PROTOCOL_V1_5.
#
# Thin wrapper around the FROZEN evaluation entrypoints:
#   - imports the frozen evaluation/summarize/selector logic verbatim,
#   - EXTENDS the scenario dictionary with the 5 new robustness conditions
#     (combinations of existing env parameters ONLY; frozen env/training and
#     the frozen scenario file on disk are untouched),
#   - injects the extended registry into the module used by the CHOSEN entry
#     (sweep / happo / mappo) and verifies the injected identity.
#
# MODULE-COPY SAFETY: the repo has several copies of scripts.evaluate_3d_*.
# For each --entry we (1) put the CORRECT worktree's scripts/ dir first on
# sys.path, (2) import the topology_robustness registry FROM that worktree,
# (3) import the entrypoint module and require module.__file__ == the expected
# file, and (4) report file SHA + SCENARIOS identity, so the executed module
# instance is provably the one patched.
#
# Frozen semantics preserved: split=test skips the selector; selection CSV is
# an empty mechanical artifact; aggregation identical to held-out audit.
#
# Usage:
#   python evaluate_robustness_v1_5.py --entry sweep --split test \
#       --base-seed 946804 ... --scenarios dropout050_delay2_relay_failure ...
#   python evaluate_robustness_v1_5.py --entry sweep --verify-imports
from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
MP_ROOT = ROOT

# entry -> (scripts root dir to put first, module name, expected module file)
ENTRY_MODULES = {
    "sweep": (AB_ROOT, "scripts.evaluate_3d_checkpoint_sweep",
              AB_ROOT / "scripts/evaluate_3d_checkpoint_sweep.py"),
    "happo": (AB_ROOT, "scripts.evaluate_happo_checkpoint_sweep",
              AB_ROOT / "scripts/evaluate_happo_checkpoint_sweep.py"),
    "mappo": (MP_ROOT, "scripts.evaluate_mappo_v1_5",
              MP_ROOT / "scripts/evaluate_mappo_v1_5.py"),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def build_extended_scenarios(scripts_root: Path) -> dict:
    """Import topology_robustness from the chosen worktree and extend it.

    Importing AFTER scripts_root is on sys.path ensures sys.modules caches the
    correct worktree copy (no cross-worktree copy pollution).
    """
    sys.path.insert(0, str(scripts_root))
    from scripts.evaluate_3d_topology_robustness import (  # noqa: E402
        SCENARIOS as BASE,
        RobustnessScenario,
    )
    extra = {
        "dropout050_delay2_relay_failure": RobustnessScenario(
            "dropout050_delay2_relay_failure",
            communication_dropout_prob=0.50,
            message_delay_steps=2,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        ),
        "dropout070_delay2_relay_failure": RobustnessScenario(
            "dropout070_delay2_relay_failure",
            communication_dropout_prob=0.70,
            message_delay_steps=2,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        ),
        "dropout030_delay4_relay_failure": RobustnessScenario(
            "dropout030_delay4_relay_failure",
            communication_dropout_prob=0.30,
            message_delay_steps=4,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        ),
        "dropout030_delay8_relay_failure": RobustnessScenario(
            "dropout030_delay8_relay_failure",
            communication_dropout_prob=0.30,
            message_delay_steps=8,
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        ),
        "dropout070_delay8_relay_failure_early": RobustnessScenario(
            "dropout070_delay8_relay_failure_early",
            communication_dropout_prob=0.70,
            message_delay_steps=8,
            failed_blue_agent=1,
            node_failure_start_step=25,
            node_failure_duration_steps=80,
        ),
    }
    return {**BASE, **extra}


def main() -> None:
    if "--entry" not in sys.argv:
        raise SystemExit("--entry {sweep|happo|mappo} is required")
    idx = sys.argv.index("--entry")
    entry = sys.argv[idx + 1]
    del sys.argv[idx:idx + 2]

    if entry not in ENTRY_MODULES:
        raise SystemExit(f"unknown --entry {entry!r}")

    scripts_root, mod_name, expected_file = ENTRY_MODULES[entry]
    extended = build_extended_scenarios(scripts_root)
    module = importlib.import_module(mod_name)
    actual_file = Path(module.__file__).resolve()
    if actual_file != expected_file.resolve():
        raise SystemExit(
            f"module-copy guard FAILED for --entry {entry}: "
            f"imported {actual_file} != expected {expected_file}"
        )
    keys_before = set(getattr(module, "SCENARIOS", {}).keys())
    module.SCENARIOS = extended
    keys_after = set(module.SCENARIOS.keys())
    print(f"[robustness] entry={entry} module={actual_file} sha={sha256_file(actual_file)}", flush=True)
    print(f"[robustness] SCENARIOS keys before={len(keys_before)} after={len(keys_after)} "
          f"new={sorted(keys_after - keys_before)}", flush=True)
    print(f"[robustness] SCENARIOS identity={id(module.SCENARIOS)} extended={id(extended)}", flush=True)

    if "--verify-imports" in sys.argv:
        v = sys.argv.index("--verify-imports")
        del sys.argv[v:v + 1]
        for k in sorted(EXTRA_KEYS(module.SCENARIOS)):
            s = module.SCENARIOS[k]
            print(f"[robustness] {k}: dropout={s.communication_dropout_prob} "
                  f"delay={s.message_delay_steps} agent={s.failed_blue_agent} "
                  f"start={s.node_failure_start_step} dur={s.node_failure_duration_steps}", flush=True)
        print("[robustness] verify-imports OK", flush=True)
        return
    module.main()


def EXTRA_KEYS(registry: dict) -> list[str]:
    """The 5 new robustness keys (order stable)."""
    order = [
        "dropout050_delay2_relay_failure",
        "dropout070_delay2_relay_failure",
        "dropout030_delay4_relay_failure",
        "dropout030_delay8_relay_failure",
        "dropout070_delay8_relay_failure_early",
    ]
    return [k for k in order if k in registry]


if __name__ == "__main__":
    main()
