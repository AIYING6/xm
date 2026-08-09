[CmdletBinding()]
param(
    [string] $PythonBin = "D:\Anaconda\envs\.conda\envs\cac\python.exe",
    [string] $OutRoot = "results\v1_9_d1_r2_p0a_requalification_local",
    [Parameter(Mandatory = $true)] [string] $ExpectedSourceCommit
)

$ErrorActionPreference = "Stop"
$Protocol = "V1_9_D1_R2_P0A_REQUALIFICATION"
$env:OMP_NUM_THREADS = "1"
if ((git rev-parse HEAD).Trim() -ne $ExpectedSourceCommit) { throw "P0-A D1 source commit mismatch" }
if (git status --porcelain --untracked-files=no) { throw "P0-A D1 requires no tracked-source modifications" }

& $PythonBin scripts/check_gpu_runtime_v1_9.py --output "$OutRoot/runtime_manifest.json" --protocol-version $Protocol
if ($LASTEXITCODE) { throw "CUDA runtime preflight failed" }
foreach ($test in @("scripts/test_actor_boundary_v1_8.py", "scripts/test_pcrf_r2_d0_v1_9.py", "scripts/test_p0_a_terminal_estimand_v1_9.py")) {
    & $PythonBin $test
    if ($LASTEXITCODE) { throw "preflight regression failed: $test" }
}

$common = @(
    "--env-name", "3d_intercept", "--num-envs", "8", "--rollout-steps", "128", "--role-dim", "8", "--intent-dim", "8", "--ppo-epochs", "4", "--device", "cuda",
    "--strict-target-sensing", "--agent-target-info-bottleneck", "--communication-dropout-prob", "0.3", "--message-delay-steps", "2", "--radar-dropout-prob", "0.1",
    "--failed-blue-agent", "1", "--node-failure-start-step", "40", "--node-failure-duration-steps", "80", "--attack-hold-steps", "4", "--min-success-step", "80",
    "--eval-interval", "10", "--eval-episodes", "4", "--save-interval", "10", "--save-snapshots", "--validation-event-logging", "--protocol-version", $Protocol
)

function Invoke-RequalificationRun {
    param([string] $Method, [string] $Encoder, [int] $Hidden, [int] $Seed, [int] $EvalSeed)
    $runDir = Join-Path $OutRoot "${Method}_seed${Seed}"
    $runId = "v1_9_d1_r2_p0a_${Method}_seed${Seed}"
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $first = @($common + @("--updates", "10", "--seed", "$Seed", "--graph-encoder", $Encoder, "--hidden-dim", "$Hidden", "--eval-base-seed", "$EvalSeed", "--method-label", $Method, "--run-id", $runId, "--out-dir", $runDir))
    & $PythonBin scripts/train_ri_gmappo.py @first 1> "$runDir/segment_01_10.stdout.log" 2> "$runDir/segment_01_10.stderr.log"
    if ($LASTEXITCODE) { throw "first segment failed: $runId" }
    $second = @($common + @("--updates", "20", "--update-offset", "10", "--append-log", "--resume", "$runDir/actor_critic_training_state_latest.pt", "--seed", "$Seed", "--graph-encoder", $Encoder, "--hidden-dim", "$Hidden", "--eval-base-seed", "$EvalSeed", "--method-label", $Method, "--run-id", $runId, "--out-dir", $runDir))
    & $PythonBin scripts/train_ri_gmappo.py @second 1> "$runDir/segment_11_30.stdout.log" 2> "$runDir/segment_11_30.stderr.log"
    if ($LASTEXITCODE) { throw "resume segment failed: $runId" }
}

foreach ($seed in 9301, 9302) {
    $evalSeed = 2930100 + 100 * ($seed - 9300)
    Invoke-RequalificationRun "pcrf_r2" "pcrf_r2" 128 $seed $evalSeed
    Invoke-RequalificationRun "single_r2" "single_r2" 147 $seed $evalSeed
    Invoke-RequalificationRun "matched_nongraph_r2" "matched_nongraph_r2" 152 $seed $evalSeed
}

& $PythonBin scripts/check_v1_9_d1_r2_p0a_artifacts.py --root $OutRoot --expected-source-commit $ExpectedSourceCommit --output "$OutRoot/D1_R2_P0A_REQUALIFICATION_GATE_MANIFEST.json"
if ($LASTEXITCODE) { throw "P0-A D1 artifact gate failed" }
