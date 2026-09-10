#!/usr/bin/env python3
"""Patch the P21 artifact: regenerate ONLY the oracle trace side.

The run that produced P21_DIAG_RESULT.json used an oracle_trace that replayed with the
full-horizon value table at every step, so its oracle fingerprints read TGT_ONLY=60 and
delivered=0, contradicting the script's own DP numbers (42/34/20/9).  The bug is fixed
in scripts/diag_p21_timing_gap.py; the learned side of the traces was produced by a real
env rollout and is unaffected, so only the oracle half is recomputed here.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diag_p21_timing_gap import oracle_trace, classify  # noqa: E402
from p18_train_coupled_policy import oracle_dp  # noqa: E402

ART = ROOT / "artifacts" / "diagnostics" / "p21_timing_gap_diag_20260910" / "P21_DIAG_RESULT.json"
cfg = json.loads((ROOT / "configs" / "p18_attitude_coupled_learning_20260910.json").read_text(encoding="utf-8"))

out = json.loads(ART.read_text(encoding="utf-8"))
traces = out["variants"]["base_h64_u600"].get("traces", {})
patched = []
for sep_str in traces:
    sep = float(sep_str)
    rows = oracle_trace(sep, cfg)
    got = int(sum(r[5] for r in rows))
    dp = int(oracle_dp(sep, cfg))
    if got != dp:
        raise SystemExit(f"refusing to patch: sep {sep} trace {got} != DP {dp}")
    traces[sep_str]["oracle"] = classify(rows)
    traces[sep_str]["oracle_delivered"] = got
    patched.append(sep_str)

out["trace_patch"] = {
    "reason": "oracle_trace replayed with the full-horizon value table at every step",
    "effect": "oracle fingerprints read TGT_ONLY=60 / delivered=0, contradicting the DP column",
    "fix": "keep every intermediate value table V_k and replay step t against V[horizon-1-t]",
    "verified": "trace delivered == DP delivered for 110/120/130/140",
    "recomputed_fields": ["variants.base_h64_u600.traces[*].oracle", "*.oracle_delivered"],
    "untouched_fields": ["variants.base_h64_u600.traces[*].learned (independent env rollout)"],
    "patched_separations": patched,
}
ART.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print("patched", ART)
for s in patched:
    print(f"  sep {s}: learnwork learned={traces[s]['learned']} | oracle={traces[s]['oracle']} "
          f"delivered={traces[s]['oracle_delivered']}")
