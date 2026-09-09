#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/epistemic_commitment_p2_pilot}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"

methods=(information_set_commitment capacity_and_risk_matched_recurrent)
seeds=(98101 98102 98103)

"$PYTHON_BIN" scripts/verify_epistemic_commitment_p2_preflight.py \
  --output-root "$OUTPUT_ROOT" --execute

running=0
for method in "${methods[@]}"; do
  for seed in "${seeds[@]}"; do
    "$PYTHON_BIN" scripts/run_epistemic_commitment_p2_pilot.py train \
      --method "$method" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute &
    running=$((running + 1))
    if (( running >= MAX_PARALLEL )); then
      wait -n
      running=$((running - 1))
    fi
  done
done
wait

for method in "${methods[@]}"; do
  for seed in "${seeds[@]}"; do
    "$PYTHON_BIN" scripts/run_epistemic_commitment_p2_pilot.py evaluate \
      --method "$method" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute &
  done
done
wait

"$PYTHON_BIN" scripts/run_epistemic_commitment_p2_pilot.py aggregate \
  --output-root "$OUTPUT_ROOT" --execute

"$PYTHON_BIN" - "$OUTPUT_ROOT" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
report = json.loads((root / "diagnostics/p2_pilot_final/P2_PILOT_REPORT.json").read_text())
complete = {
    "protocol": "EPISTEMIC-COMMITMENT-P2-PILOT-COMPLETE-V1",
    "status": "completed",
    "trajectories": 6,
    "evaluations": 6,
    "verdict": report["verdict"],
    "automatic_continuation": False,
}
(root / "P2_PILOT_COMPLETE.json").write_text(
    json.dumps(complete, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(complete, indent=2))
PY
