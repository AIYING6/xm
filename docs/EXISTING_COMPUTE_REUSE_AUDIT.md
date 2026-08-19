# Existing Compute Reuse Audit

**Status:** completed — zero-training asset/provenance audit
**Scope:** final-method pre-training convergence program, Step A
**Decision:** existing Phase-D 2M UTR runs are reusable *development comparators* only under an exact frozen-contract match. They are not formal-paper or confirmatory evidence.

## 1. Immutable context

This audit does not revise any historical decision:

- DRTP-SG-MAPPO remains `C — NO_ACTIONABLE_CAUSE / INTRINSIC_SEED_SENSITIVITY` and closed.
- TCR-SG-MAPPO remains permanently closed after the 2M stop and forensic `C` result.
- EDR-SG-MAPPO remains `C — NO_GO`; it was not implemented or trained.
- R1 remains the system-robustness fallback paper backbone.

The frozen scientific problem is legal relay-node-failure-induced communication/path reconfiguration, not information blackout or strict recovery.

## 2. Principal verified assets

The directly inspected Phase-D archive is [phase_d_2m_stoploss_results.tar.gz](D:/File/Downloads/phase_d_2m_stoploss_results.tar.gz). Its companion SHA-256 file is [phase_d_2m_stoploss_results.sha256](D:/File/Downloads/phase_d_2m_stoploss_results.sha256). The archive contains all 15 Phase-D 2M run manifests, training logs, final and milestone checkpoints/runtime states, gradient telemetry, 18,000 final-evaluation records, and the frozen evaluation manifest/decision.

The Phase-D manifest fixes the following for all UTR/SPC/TCR cells:

| Contract element | Verified frozen value |
|---|---|
| Architecture | matched Single-Graph actor/critic; 116,728 parameters |
| Training | 4 environments × 64 rollout steps; PPO learning rate 0.0003, gamma 0.99, GAE 0.95, clip 0.2, entropy 0.01, value coefficient 0.5, 4 PPO epochs, graph minibatch 256 |
| Environment | frozen 3DOF relay-failure environment, including legal sensing/cache/communication semantics |
| Reward/failure | S2-frozen; no reward amendment; fixed failure condition definitions |
| Actor boundary | decentralized actor legal observations/graph only; centralized `share_obs` remains critic-only |
| Exposure | 50% nominal plus conditional-uniform six topology-failure groups, with stratified bookkeeping |
| Phase-D endpoint | strict continuation to 2,000,128 steps / update 7,813; final checkpoint only for the decision |
| Evaluation | development tape starting at 440000, 100 base episodes, 12 nominal/F0/timing/duration/compound conditions, 18,000 raw rows |

## 3. Asset matrix

