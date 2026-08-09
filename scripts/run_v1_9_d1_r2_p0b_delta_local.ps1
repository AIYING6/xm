[CmdletBinding()]
param(
    [string] $PythonBin = "D:\Anaconda\envs\.conda\envs\cac\python.exe",
    [string] $OutRoot = "results\v1_9_d1_r2_p0b_delta_requalification_local",
    [Parameter(Mandatory = $true)] [string] $ExpectedSourceCommit
)

$ErrorActionPreference = "Stop"
$Protocol = "V1_9_D1_R2_P0B_DELTA_REQUALIFICATION"
$env:OMP_NUM_THREADS = "1"
if ((git rev-parse HEAD).Trim() -ne $ExpectedSourceCommit) { throw "P0-B delta source commit mismatch" }
if (git status --porcelain --untracked-files=no) { throw "P0-B delta requires no tracked-source modifications" }
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

& $PythonBin scripts/check_gpu_runtime_v1_9.py --output "$OutRoot/runtime_manifest.json" --protocol-version $Protocol
if ($LASTEXITCODE) { throw "CUDA runtime preflight failed" }
& $PythonBin scripts/audit_p0_b_feature_provenance_v1_9.py 1> "$OutRoot/p0b_runtime_path.log" 2> "$OutRoot/p0b_runtime_path.stderr.log"
if ($LASTEXITCODE) { throw "P0-B runtime-path regression failed" }
foreach ($test in @("scripts/test_actor_boundary_v1_8.py", "scripts/test_pcrf_r2_d0_v1_9.py", "scripts/test_p0_a_terminal_estimand_v1_9.py")) {
    & $PythonBin $test
    if ($LASTEXITCODE) { throw "preflight regression failed: $test" }
}

$common = @(
    "--env-name", "3d_intercept", "--num-envs", "8", "--rollout-steps", "128", "--role-dim", "8", "--intent-dim", "8", "--ppo-epochs", "4", "--device", "cuda",
    "--strict-target-sensing", "--agent-target-info-bottleneck", "--communication-dropout-prob", "0.3", "--message-delay-steps", "2", "--radar-dropout-prob", "0.1",
    "--failed-blue-agent", "1", "--node-failure-start-step", "40", "--node-failure-duration-steps", "80", "--attack-hold-steps", "4", "--min-success-step", "80",
    "--updates", "15", "--eval-interval", "5", "--eval-episodes", "4", "--save-interval", "5", "--save-snapshots", "--validation-event-logging", "--protocol-version", $Protocol,
    "--seed", "9401", "--eval-base-seed", "2940100"
)

function Invoke-DeltaRun {
    param([string] $Method, [string] $Encoder, [int] $Hidden)
    $runDir = Join-Path $OutRoot "${Method}_seed9401"
    $runId = "v1_9_d1_r2_p0b_delta_${Method}_seed9401"
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $runArgs = @($common + @("--graph-encoder", $Encoder, "--hidden-dim", "$Hidden", "--method-label", $Method, "--run-id", $runId, "--out-dir", $runDir))
    & $PythonBin scripts/train_ri_gmappo.py @runArgs 1> "$runDir/train.stdout.log" 2> "$runDir/train.stderr.log"
    if ($LASTEXITCODE) { throw "delta run failed: $runId" }
}

Invoke-DeltaRun "pcrf_r2" "pcrf_r2" 128
Invoke-DeltaRun "single_r2" "single_r2" 147
Invoke-DeltaRun "matched_nongraph_r2" "matched_nongraph_r2" 152

& $PythonBin scripts/check_v1_9_d1_r2_p0b_delta_artifacts.py --root $OutRoot --expected-source-commit $ExpectedSourceCommit --output "$OutRoot/D1_R2_P0B_DELTA_REQUALIFICATION_GATE_MANIFEST.json"
if ($LASTEXITCODE) { throw "P0-B delta artifact gate failed" }
