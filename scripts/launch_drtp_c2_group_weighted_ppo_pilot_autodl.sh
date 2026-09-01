#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_c2_group_weighted_ppo_pilot}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "$MAX_PARALLEL" =~ ^[1-9][0-9]*$ && "$MAX_PARALLEL" -le 30 ]] || { echo "MAX_PARALLEL must be 1..30" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }

export PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight"
cd "$ROOT"
export ROOT OUT PYTHON_BIN

"$PYTHON_BIN" scripts/verify_drtp_c2_group_weighted_ppo_pilot_preflight.py --output "$OUT/diagnostics/preflight/C2_CLOUD_PREFLIGHT.json"

printf '%s\n' $(
  for arm in utr_sg drtp_sg group_weighted_utr_sg; do
    for seed in {4801..4810}; do echo "$arm:$seed"; done
  done
) | xargs -n1 -P "$MAX_PARALLEL" bash -c '
  item="$1"; arm="${item%%:*}"; seed="${item##*:}"
  "$PYTHON_BIN" "$ROOT/scripts/run_drtp_c2_group_weighted_ppo_pilot.py" train \
    --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
    >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
' _

"$PYTHON_BIN" scripts/run_drtp_c2_group_weighted_ppo_pilot.py evaluate --output-root "$OUT" --workers "$MAX_PARALLEL" --execute
"$PYTHON_BIN" scripts/run_drtp_c2_group_weighted_ppo_pilot.py aggregate --output-root "$OUT" --execute

tar -czf "$ROOT/drtp_c2_group_weighted_ppo_pilot_05m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_c2_group_weighted_ppo_pilot_05m_results.tar.gz" > "$ROOT/drtp_c2_group_weighted_ppo_pilot_05m_results.tar.gz.sha256"
echo "C2 complete; no continuation, tuning, or new candidate started."
