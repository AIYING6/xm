param([string]$Python = "D:/Anaconda/envs/.conda/envs/cac/python.exe", [string]$Device = "cuda")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$resultRoot = Join-Path $root "results/development/role_gate_phase2ia2"
$configRoot = Join-Path $root "configs/development"
$gitSha = (& git -C $root rev-parse HEAD).Trim()
function Get-Sha256([string]$Path) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $stream = [System.IO.File]::OpenRead($Path)
    try { return ([System.BitConverter]::ToString($sha.ComputeHash($stream))).Replace("-", "").ToLowerInvariant() }
    finally { $stream.Dispose() }
  } finally { $sha.Dispose() }
}
$common = @("--env-name","3d_intercept","--target-policy","straight","--num-envs","4","--rollout-steps","64","--updates","782","--hidden-dim","64","--role-dim","8","--intent-dim","8","--graph-encoder","multi_relation","--role-gate-prior-strength","0.4","--multi-relation-global-residual-weight","1.0","--strict-target-sensing","--agent-target-info-bottleneck","--communication-dropout-prob","0.30","--message-delay-steps","2","--failed-blue-agent","1","--node-failure-start-step","40","--node-failure-duration-steps","80","--disable-evaluation","--role-gate-telemetry","--save-interval","782","--device",$Device)
foreach ($arm in @(@("full_gate","relation_conditioned"), @("no_role_gate","none"))) {
  foreach ($seed in 101,202,303) {
    $out = Join-Path $resultRoot "runs/$($arm[0])/seed$seed"
    if (Test-Path -LiteralPath $out) { throw "refusing to overwrite existing frozen run directory: $out" }
    $config = Join-Path $configRoot "phase2ia2_$($arm[0]).json"
    $manifest = [ordered]@{ artifact_class="DEVELOPMENT_ONLY"; arm=$arm[0]; seed=$seed; git_sha=$gitSha; config_path=$config; config_sha256=(Get-Sha256 $config); environment_steps=200192; start_time=(Get-Date).ToUniversalTime().ToString("o"); completion_status="running"; checkpoint="actor_critic_latest.pt"; telemetry="role_gate_telemetry.csv" }
    New-Item -ItemType Directory -Path $out -Force | Out-Null
    $manifest | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $out "run_manifest.json")
    & $Python (Join-Path $root "scripts/train_ri_gmappo.py") @common "--seed" $seed "--role-gate-mode" $arm[1] "--out-dir" $out
    if ($LASTEXITCODE -ne 0) { throw "development run failed: $($arm[0]) seed $seed" }
    $checkpoint = Join-Path $out "actor_critic_latest.pt"
    $manifest.completion_status="completed"; $manifest.end_time=(Get-Date).ToUniversalTime().ToString("o"); $manifest.checkpoint_sha256=(Get-Sha256 $checkpoint)
    $manifest | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $out "run_manifest.json")
  }
}
