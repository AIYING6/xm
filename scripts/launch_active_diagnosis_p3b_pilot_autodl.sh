#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/active_diagnosis_p3b_pilot}"
PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
RUNNER="scripts/run_active_diagnosis_p3b_pilot.py"
SEEDS=(83011 83012 83013)
ARMS=(recurrent_mappo entropy_probe decision_relevant_probe)

mkdir -p "$OUTPUT_ROOT/logs"
"$PYTHON_BIN" scripts/audit_active_diagnosis_p3b_integrated_runner.py \
  --output "$OUTPUT_ROOT/P3B_INTEGRATED_RUNNER_AUDIT.json" \
  > "$OUTPUT_ROOT/logs/integrated_runner_audit.out" \
  2> "$OUTPUT_ROOT/logs/integrated_runner_audit.err"
"$PYTHON_BIN" "$RUNNER" preflight --output-root "$OUTPUT_ROOT" \
  > "$OUTPUT_ROOT/P3B_PREFLIGHT.json"

run_batch() {
  local -a pids=()
  local running=0
  while (($#)); do
    bash -lc "$1" &
    pids+=("$!")
    running=$((running + 1))
    shift
    if ((running >= MAX_PARALLEL)); then
      for pid in "${pids[@]}"; do wait "$pid"; done
      pids=(); running=0
    fi
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
}

commands=()
for seed in "${SEEDS[@]}"; do
  commands+=("OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 '$PYTHON_BIN' '$RUNNER' prefix --seed '$seed' --output-root '$OUTPUT_ROOT' --execute > '$OUTPUT_ROOT/logs/prefix_seed${seed}.out' 2> '$OUTPUT_ROOT/logs/prefix_seed${seed}.err'")
done
run_batch "${commands[@]}"

commands=()
for seed in "${SEEDS[@]}"; do
  commands+=("OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 '$PYTHON_BIN' '$RUNNER' calibrate --seed '$seed' --output-root '$OUTPUT_ROOT' --execute > '$OUTPUT_ROOT/logs/calibrate_seed${seed}.out' 2> '$OUTPUT_ROOT/logs/calibrate_seed${seed}.err'")
done
run_batch "${commands[@]}"

if ! "$PYTHON_BIN" - "$OUTPUT_ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
reports = [json.loads((root / "calibration" / f"seed{s}" / "calibration_report.json").read_text()) for s in (83011, 83012, 83013)]
passed = all(report["arm_specific_training_authorized"] for report in reports)
(root / "P3B_CALIBRATION_GATE.json").write_text(json.dumps({
    "verdict": "P3B_CALIBRATION_PASS" if passed else "P3B_CALIBRATION_STOP",
    "seed_verdicts": {str(seed): report["quality_verdict"] for seed, report in zip((83011, 83012, 83013), reports)},
    "arm_specific_training_started": False,
}, indent=2) + "\n")
raise SystemExit(0 if passed else 4)
PY
then
  echo "Calibration quality stop: arm-specific training and evaluation were not started."
  exit 0
fi

commands=()
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    commands+=("OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 '$PYTHON_BIN' '$RUNNER' train-arm --arm '$arm' --seed '$seed' --output-root '$OUTPUT_ROOT' --execute > '$OUTPUT_ROOT/logs/train_${arm}_seed${seed}.out' 2> '$OUTPUT_ROOT/logs/train_${arm}_seed${seed}.err'")
  done
done
run_batch "${commands[@]}"

commands=()
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    commands+=("OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 '$PYTHON_BIN' '$RUNNER' evaluate --arm '$arm' --seed '$seed' --output-root '$OUTPUT_ROOT' --execute > '$OUTPUT_ROOT/logs/eval_${arm}_seed${seed}.out' 2> '$OUTPUT_ROOT/logs/eval_${arm}_seed${seed}.err'")
  done
done
run_batch "${commands[@]}"

"$PYTHON_BIN" "$RUNNER" aggregate --output-root "$OUTPUT_ROOT" --execute
"$PYTHON_BIN" - "$OUTPUT_ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
(root / "P3B_PILOT_COMPLETE.json").write_text(json.dumps({
    "status": "ACTIVE_DIAGNOSIS_P3B_PILOT_COMPLETE",
    "training_seeds": [83011, 83012, 83013],
    "arms": ["recurrent_mappo", "entropy_probe", "decision_relevant_probe"],
    "fixed_endpoint_evaluation": True,
    "automatic_algorithm_revision": False,
}, indent=2) + "\n")
PY
