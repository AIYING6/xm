# T3 — Offline Continuity Predictability Report

## Contract compliance

This report uses only the five existing source-closed T1 UTR-SG final-policy telemetry files. It created no environment, rollout, evaluation tape, checkpoint, MARL update, or policy fine-tuning. The only fitted objects were CPU `SGDClassifier(loss='log_loss')` diagnostic probes.

- Source: `results/development/t1_telemetry_native_reference_1m_run1`
- Output: `results/development/t3_offline_continuity_predictability_run3/t3_predictability.json`
- Seeds: 2201–2205; validation leaves one complete training seed out.
- Each seed contributes a deterministic, balanced reservoir of 4,000 positive and 4,000 negative samples. Adjacent episode timesteps are never split across train and validation.
- Label: attacker `Y_A^t(16)` from [T3_TASK_SUPPORT_CONTINUITY_FORMALIZATION.md](T3_TASK_SUPPORT_CONTINUITY_FORMALIZATION.md).

## Pooled leave-one-training-seed-out result

| Legal input representation | Mean AUC | Mean balanced accuracy | Delta AUC vs. current observation |
|---|---:|---:|---:|
| current actor observation, `L=1` | **0.9248** | **0.8623** | 0.0000 |
| current observation + graph | 0.9247 | 0.7620 | -0.0001 |
| observation history, `L=4` | 0.9331 | 0.8523 | +0.0083 |
| observation history, `L=8` | 0.9291 | 0.8299 | +0.0043 |
| observation history, `L=16` | 0.9167 | 0.8244 | -0.0081 |
| observation history, `L=32` | 0.9165 | 0.8275 | -0.0083 |
| observation + legal graph history, `L=16` | 0.9187 | 0.7768 | -0.0060 |
| scenario/time metadata only (forbidden control) | 0.8581 | 0.7958 | -0.0667 |
| metadata + failure-active truth (forbidden control) | 0.8511 | 0.8203 | -0.0737 |
| metadata + terminal proximity oracle (forbidden control) | 0.8588 | 0.7978 | -0.0660 |

The full seed-level, period, and scenario-family values are preserved in the JSON artifact. Instantaneous legal observation has nontrivial AUC in each required family and every validation seed: F0 0.853–0.971, timing 0.881–0.955, and duration 0.831–0.973. Relevant period slices also exceed chance when both classes are available; no terminal-derived value is an input.

## Questions Q1–Q7

| Question | Result | Evidence-bound interpretation |
|---|---|---|
| Q1: above trivial frequency? | PASS | `L=1` mean AUC 0.9248 and balanced accuracy 0.8623. |
| Q2: history adds meaningful value? | **FAIL** | The best result is `L=4`, only +0.0083 AUC; `L>=16` is worse than `L=1`. |
| Q3: graph history adds value? | **FAIL** | `obs+graph L=16` is 0.9187, below `L=1`. |
| Q4: leave-one-seed-out survives? | PASS for instantaneous predictability | All `L=1` AUCs are 0.867–0.958; this does not rescue Q2/Q3. |
| Q5: F0/timing/duration? | PASS for instantaneous predictability | The signal is not restricted to one failure family. |
| Q6: before terminal? | PASS, qualified | Relevant pre-/early-/mid-period slices are above chance; some are class-imbalanced. |
| Q7: actor-legal without privileged global input? | PASS | Inputs are actor `obs[2]` and legal graph summaries only. |

## Shortcut conclusion

The terminal-proximity oracle is not stronger than metadata alone, so the `L=1` signal is not explained solely by termination proximity. However, time/condition metadata alone reaches AUC 0.8581, especially 0.9623 in seed2204. It is prohibited at execution and demonstrates substantial label structure unrelated to an inferred topology belief.

Most importantly, instantaneous actor-legal observation outperforms all longer temporal/graph histories. The evidence supports a short-horizon local-state association, not a memory deficit or new temporal graph state.

## T3 feasibility verdict

The target is legal and reproducibly predictable, but temporal and graph history do not provide material, stable incremental predictability. Under the frozen T3 rule, this does not justify a continuity-belief, GRU, temporal graph, or history-auxiliary method.
