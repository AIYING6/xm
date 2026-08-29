#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; OUT="${OUTPUT_ROOT:-$ROOT/results/development/pp_drtp_p3_pilot}"; PYTHON_BIN="${PYTHON_BIN:-python}"; MAX_PARALLEL="${MAX_PARALLEL:-9}"
[[ "$MAX_PARALLEL" == "9" ]] || { echo 'P3 freezes exactly nine concurrent trajectories' >&2; exit 2; }; [[ ! -e "$OUT" ]] || { echo "refusing existing output: $OUT" >&2; exit 2; }
[[ "$(df -Pk "$ROOT"|awk 'NR==2{print $4}')" -ge 15728640 ]] || { echo 'need 15 GiB free' >&2; exit 2; }
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"; cd "$ROOT"; mkdir -p "$OUT/launcher_logs"
export ROOT OUT PYTHON_BIN
"$PYTHON_BIN" -m pytest -q tests/test_pp_drtp_sampler.py
"$PYTHON_BIN" scripts/run_pp_drtp_p2_technical_audit.py --output "$OUT/P2_REAUDIT.json"
printf '%s\n' utr_sg:3401 utr_sg:3402 utr_sg:3403 drtp_sg:3401 drtp_sg:3402 drtp_sg:3403 pp_drtp_sg:3401 pp_drtp_sg:3402 pp_drtp_sg:3403 | xargs -n 1 -P 9 bash -c 's="$1"; a="${s%%:*}"; z="${s##*:}"; "$PYTHON_BIN" scripts/run_pp_drtp_p3_single.py --arm "$a" --seed "$z" --output-root "$OUT" --execute >"$OUT/launcher_logs/${a}_seed${z}.out" 2>"$OUT/launcher_logs/${a}_seed${z}.err"' _ || { echo 'training failed; no evaluation' >&2; exit 3; }
echo 'Training complete. Evaluation and frozen gate are intentionally separate, requiring no new training.'
