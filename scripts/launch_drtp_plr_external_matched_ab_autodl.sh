#!/usr/bin/env bash
# Computes only the missing PLR comparator.  UTR/DRTP are extracted, verified, and reused.
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"; OUTPUT_ROOT="${OUTPUT_ROOT:-results/final_evidence/drtp_plr_external_matched_ab}"; MAX_PARALLEL="${MAX_PARALLEL:-20}"; CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-20}"
ARCHIVE_A="${ARCHIVE_A:?ARCHIVE_A must name the frozen A complete-results tar.gz}"; ARCHIVE_B="${ARCHIVE_B:?ARCHIVE_B must name the frozen B complete-results tar.gz}"
[[ "$MAX_PARALLEL" =~ ^[0-9]+$ && "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 20 ]] || { echo 'MAX_PARALLEL must be 1..20' >&2; exit 2; }
[[ -f "$ARCHIVE_A" && -f "$ARCHIVE_B" ]] || { echo 'A/B frozen result archives missing' >&2; exit 2; }
[[ ! -e "$OUTPUT_ROOT/cohorts" ]] || { echo "refusing to overwrite $OUTPUT_ROOT/cohorts" >&2; exit 2; }
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$((CPU_THREADS_TOTAL/MAX_PARALLEL))}"; [[ "$OMP_NUM_THREADS" -ge 1 ]] || export OMP_NUM_THREADS=1; export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}" OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}" NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT/baselines/A" "$OUTPUT_ROOT/baselines/B" "$OUTPUT_ROOT/launcher_logs"
tar -xzf "$ARCHIVE_A" -C "$OUTPUT_ROOT/baselines/A"; tar -xzf "$ARCHIVE_B" -C "$OUTPUT_ROOT/baselines/B"
for c in A B; do n=$(find "$OUTPUT_ROOT/baselines/$c" -path '*runs/utr_sg/seed*/actor_critic_latest.pt' -type f | wc -l); d=$(find "$OUTPUT_ROOT/baselines/$c" -path '*runs/drtp_sg/seed*/actor_critic_latest.pt' -type f | wc -l); [[ "$n" -eq 5 && "$d" -eq 5 ]] || { echo "invalid frozen $c baseline assets: UTR=$n DRTP=$d" >&2; exit 2; }; "$PYTHON_BIN" scripts/create_drtp_plr_matched_ab_tape.py --cohort "$c" --output-root "$OUTPUT_ROOT/cohorts/$c/tape"; done
train_one(){ "$PYTHON_BIN" scripts/run_drtp_plr_matched_ab_single.py --cohort "$1" --seed "$2" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/launcher_logs/train_${1}_seed${2}.out" 2> "$OUTPUT_ROOT/launcher_logs/train_${1}_seed${2}.err"; }
for c in A B; do if [[ "$c" == A ]]; then seeds=(78011 78012 78013 78014 78015); else seeds=(78021 78022 78023 78024 78025); fi; for s in "${seeds[@]}"; do while [[ "$(jobs -rp|wc -l)" -ge "$MAX_PARALLEL" ]]; do wait -n; done; train_one "$c" "$s" & done; done; wait
printf '{"status":"PLR_MATCHED_AB_TRAINING_COMPLETE","new_plr_trajectories":10,"UTR_retrained":false,"DRTP_retrained":false,"evaluation_started":false}\n' > "$OUTPUT_ROOT/PLR_MATCHED_AB_TRAINING_COMPLETE.json"
for c in A B; do "$PYTHON_BIN" scripts/run_drtp_plr_matched_ab_evaluation.py --cohort "$c" --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/cohorts/$c/evaluations/final_10m" --workers "$MAX_PARALLEL" --execute; done
"$PYTHON_BIN" scripts/aggregate_drtp_plr_matched_ab.py --output-root "$OUTPUT_ROOT" --baseline-a-root "$OUTPUT_ROOT/baselines/A" --baseline-b-root "$OUTPUT_ROOT/baselines/B" --execute
printf '{"status":"PLR_MATCHED_AB_COMPLETE","new_plr_trajectories":10,"A_B_separate":true,"UTR_retrained":false,"DRTP_retrained":false,"automatic_algorithm_revision":false}\n' > "$OUTPUT_ROOT/PLR_MATCHED_AB_COMPLETE.json"
