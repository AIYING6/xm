#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/reliable_drtp_ensemble_p1}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "$MAX_PARALLEL" =~ ^[1-9][0-9]*$ && "$MAX_PARALLEL" -le 20 ]] || {
  echo "MAX_PARALLEL must be 1..20" >&2; exit 2;
}
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
[[ $(df -Pk "$ROOT" | awk 'NR==2 {print $4}') -ge 15728640 ]] || {
  echo "need at least 15 GiB free disk" >&2; exit 2;
}

export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight"
cd "$ROOT"
export ROOT OUT PYTHON_BIN

"$PYTHON_BIN" scripts/verify_reliable_drtp_ensemble_p1_preflight.py \
  --output "$OUT/diagnostics/preflight/P1_CLOUD_PREFLIGHT.json"

printf '%s\n' $(
  for arm in e_utr e_drtp; do
    for seed in {4601..4609} {4611..4619}; do
      echo "$arm:$seed"
    done
  done
) | xargs -n1 -P "$MAX_PARALLEL" bash -c '
  item="$1"; arm="${item%%:*}"; seed="${item##*:}"
  "$PYTHON_BIN" "$ROOT/scripts/run_reliable_drtp_ensemble_p1.py" train \
    --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
    >"$OUT/launcher_logs/${arm}_seed${seed}.out" \
    2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
' _

"$PYTHON_BIN" scripts/run_reliable_drtp_ensemble_p1.py evaluate \
  --output-root "$OUT" --workers "$MAX_PARALLEL" --execute
"$PYTHON_BIN" scripts/run_reliable_drtp_ensemble_p1.py aggregate \
  --output-root "$OUT" --execute

tar -czf "$ROOT/reliable_drtp_ensemble_p1_05m_results.tar.gz" \
  -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/reliable_drtp_ensemble_p1_05m_results.tar.gz" \
  > "$ROOT/reliable_drtp_ensemble_p1_05m_results.tar.gz.sha256"
echo "Reliable-DRTP ensemble P1 complete; no continuation or distillation started."
