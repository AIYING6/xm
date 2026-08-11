#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-results/m2r_identity_preserving_pilot_cloud}"; PYTHON_BIN="${PYTHON_BIN:-python}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}" OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
mkdir -p "$ROOT"; pids=()
for spec in "full 9601" "b1 9601" "full 9602" "b1 9602"; do
 read -r method seed <<<"$spec"
 "$PYTHON_BIN" -m scripts.run_m2r_acquisition_residual_pilot --device cuda --methods "$method" --seeds "$seed" --output-root "$ROOT/${method}_seed${seed}" > "$ROOT/${method}_seed${seed}.log" 2>&1 & pids+=("$!")
done
status=0; for pid in "${pids[@]}"; do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"
"$PYTHON_BIN" -m scripts.finalize_m2r_acquisition_residual_pilot --root "$ROOT"
