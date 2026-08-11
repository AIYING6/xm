#!/usr/bin/env bash
# Four independent, semantics-identical development runs share one GPU.  They
# improve small-model device occupancy; no run shares model state or episodes.
set -euo pipefail
ROOT="${1:-results/m2_acquisition_oriented_pilot_cloud}"
PYTHON_BIN="${PYTHON_BIN:-python}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
mkdir -p "${ROOT}"

# The simulator is CPU-bound.  Limiting numerical-library worker pools avoids
# oversubscribing the 16 vCPUs while all four independent pilot jobs run.
pids=()
for spec in "full 9201" "b1 9201" "full 9202" "b1 9202"; do
  read -r method seed <<<"${spec}"
  "${PYTHON_BIN}" -m scripts.run_m2_acquisition_oriented_pilot --device cuda --methods "${method}" --seeds "${seed}" --output-root "${ROOT}/${method}_seed${seed}" > "${ROOT}/${method}_seed${seed}.log" 2>&1 &
  pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do
  wait "${pid}" || status=1
done
if [[ "${status}" -ne 0 ]]; then
  echo "One or more isolated M2 pilot runs failed; aggregation is intentionally skipped." >&2
  exit "${status}"
fi
"${PYTHON_BIN}" -m scripts.finalize_m2_acquisition_oriented_pilot --root "${ROOT}"
