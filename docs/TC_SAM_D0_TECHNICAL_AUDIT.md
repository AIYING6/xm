# TC-SAM-D0 Technical Audit

Audit artifact: `artifacts/tc_sam_d0/tc_sam_d0_audit.json` (generated locally; not maintained experiment evidence). All checks use synthetic PPO tensors or the existing actor-boundary regression. No environment step, rollout, tape, evaluation, development seed, held-out seed, or canonical seed was used.

| Audit | Result | Evidence |
|---|---:|---|
| A. Syntax / construction | PASS | `py_compile`; TC-SAM unit suite passed 5/5 |
| B. Baseline UTR path | PASS | `sam_enabled=False` preserves the existing UTR branch and telemetry schema |
| C. `rho=0` identity | PASS | maximum parameter difference `7.45e-09` (tolerance `2e-06`) |
| D. Perturbation norm | PASS | requested `0.05`; measured `0.050000000745`; relative error `1.49e-08` |
| E. Exact restoration | PASS | unit test compares every actor tensor with `torch.equal` after restore |
| F. Optimizer integrity | PASS | all Adam state steps are `{1}` after one update; first pass has no `optimizer.step()` |
| G. Minibatch identity | PASS | first/second SHA-256 hashes match; samples are 128 nominal / 128 failure |
| H. Actor legality | PASS | existing hidden-state regression passed 3/3 without `env.step` |
| I. Parameter equality | PASS | UTR and TC-SAM both have 116,728 parameters |
| J. Inference identity | PASS | identical weights give exactly equal deterministic actions in the unit test |
| Checkpoint continuation | PASS | save/reload/next synthetic update gives bitwise-equal model tensors |
| Finite one-update smoke | PASS | no NaN/Inf; nonzero second-pass gradient `0.0035030` |
| DRTP isolation | PASS | static SAM branch audit finds no adaptive state or return feedback |

The full test commands and measured values are retained in the JSON artifact.
