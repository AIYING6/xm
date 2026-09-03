# Claim–evidence matrix

| Candidate claim | Current evidence | Status | Safe manuscript wording |
|---|---|---|---|
| The corrected six-UAV task is learnable | P2.13: Plain and UTR nominal success 5/5; UTR Tier-R 5/5 | Supported at main scale | “The corrected main-scale task is learnable under the frozen development protocol.” |
| UTR preserves nominal success while covering frozen groups | P2.13 UTR nominal and Tier-R success 5/5 | Supported at main scale | “UTR retained nominal success while learning the specified training conditions.” |
| UTR outperforms the tested static curriculum | P3-P2: mean all-group delta for staged minus UTR = -0.4; 0/5 positive | Supported only as an internal development ablation | “The tested static schedule did not improve over UTR under the preregistered pilot.” |
| UTR is a new robust-MARL algorithm | No distinct objective, architecture, or adaptive rule | Unsupported / contradicted | Do not claim |
| UTR beats naive randomization, PLR, EPOpt, or group-DRO | No such matched results | Not tested | Do not imply |
| UTR generalizes to held-out topology structures | No held-out result in this audit | Not tested | Do not imply |
| Framework transfers across scales | Generator semantics exist, but no matched 4/6/8 learning evidence | Not tested | Do not imply |
| Structured topology taxonomy is useful | Scripted/task-semantic validation plus current learnability | Partial | “We define and validate a candidate taxonomy; external comparisons remain required.” |