| Asset | Reusable for new-method development? | Reusable as comparator? | Formal-paper eligible? | Retrain required? | Reason |
|---|---|---|---|---|---|
| Phase-D 2M UTR, seeds 2002/2101–2104 | Yes, conditionally | **Yes** | No | No if a future candidate keeps the exact contract and uses 2M | Complete strict-continuous manifests, checkpoint/runtime integrity, and matching frozen 2M budget exist. A future method would still need one fresh, pre-frozen development tape for a direct comparison. |
| Phase-D 2M SPC, same seeds | No as neutral baseline | Diagnostic only | No | Yes if ever proposed as a paper comparator | Symmetric projection is a control with two catastrophic cells under its own rule; useful negative/stability evidence, not a neutral reusable baseline. |
| Phase-D 2M TCR, same seeds | No | Diagnostic only | No | Yes, but route is prohibited | One catastrophic TCR/2101 cell; forensic review found no actionable repair mechanism. |
| Phase-C 1M UTR/SPC/TCR | Curves/forensics only | No final comparator | No | Yes for a fresh final-budget comparison | Superseded by strict 2M continuation and historical v1/v2 technical-validity history. |
| DRTP strict 10M development, seeds 1901/1902 | No | Negative-result provenance only | No | Yes, route closed | Adaptive weighting suffered intrinsic seed sensitivity and is permanently closed. |
| DRTP held-out v2, seeds 2001/2002/2003 | No | No | No | N/A | Held-out evidence has already been viewed and failed; it cannot become a future untouched confirmation set. |
| FL nominal/F0 specialists, seeds 1801/1802 | Yes for zero-training diagnosis | Learnability reference only | No | Yes for any new comparison | Establishes that F0 can be learned under specialization; it does not establish a stable shared-policy algorithm. |
| MSR Mixed-50, seeds 1801/1802 | Curves/diagnosis only | No | No | Yes | Two-seed, development-only maturity reference; no OOD/seed basis for a final claim. |
| S3/RSG/Full/Role-Gate 200k runs, seeds 1501–1503 | Historical diagnosis only | No | No | Yes | Earlier architecture screens; different method state and insufficient mature budget. |
| S1-B/S2 transparent-controller and topology records | Yes for problem/mechanism evidence | Not a MARL comparator | System-paper evidence only | N/A | Supports topology/path reconfiguration and legal boundary, not algorithm superiority. |
| Canonical seeds 0–4 | No | No | Reserved only | N/A | Must remain untouched for a future fully frozen formal evaluation. Existing archival artifacts must not be repurposed as evidence for the final route. |

## 4. Seed provenance

| Seed range | Status after this audit |
|---|---|
| 0–4 | Reserved canonical only; do not train/evaluate in future development work. |
| 1501–1503 | Historical S3/RSG development. |
| 1601–1602 | TP development. |
| 1801–1802 | FL/MSR development. |
| 1901–1902 | DRTP development. |
| 2001–2003 | Previously inspected DRTP held-out; permanently not held-out. |
| 2002 | Declared stress-development seed; already used in DRTP, TCR/SPC, and Phase-D. |
| 2101–2104 | TCR/SPC/Phase-D development; already inspected. |

No listed historical seed may be described as future confirmatory/held-out. Any future confirmation must use newly frozen, never-viewed seeds after a development method passes its pre-registered screen.

## 5. A1: UTR reuse decision

**Yes — reuse the five existing UTR 2M trajectories instead of retraining them**, but only if every condition below is true:

1. the new candidate retains the S2 environment, reward, failure semantics, PPO settings, actor information boundary, SG architecture capacity, and 50% nominal/six-group conditional-uniform training distribution exactly;
2. the new candidate is trained from scratch for exactly the same 2,000,128-step development budget on seeds 2002/2101–2104;
3. comparison uses a newly frozen development-only evaluation tape that both the archived UTR final checkpoints and candidate final checkpoints can run without changing the evaluator;
4. results are analyzed per training seed, with no checkpoint promotion and no seed exclusion.

The five archived UTR runs are **not** formal-paper eligible because the seeds and tape are development evidence already examined. Reuse saves five 2M trajectories of GPU time without compromising a future development comparison; it does not remove the need for a genuinely untouched held-out stage if development succeeds.

## 6. Checkpoint/provenance safeguards

- Treat archive contents as immutable input. Do not overwrite archive-local manifests, logs, hashes, or runtime states.
- Any future re-evaluation must record the exact checkpoint SHA-256 and fresh tape SHA-256.
- Phase-D 1.5M checkpoints are learning-curve artifacts only; Phase-D conclusions use 2M final checkpoints and must not be changed by selecting milestones.
- DRTP/TCR failures are retained as negative results and may only be used as controlled stability context after a new method independently passes all future gates.

## 7. Compute implication

If a future candidate survives this convergence program, the smallest fair development comparison is not a new UTR re-run. It is:

```text
candidate × seeds {2002,2101,2102,2103,2104} × 2,000,128 steps
plus fresh shared evaluation of archived UTR final checkpoints and candidate finals.
```

That conclusion is conditional on the exact contract match above. This audit authorizes no candidate implementation, tape creation, re-evaluation, or training.
