$py = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$methods = @("ea_rg_mappo", "single_graph", "mappo", "happo")
$seeds = @(1, 2)
$TARGET = 3907

while ($true) {
  Write-Host "=== Round start ==="
  & $py scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 1 2

  $allDone = $true

  foreach ($method in $methods) {
    foreach ($seed in $seeds) {
      Write-Host "=== $method seed=$seed ==="
      & $py scripts/run_manifest_training_chunk.py `
        --method $method `
        --seed $seed `
        --chunk-updates 500 `
        --target-updates $TARGET `
        --python-exe $py

      if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $method seed=$seed failed with code $LASTEXITCODE"
      }
    }
  }

  $progress = & $py scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 1 2
  Write-Host $progress

  if ($progress -match "complete=False") {
    $allDone = $false
  }

  if ($allDone) {
    Write-Host "All seeds complete!"
    break
  }

  Write-Host "=== Round complete, starting next round ==="
}

Write-Host "=== Running audit ==="
& $py scripts/audit_training_outputs.py `
  --mode dev_1m `
  --methods ea_rg_mappo single_graph mappo happo `
  --seeds 1 2 `
  --min-update $TARGET

Write-Host "=== Generating summary ==="
& $py scripts/summarize_training_logs.py `
  --mode dev_1m `
  --methods ea_rg_mappo single_graph mappo happo `
  --seeds 1 2 `
  --out-csv results/dev1m_seed12_3907update_summary.csv

Write-Host "=== Final check ==="
& $py scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 1 2

Write-Host "ALL DONE"
