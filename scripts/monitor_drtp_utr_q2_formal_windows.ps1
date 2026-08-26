param([string]$OutputRoot = "results/formal/drtp_utr_q2_paired_5seed")

Set-Location (Split-Path -Parent $PSScriptRoot)
$target = 39063
$total = 0
Write-Output "=== ten training trajectories ==="
foreach ($arm in @("utr_sg", "drtp_sg")) {
    foreach ($seed in @(2301, 2302, 2303, 2304, 2305)) {
        $log = Join-Path $OutputRoot "runs/$arm/seed$seed/train_log.csv"
        if (Test-Path -LiteralPath $log) {
            $last = Import-Csv -LiteralPath $log | Where-Object { $_.update -match '^\d+$' } | Select-Object -Last 1
            $update = if ($null -eq $last) { 0 } else { [int]$last.update }
            $total += $update
            "{0,-7} seed{1}: {2}/{3} ({4:N2}%)" -f $arm, $seed, $update, $target, (100 * $update / $target)
        } else {
            "{0,-7} seed{1}: not started" -f $arm, $seed
        }
    }
}
"overall training: {0}/{1} updates ({2:N2}%)" -f $total, (10 * $target), (100 * $total / (10 * $target))

Write-Output "`n=== controller ==="
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'launch_drtp_utr_q2_formal_windows|run_drtp_utr_q2_formal_single|run_drtp_utr_q2_formal_evaluation'
} | Select-Object ProcessId, Name, CommandLine

$status = Join-Path $OutputRoot "windows_controller_status.json"
if (Test-Path -LiteralPath $status) {
    Write-Output "`n=== stage status ==="
    Get-Content -LiteralPath $status
}

$evalLog = Join-Path $OutputRoot "formal_evaluation.out"
if (Test-Path -LiteralPath $evalLog) {
    Write-Output "`n=== evaluation ==="
    Select-String -LiteralPath $evalLog -Pattern 'formal evaluation progress' | Select-Object -Last 1
}
