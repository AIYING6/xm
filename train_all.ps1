$PY="D:/Anaconda/envs/.conda/envs/cac/python.exe"
$METHODS=@("ea_rg_mappo","single_graph","mappo","happo")
$TARGET=3907

while ($true) {
  & $PY scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0

  $allDone = $true

  foreach ($m in $METHODS) {
    & $PY scripts/run_manifest_training_chunk.py `
      --method $m `
      --seed 0 `
      --chunk-updates 100 `
      --target-updates $TARGET `
      --python-exe $PY

    if ($LASTEXITCODE -ne 0) {
      Write-Host "Training failed for method: $m"
      exit 1
    }
  }

  $progress = & $PY scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0
  Write-Host $progress

  if ($progress -match "complete=False") {
    $allDone = $false
  }

  if ($allDone) {
    break
  }
}

& $PY scripts/audit_training_outputs.py `
  --mode dev_1m `
  --methods ea_rg_mappo single_graph mappo happo `
  --seeds 0 `
  --min-update $TARGET

& $PY scripts/summarize_training_logs.py `
  --mode dev_1m `
  --methods ea_rg_mappo single_graph mappo happo `
  --seeds 0 `
  --out-csv results/dev1m_seed0_3907update_summary.csv

& $PY scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0
