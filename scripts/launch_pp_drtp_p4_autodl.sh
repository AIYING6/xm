#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/pp_drtp_p4_validation}"
PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
[[ "$MAX_PARALLEL" == "15" ]] || { echo 'P4 freezes exactly fifteen concurrent trajectories' >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output: $OUT" >&2; exit 2; }
[[ "$(df -Pk "$ROOT" | awk 'NR==2{print $4}')" -ge 20971520 ]] || { echo 'need 20 GiB free' >&2; exit 2; }
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
cd "$ROOT"
mkdir -p "$OUT/launcher_logs"
export ROOT OUT PYTHON_BIN
"$PYTHON_BIN" -m pytest -q tests/test_pp_drtp_sampler.py
"$PYTHON_BIN" scripts/run_pp_drtp_p2_technical_audit.py --output "$OUT/P2_REAUDIT.json"
printf '%s\n' utr_sg:3501 utr_sg:3502 utr_sg:3503 utr_sg:3504 utr_sg:3505 drtp_sg:3501 drtp_sg:3502 drtp_sg:3503 drtp_sg:3504 drtp_sg:3505 pp_drtp_sg:3501 pp_drtp_sg:3502 pp_drtp_sg:3503 pp_drtp_sg:3504 pp_drtp_sg:3505 | xargs -n 1 -P 15 bash -c 's="$1"; a="${s%%:*}"; z="${s##*:}"; "$PYTHON_BIN" scripts/run_pp_drtp_p4_single.py --arm "$a" --seed "$z" --output-root "$OUT" --execute >"$OUT/launcher_logs/${a}_seed${z}.out" 2>"$OUT/launcher_logs/${a}_seed${z}.err"' _ || { echo 'training failed; no evaluation' >&2; exit 3; }
"$PYTHON_BIN" scripts/run_pp_drtp_p4_evaluation.py --output-root "$OUT" --workers 15 --execute
"$PYTHON_BIN" scripts/aggregate_pp_drtp_p4.py --output-root "$OUT" --execute
tar -czf "$ROOT/pp_drtp_p4_validation_05m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/pp_drtp_p4_validation_05m_results.tar.gz" > "$ROOT/pp_drtp_p4_validation_05m_results.tar.gz.sha256"
echo 'PP-DRTP P4 complete; no continuation was started.'
