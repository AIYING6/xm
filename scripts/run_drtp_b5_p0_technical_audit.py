#!/usr/bin/env python3
"""Zero-training technical audit for B5 group-conditioned credit telemetry."""

from __future__ import annotations

import ast
import csv
import json
import math
import runpy
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.group_credit_telemetry import (  # noqa: E402
    CONFLICT_FIELDS,
    GROUP_FIELDS,
    summarize_group_credit_assignment,
)


CONFIG = ROOT / "configs" / "drtp_b5_p0_credit_telemetry_freeze.json"
OUT = ROOT / "docs" / "drtp_b5_p0_20260830"
TEST = ROOT / "tests" / "test_drtp_b5_group_credit_telemetry.py"


def no_mutating_calls(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"backward", "step", "zero_grad"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in forbidden:
            return False
    return True


def static_checks(config: dict) -> dict[str, bool]:
    trainer = (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
    telemetry_path = ROOT / "algorithms" / "ri_gmappo" / "group_credit_telemetry.py"
    update_body = trainer.split("def update_policy(", 1)[1]
    call_position = trainer.index("summarize_group_credit_assignment(", trainer.index("for local_update"))
    update_position = trainer.index("train_info = update_policy(", trainer.index("for local_update"))
    return {
        "default_off": "group_credit_telemetry: bool = False" in trainer,
        "positive_interval_guard": "group_credit_telemetry_interval must be positive" in trainer,
        "pre_update_collection": call_position < update_position,
        "condition_group_not_consumed_by_update_policy": "condition_group" not in update_body,
        "no_backward_optimizer_or_zero_grad_in_telemetry_module": no_mutating_calls(telemetry_path),
        "frozen_groups": config["groups"] == ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "group_schema_frozen": len(GROUP_FIELDS) == len(set(GROUP_FIELDS)),
        "conflict_schema_frozen": len(CONFLICT_FIELDS) == len(set(CONFLICT_FIELDS)),
        "seed_is_independent_unit": config["independent_unit"] == "training_seed",
        "mainline_a_untouched": config["mainline_a_modified"] is False,
        "training_not_authorized": config["training_authorized"] is False,
    }


def run_tests() -> dict:
    command = [
        sys.executable, "-m", "pytest", "-q",
        "tests/test_drtp_b5_group_credit_telemetry.py",
        "tests/test_drtp_stable_v2_kl_guard.py",
        "tests/test_tc_sam.py",
        "tests/test_drtp_b5_cross_cohort_atlas.py",
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "pass": completed.returncode == 0,
        "returncode": completed.returncode,
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def dynamic_audit(config: dict) -> dict:
    namespace = runpy.run_path(str(TEST))
    fixture = namespace["fixture"]
    update_policy = namespace["update_policy"]
    make_optimizer = namespace["make_optimizer"]
    np = namespace["np"]
    import copy

    agent, cfg, batch, device = fixture()
    telemetry_start = time.perf_counter()
    group_rows, conflict_rows = summarize_group_credit_assignment(agent, batch, cfg, device, update=1)
    telemetry_seconds = time.perf_counter() - telemetry_start

    update_agent, update_cfg, update_batch, update_device = fixture()
    update_cfg.ppo_epochs = 4
    optimizer = make_optimizer(update_agent, update_cfg)
    update_start = time.perf_counter()
    update_policy(
        update_agent, optimizer, copy.deepcopy(update_batch), update_cfg, update_device, 1,
        minibatch_rng=np.random.default_rng(77),
    )
    ppo_seconds = time.perf_counter() - update_start
    interval = int(config["collection_interval_updates"])
    projected_fraction = telemetry_seconds / max(ppo_seconds, 1e-12) / interval

    numeric_group_fields = [field for field in GROUP_FIELDS if field not in {
        "group", "status", "gradient_objective", "independent_unit", "repetition_unit"
    }]
    finite = True
    for row in group_rows:
        for field in numeric_group_fields:
            value = row[field]
            if value is not None and not math.isfinite(float(value)):
                finite = False
    for row in conflict_rows:
        for field, value in row.items():
            if isinstance(value, float) and not math.isfinite(value):
                finite = False

    with tempfile.TemporaryDirectory(prefix="drtp_b5_credit_csv_") as temporary:
        root = Path(temporary)
        group_path = root / "group.csv"
        conflict_path = root / "conflict.csv"
        for append in (False, True):
            with group_path.open("a" if append else "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=GROUP_FIELDS)
                if not append:
                    writer.writeheader()
                writer.writerows(group_rows)
            with conflict_path.open("a" if append else "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=CONFLICT_FIELDS)
                if not append:
                    writer.writeheader()
                writer.writerows(conflict_rows)
        group_lines = group_path.read_text(encoding="utf-8").splitlines()
        conflict_lines = conflict_path.read_text(encoding="utf-8").splitlines()
        append_resume_exact = (
            group_lines.count(",".join(GROUP_FIELDS)) == 1
            and conflict_lines.count(",".join(CONFLICT_FIELDS)) == 1
            and len(group_lines) == 1 + 2 * len(group_rows)
            and len(conflict_lines) == 1 + 2 * len(conflict_rows)
        )

    return {
        "pass": finite and append_resume_exact,
        "group_rows": len(group_rows),
        "conflict_rows": len(conflict_rows),
        "finite_numeric_values": finite,
        "append_resume_header_exact": append_resume_exact,
        "telemetry_seconds_synthetic": telemetry_seconds,
        "ppo_four_epoch_seconds_synthetic": ppo_seconds,
        "telemetry_to_ppo_ratio_synthetic": telemetry_seconds / max(ppo_seconds, 1e-12),
        "projected_fractional_overhead_at_frozen_interval": projected_fraction,
        "projected_percent_overhead_at_frozen_interval": 100.0 * projected_fraction,
        "benchmark_boundary": "single CPU synthetic fixture; report for engineering planning only, not a cloud runtime guarantee",
    }


def write_outputs(config: dict, result: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "B5_P0_TECHNICAL_AUDIT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    status = result["decision"]
    lines = [
        "# B5-P0 group-conditioned credit telemetry technical audit",
        "",
        f"**Decision:** `{status}`.",
        "",
        "本阶段仅执行本地零训练技术验收；没有启动科学训练、评估 tape 或算法修改。",
        "",
        "| check | status |",
        "|---|---|",
    ]
    lines.extend(f"| {name} | {'PASS' if passed else 'FAIL'} |" for name, passed in result["static_checks"].items())
    lines.extend([
        f"| targeted pytest | {'PASS' if result['tests']['pass'] else 'FAIL'} |",
        f"| dynamic schema / finite / append | {'PASS' if result['dynamic']['pass'] else 'FAIL'} |",
        "",
        "## Performance boundary",
        "",
        f"Synthetic CPU projected overhead at the frozen interval: `{result['dynamic']['projected_percent_overhead_at_frozen_interval']:.2f}%`.",
        "This is an engineering estimate, not a promised cloud runtime. The actual cloud launcher must record measured wall time and disk growth.",
        "",
        "## Statistical boundary",
        "",
        "Training seed is the independent unit. Update×group and update×group-pair rows are repeated technical measurements and cannot be treated as independent n.",
    ])
    (OUT / "B5_P0_TECHNICAL_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dictionary = [
        "# B5 group credit telemetry dictionary",
        "",
        "## Group file: `group_credit_telemetry.csv`",
        "",
        "One row per PPO update × failure group. `status=NO_SAMPLES` is explicit missingness and must not be imputed.",
        "",
        "| field family | meaning |",
        "|---|---|",
        "| return / rollout_value | GAE return target and rollout-time critic prediction |",
        "| value_residual | return target minus rollout-time value prediction |",
        "| td_residual | one-step reward + discounted next value − rollout value |",
        "| raw_advantage | unnormalized GAE advantage |",
        "| normalized_advantage | normalization across the full paired rollout, matching PPO |",
        "| actor_gradient_norm | group PPO policy+entropy gradient norm; diagnostic only |",
        "| critic_gradient_norm | group value-loss gradient norm; diagnostic only |",
        "",
        "## Conflict file: `group_credit_gradient_conflicts.csv`",
        "",
        "One row per observed update × unordered group pair. Negative dot product marks a conflict for that diagnostic objective; it is not itself a mechanism or an independent replicate.",
    ]
    (OUT / "TELEMETRY_DICTIONARY.md").write_text("\n".join(dictionary) + "\n", encoding="utf-8")

    decision = {
        "decision": status,
        "training_started": False,
        "algorithm_modification": False,
        "mainline_a_modified": False,
        "cloud_training_authorized": False,
        "next_action": "prepare frozen cloud observational cohort package for separate human authorization" if "PASS" in status else "repair technical failure only",
    }
    (OUT / "B5_P0_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    readiness = [
        "# B5-P0 readiness",
        "",
        f"Status: `{status}`.",
        "",
        "P0 PASS permits package preparation only. It does not authorize cloud training, a new DRTP variant, or any modification to mainline A.",
    ]
    (OUT / "B5_P0_READINESS.md").write_text("\n".join(readiness) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    checks = static_checks(config)
    tests = run_tests()
    dynamic = dynamic_audit(config)
    passed = all(checks.values()) and tests["pass"] and dynamic["pass"]
    decision = config["decision_if_pass"] if passed else config["decision_if_fail"]
    result = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "static_checks": checks,
        "tests": tests,
        "dynamic": dynamic,
        "large_scale_training_or_evaluation": False,
        "algorithm_modification": False,
        "mainline_a_modified": False,
    }
    write_outputs(config, result)
    print(json.dumps({"decision": decision, "output": str(OUT)}, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
