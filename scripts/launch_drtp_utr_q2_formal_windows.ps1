param(
    [string]$PythonBin = "D:/Anaconda/envs/.conda/envs/cac/python.exe",
    [string]$OutputRoot = "results/formal/drtp_utr_q2_paired_5seed",
    [int]$MaxParallel = 2,
    [int]$EvalWorkers = 2
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if ($MaxParallel -lt 1 -or $EvalWorkers -lt 1) {
    throw "MaxParallel and EvalWorkers must be positive"
}
if (-not (Test-Path -LiteralPath $PythonBin)) {
    throw "Python runtime not found: $PythonBin"
}
if ((Test-Path -LiteralPath $OutputRoot) -and
    (Get-ChildItem -LiteralPath $OutputRoot -Force -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    throw "Refusing to overwrite non-empty output root: $OutputRoot"
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$env:CUDA_VISIBLE_DEVICES = "0"
$env:OMP_NUM_THREADS = [string][Math]::Max(1, [Math]::Floor([Environment]::ProcessorCount / $MaxParallel))
$env:MKL_NUM_THREADS = $env:OMP_NUM_THREADS
$statusPath = Join-Path $OutputRoot "windows_controller_status.json"

function Write-Status([string]$Stage, [string]$Status, [hashtable]$Extra = @{}) {
    $payload = [ordered]@{
        protocol = "DRTP-UTR-Q2-FORMAL-WINDOWS-CONTROLLER-V1"
        stage = $Stage
        status = $Status
        timestamp = (Get-Date).ToString("o")
        max_parallel = $MaxParallel
        eval_workers = $EvalWorkers
    }
    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
}

function Invoke-LoggedPython([string[]]$Arguments, [string]$Stdout, [string]$Stderr) {
    & $PythonBin @Arguments 1> $Stdout 2> $Stderr
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "Python stage failed with exit code $code; see $Stderr"
    }
}

try {
    Write-Status "preflight" "running"
    Invoke-LoggedPython @(
        "scripts/verify_drtp_utr_q2_formal_contract.py", "--output",
        (Join-Path $OutputRoot "formal_preflight.json")
    ) (Join-Path $OutputRoot "formal_preflight.out") (Join-Path $OutputRoot "formal_preflight.err")

    Invoke-LoggedPython @(
        "scripts/create_drtp_utr_q2_formal_tape.py", "--output-root", $OutputRoot, "--execute"
    ) (Join-Path $OutputRoot "tape_creation.out") (Join-Path $OutputRoot "tape_creation.err")

    Write-Status "training" "running" @{ completed_runs = 0; total_runs = 10 }
    $queue = [System.Collections.Generic.Queue[object]]::new()
    foreach ($arm in @("utr_sg", "drtp_sg")) {
        foreach ($seed in @(2301, 2302, 2303, 2304, 2305)) {
            $queue.Enqueue([pscustomobject]@{ Arm = $arm; Seed = $seed })
        }
    }
    $active = @()
    $completed = 0
    while ($queue.Count -gt 0 -or $active.Count -gt 0) {
        while ($queue.Count -gt 0 -and $active.Count -lt $MaxParallel) {
            $item = $queue.Dequeue()
            $stdout = Join-Path $OutputRoot "$($item.Arm)_$($item.Seed).out"
            $stderr = Join-Path $OutputRoot "$($item.Arm)_$($item.Seed).err"
            $arguments = @(
                "scripts/run_drtp_utr_q2_formal_single.py", "--arm", $item.Arm,
                "--seed", [string]$item.Seed, "--output-root", $OutputRoot, "--execute"
            )
            $process = Start-Process -FilePath $PythonBin -ArgumentList $arguments `
                -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
                -WindowStyle Hidden -PassThru
            $active += [pscustomobject]@{
                Process = $process; Arm = $item.Arm; Seed = $item.Seed; ErrorLog = $stderr
            }
        }
        Start-Sleep -Seconds 5
        $remaining = @()
        foreach ($job in $active) {
            if ($job.Process.HasExited) {
                $job.Process.Refresh()
                $manifest = Join-Path $OutputRoot "runs/$($job.Arm)/seed$($job.Seed)/run_manifest.json"
                $completedManifest = $false
                if (Test-Path -LiteralPath $manifest) {
                    try {
                        $completedManifest = ((Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).status -eq "completed")
                    } catch {
                        $completedManifest = $false
                    }
                }
                if ($job.Process.ExitCode -ne 0 -or -not $completedManifest) {
                    throw "$($job.Arm)/seed$($job.Seed) failed; see $($job.ErrorLog)"
                }
                $completed += 1
                Write-Status "training" "running" @{ completed_runs = $completed; total_runs = 10 }
            } else {
                $remaining += $job
            }
        }
        $active = $remaining
    }

    Write-Status "evaluation" "running" @{ completed_runs = 10; total_runs = 10 }
    Invoke-LoggedPython @(
        "scripts/run_drtp_utr_q2_formal_evaluation.py", "--output-root", $OutputRoot,
        "--workers", [string]$EvalWorkers, "--gpu-ids", "0", "--execute"
    ) (Join-Path $OutputRoot "formal_evaluation.out") (Join-Path $OutputRoot "formal_evaluation.err")

    Write-Status "aggregation" "running"
    Invoke-LoggedPython @(
        "scripts/aggregate_drtp_utr_q2_formal.py", "--results-root", $OutputRoot,
        "--report-path", (Join-Path $OutputRoot "DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_REPORT.md")
    ) (Join-Path $OutputRoot "formal_aggregate.out") (Join-Path $OutputRoot "formal_aggregate.err")

    $archive = "$OutputRoot.tar.gz"
    & tar.exe -czf $archive $OutputRoot
    if ($LASTEXITCODE -ne 0) { throw "result archive failed" }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    "$hash  $archive" | Set-Content -LiteralPath "$archive.sha256" -Encoding ASCII
    Write-Status "complete" "completed" @{ archive = $archive; archive_sha256 = $hash }
} catch {
    Write-Status "failed" "failed" @{ error = $_.Exception.Message }
    throw
}
