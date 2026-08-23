#!/usr/bin/env bash
set -u

OUTPUT_ROOT="${OUTPUT_ROOT:-results/formal/drtp_utr_q2_paired_5seed}"
target=39063
total=0
found=0

echo "=== ten training trajectories ==="
for arm in utr_sg drtp_sg; do
  for seed in 2301 2302 2303 2304 2305; do
    log="$OUTPUT_ROOT/runs/$arm/seed$seed/train_log.csv"
    if [[ -s "$log" ]]; then
      update=$(awk -F, 'NR>1 && $1 ~ /^[0-9]+$/ {u=$1} END {print u+0}' "$log")
      total=$((total + update))
      found=$((found + 1))
      awk -v a="$arm" -v s="$seed" -v u="$update" -v t="$target" \
        'BEGIN {printf "%-7s seed%s: %d/%d (%.2f%%)\n", a, s, u, t, 100*u/t}'
    else
      printf "%-7s seed%s: not started\n" "$arm" "$seed"
    fi
  done
done
awk -v u="$total" -v t="$((10 * target))" \
  'BEGIN {printf "overall training: %d/%d updates (%.2f%%)\n", u, t, 100*u/t}'

echo
echo "=== active stage ==="
pgrep -af 'run_drtp_utr_q2_formal_single|run_drtp_utr_q2_formal_evaluation|aggregate_drtp_utr_q2_formal' \
  || echo "no formal training/evaluation/aggregation process"

echo
echo "=== evaluation ==="
eval_log="$OUTPUT_ROOT/formal_evaluation.out"
if [[ -f "$eval_log" ]]; then
  line=$(grep 'formal evaluation progress' "$eval_log" | tail -n 1 || true)
  if [[ -n "$line" ]]; then
    echo "$line"
  else
    echo "evaluation log exists; no progress row yet"
  fi
else
  echo "evaluation not started"
fi

decision="$OUTPUT_ROOT/evaluations/final_10m/DRTP_UTR_Q2_FORMAL_DECISION.json"
if [[ -f "$decision" ]]; then
  echo
  echo "=== final decision ==="
  python -m json.tool "$decision" | grep -E '"verdict"|"catastrophic_seed_count"'
fi
