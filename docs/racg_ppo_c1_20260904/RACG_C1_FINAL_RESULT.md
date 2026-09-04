# RACG-PPO C1 final result

## Verdict

`RACG_C1_NO_GO`

This is a training-only, exact same-rollout mechanism result. It is not a return or policy-performance evaluation, and no formal, independent or held-out evaluation tape was read.

## What was tested

Five completed UTR source states (2201--2205) supplied model and Adam states. Each state produced one deterministic 24-by-64 rollout with 768 nominal graphs and 128 graphs for each of F0, TE, TL, DS, DL and CP. Every topology group had two fixed stream halves. Ordinary PPO and frozen RACG-PPO started from identical model/optimizer states and consumed the same immutable batch.

RACG used both training halves only to estimate gradient agreement and construct the frozen continuous correction. No held-stream acceptance test, actor rollback or zero-step path was present. The critic state was copied from the matched ordinary branch after the actor comparison so critic learning remained exact.

## Gate results

| Gate | Result | Evidence |
| :--- | :---: | :--- |
| exact paired batches | PASS | 5/5 complete, correctly stratified batches |
| material correction | PASS | 3/5 states exceeded the frozen 1% correction ratio |
| worst-group harm reduction | FAIL | only 2/5 states improved by at least `1e-7`; 4/5 required |
| overall surrogate retention | PASS | 4/5 states retained ordinary within `1e-7` |
| non-freezing and realized motion | PASS | every epoch retained the 0.5 bound and produced nonzero actor displacement |
| critic parity | PASS | 5/5 critic states exactly matched ordinary PPO |
| numerical safety | PASS | finite outputs, no solver failure and no zero actor step |
| cost | FAIL | CPU wall-time ratios were 6.84--11.05; maximum allowed was 4.0 |
| evaluation isolation | PASS | no evaluation data used |

## Per-state direction

| Seed | worst-group RACG-minus-ordinary | overall RACG-minus-ordinary | maximum correction ratio | mean reliability |
| ---: | ---: | ---: | ---: | ---: |
| 2201 | -5.44079e-05 | 1.57392e-05 | 0.037 | 0.064 |
| 2202 | 4.09343e-04 | 1.94086e-04 | 0.093 | 0.179 |
| 2203 | 1.16907e-04 | -1.88753e-04 | 0.322 | 0.291 |
| 2204 | -1.45985e-07 | 2.83937e-07 | 0.000 | 0.000 |
| 2205 | 2.32831e-08 | -1.16415e-10 | 0.000 | 0.000 |

## Interpretation

RACG fixes TGTR's liveness failure: uncertainty no longer rejects every actor update, and the soft correction usually preserves the overall PPO surrogate. However, the intended scientific mechanism was not repeatable. The correction reduced the worst group harm in only two source states and slightly worsened it in two others. In the remaining state the change was below the frozen numerical threshold. The cross-fitted agreement was nearly zero in two states, so the candidate mostly reverted to ordinary PPO there.

The cost failure is secondary but material: fourteen group-gradient vector products per epoch make this implementation much more expensive than ordinary PPO. Even if GPU execution reduced the wall ratio, the failed 2/5 worst-group mechanism gate independently determines `NO_GO`.

## Boundary and stop decision

The frozen RACG candidate is closed. The result does not authorize a threshold change, stronger correction, alternative reliability formula, solver revision, RACG-v2, fresh-seed development, cloud training or performance claim. Any future algorithm work must start as a new mechanism hypothesis rather than tune this failed C1 outcome.
