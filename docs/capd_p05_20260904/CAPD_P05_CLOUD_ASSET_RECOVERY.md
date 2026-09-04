# CAPD P0.5 cloud asset recovery

This recovery step copies existing UTR/EGTR training artifacts only. It does not train, evaluate, select checkpoints by return, or include an evaluation tape.

Run on the original AutoDL instance (or any instance with its original data disk mounted):

```bash
cd /root/autodl-tmp/egtr_double_cohort_simultaneous_20260903

ROOT=results/development/egtr_double_cohort_simultaneous
LIST=capd_p05_teacher_assets.list
PKG=capd_p05_teacher_assets_10m.tar.gz

: > "$LIST"

for arm in utr_sg egtr_sg; do
  for seed in 71011 71012 71013 71014 71015 71021 71022 71023 71024 71025; do
    run="$ROOT/runs/$arm/seed$seed"
    test -f "$run/actor_critic_latest.pt" || { echo "MISSING $run/actor_critic_latest.pt"; exit 1; }
    test -f "$run/run_manifest.json" || { echo "MISSING $run/run_manifest.json"; exit 1; }

    printf '%s\n' "$run/actor_critic_latest.pt" "$run/run_manifest.json" >> "$LIST"

    for name in \
      actor_critic_runtime_state_latest.pt \
      actor_critic_training_state_latest.pt \
      drtp_topology_sampler_manifest.json \
      drtp_topology_sampler_log.csv \
      train_log.csv; do
      test ! -f "$run/$name" || printf '%s\n' "$run/$name" >> "$LIST"
    done
  done
done

sort -u -o "$LIST" "$LIST"
test "$(grep -c '/actor_critic_latest.pt$' "$LIST")" -eq 20
test "$(grep -c '/run_manifest.json$' "$LIST")" -eq 20

sha256sum $(cat "$LIST") > capd_p05_teacher_assets.sha256
tar -czf "$PKG" -T "$LIST" capd_p05_teacher_assets.sha256
sha256sum "$PKG" > "${PKG}.sha256"

ls -lh "$PKG" "${PKG}.sha256"
```

Download both `capd_p05_teacher_assets_10m.tar.gz` and `capd_p05_teacher_assets_10m.tar.gz.sha256`.

If the original AutoDL data disk is no longer available, search local downloads for `egtr_double_cohort_simultaneous_10m_results.tar.gz`. Its presence may avoid retraining. Do not substitute execution ZIP files: they contain source code and launch contracts, not completed 10M teacher checkpoints.

After extraction, rerun:

```bash
python scripts/audit_capd_p05_asset_inventory.py \
  --search-root /path/to/extracted/assets \
  --output-dir /path/to/new/inventory/output \
  --execute
```

Only `CAPD_P05_ASSETS_READY_FOR_SIGNAL_AUDIT` permits the next, still zero-training, signal audit. `CAPD_P05_BLOCKED_ASSETS_NOT_LOCAL` is not a scientific NO-GO.
