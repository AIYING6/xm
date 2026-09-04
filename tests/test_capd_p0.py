from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_capd_p0.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_capd_p0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_consensus_is_simplex_and_continuous():
    module = load_module()
    anchor = [0.6, 0.3, 0.1]
    close = [[0.2, 0.7, 0.1], [0.21, 0.69, 0.1], [0.19, 0.71, 0.1]]
    split = [[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]]
    target_close, div_close, confidence_close, _ = module.consensus_target(anchor, close, 0.1)
    target_split, div_split, confidence_split, _ = module.consensus_target(anchor, split, 0.1)
    assert abs(sum(target_close) - 1.0) < 1e-12
    assert abs(sum(target_split) - 1.0) < 1e-12
    assert div_split > div_close
    assert confidence_split < confidence_close


def test_audit_generates_zero_training_verdict(tmp_path: Path):
    output = tmp_path / "audit"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", str(output), "--execute"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads((output / "CAPD_P0_RESULT.json").read_text(encoding="utf-8"))
    assert payload["verdict"] == "CAPD_P0_FEASIBLE_FOR_P05_ASSET_SIGNAL_AUDIT"
    assert payload["environment_steps"] == 0
    assert payload["ppo_updates"] == 0
    assert payload["evaluation_started"] is False
    assert payload["implementation_authorized"] is False
    assert "CAPD_P0_FEASIBLE" in completed.stdout
