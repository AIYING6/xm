param([string]$Python = "D:/Anaconda/envs/.conda/envs/cac/python.exe", [string]$Device = "cuda")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$common = @("--env-name","3d_intercept","--target-policy","straight","--num-envs","4","--rollout-steps","64","--updates","782","--hidden-dim","64","--role-dim","8","--intent-dim","8","--graph-encoder","multi_relation","--role-gate-prior-strength","0.4","--multi-relation-global-residual-weight","1.0","--strict-target-sensing","--agent-target-info-bottleneck","--communication-dropout-prob","0.30","--message-delay-steps","2","--failed-blue-agent","1","--node-failure-start-step","40","--node-failure-duration-steps","80","--disable-evaluation","--role-gate-telemetry","--save-interval","782","--device",$Device)
foreach ($arm in @(@("full_gate","relation_conditioned"), @("no_role_gate","none"))) {
  foreach ($seed in 101,202,303) {
    $out = Join-Path $root "results/development/phase2ia2/$($arm[0])/seed$seed"
    & $Python (Join-Path $root "scripts/train_ri_gmappo.py") @common "--seed" $seed "--role-gate-mode" $arm[1] "--out-dir" $out
    if ($LASTEXITCODE -ne 0) { throw "development run failed: $($arm[0]) seed $seed" }
  }
}
