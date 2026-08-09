[CmdletBinding()]
param(
    [string] $PythonBin = "D:\Anaconda\envs\.conda\envs\cac\python.exe",
    [string] $OutRoot = "results\v1_9_d1_r2_engineering_local",
    [Parameter(Mandatory = $true)]
    [string] $ExpectedSourceCommit
)

$ErrorActionPreference = "Stop"
$Protocol = "V1_9_D1_R2_ENGINEERING_PILOT"
$env:OMP_NUM_THREADS = "1"

$actualCommit = (git rev-parse HEAD).Trim()
if ($actualCommit -ne $ExpectedSourceCommit) {
    throw "D1-R2 refuses source mismatch: expected $ExpectedSourceCommit, found $actualCommit"
}
if (git status --porcelain --untracked-files=no) {
    throw "D1-R2 requires no tracked-source modifications."
}
if (-not (Test-Path -LiteralPath $PythonBin)) {
    throw "Python interpreter not found: $PythonBin"
}

& $PythonBin scripts/check_gpu_runtime_v1_9.py --output "$OutRoot/runtime_manifest.json" --protocol-version $Protocol
if ($LASTEXITCODE -ne 0) { throw "CUDA runtime preflight failed" }
& $PythonBin scripts/test_actor_boundary_v1_8.py
if ($LASTEXITCODE -ne 0) { throw "actor-boundary regression failed" }
& $PythonBin scripts/test_pcrf_r2_d0_v1_9.py
if ($LASTEXITCODE -ne 0) { throw "D0-R2 regression failed" }

$common = @(
    "--env-name", "3d_intercept", "--num-envs", "8", "--rollout-steps", "128",
    "--role-dim", "8", "--intent-dim", "8", "--ppo-epochs", "4", "--device", "cuda",
    "--strict-target-sensing", "--agent-target-info-bottleneck",
    "--communication-dropout-prob", "0.3", "--message-delay-steps", "2", "--radar-dropout-prob", "0.1",
    "--failed-blue-agent", "1", "--node-failure-start-step", "40", "--node-failure-duration-steps", "80",
    "--attack-hold-steps", "4", "--min-success-step", "80", "--eval-interval", "10", "--eval-episodes", "4",
    "--save-interval", "10", "--save-snapshots", "--validation-event-logging",
    "--protocol-version", $Protocol
)

function Invoke-D1Run {
    param([string] $Method, [string] $Encoder, [int] $Hidden, [int] $Seed, [int] $EvalSeed)
    $runDir = Join-Path $OutRoot "${Method}_seed${Seed}"
    $runId = "v1_9_d1_r2_${Method}_seed${Seed}"
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $first = @($common + @(
        "--updates", "10", "--seed", "$Seed", "--graph-encoder", $Encoder, "--hidden-dim", "$Hidden",
        "--eval-base-seed", "$EvalSeed", "--method-label", $Method, "--run-id", $runId, "--out-dir", $runDir
    ))
    & $PythonBin scripts/train_ri_gmappo.py @first 1> "$runDir/segment_01_10.stdout.log" 2> "$runDir/segment_01_10.stderr.log"
    if ($LASTEXITCODE -ne 0) { throw "D1-R2 first segment failed: $runId" }
    $second = @($common + @(
        "--updates", "20", "--update-offset", "10", "--append-log",
        "--resume", "$runDir/actor_critic_training_state_latest.pt",
        "--seed", "$Seed", "--graph-encoder", $Encoder, "--hidden-dim", "$Hidden",
        "--eval-base-seed", "$EvalSeed", "--method-label", $Method, "--run-id", $runId, "--out-dir", $runDir
    ))
    & $PythonBin scripts/train_ri_gmappo.py @second 1> "$runDir/segment_11_30.stdout.log" 2> "$runDir/segment_11_30.stderr.log"
    if ($LASTEXITCODE -ne 0) { throw "D1-R2 resume segment failed: $runId" }
}

foreach ($seed in 9201, 9202) {
    $evalSeed = 2920100 + 100 * ($seed - 9200)
    Invoke-D1Run -Method "pcrf_r2" -Encoder "pcrf_r2" -Hidden 128 -Seed $seed -EvalSeed $evalSeed
    Invoke-D1Run -Method "single_r2" -Encoder "single_r2" -Hidden 147 -Seed $seed -EvalSeed $evalSeed
    Invoke-D1Run -Method "matched_nongraph_r2" -Encoder "matched_nongraph_r2" -Hidden 152 -Seed $seed -EvalSeed $evalSeed
}

& $PythonBin scripts/check_v1_9_d1_r2_artifacts.py `
    --root $OutRoot --expected-source-commit $ExpectedSourceCommit `
    --output "$OutRoot/D1_R2_ARTIFACT_GATE_MANIFEST.json"
if ($LASTEXITCODE -ne 0) { throw "D1-R2 artifact gate failed" }
