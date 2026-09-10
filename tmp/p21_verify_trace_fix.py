#!/usr/bin/env python3
"""Verify the P21 oracle_trace fix: the greedy forward rollout must now match the DP."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diag_p21_timing_gap import oracle_trace, classify, FOCUS_BAND  # noqa: E402
from p18_train_coupled_policy import oracle_dp  # noqa: E402

cfg = json.loads((ROOT / "configs" / "p18_attitude_coupled_learning_20260910.json").read_text(encoding="utf-8"))

print(f"{'sep':>5} {'DP':>5} {'trace_delivered':>16} {'match':>6}   oracle fingerprint")
ok = True
for sep in FOCUS_BAND:
    rows = oracle_trace(float(sep), cfg)
    got = int(sum(r[5] for r in rows))
    dp = int(oracle_dp(sep, cfg))
    match = got == dp
    ok &= match
    print(f"{sep:>5} {dp:>5} {got:>16} {str(match):>6}   {classify(rows)}")
print("\nALL MATCH" if ok else "\nSTILL MISMATCHED - trace is still not usable as evidence")
