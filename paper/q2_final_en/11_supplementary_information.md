# Supplementary Information

## S1. Formal-cohort condition, seed, and safety audit

This section corresponds only to the formal UTR--DRTP cohort (training seeds 2301--2305). All values use the common 10M final checkpoint and the frozen 12-condition tape with base episode identifiers 490000--490099. Training seed is the independent unit; the 100 evaluation episodes within each method--seed--condition cell estimate that seed's condition outcome and do not create additional independent training replicates.

The machine-readable source of truth is the formal release package: `per_seed_condition_summary.csv` contains all normal, F0, and ten perturbation-condition outcomes and diagnostics; `formal_failure_safety_by_seed.csv` contains safety and risk-set fields; `formal_terminal_outcomes_by_seed_family.csv` contains completion, timeout, collision, and constraint outcomes; and the evaluation manifests retain the condition list, episode identifiers, and tape hash. The archived machine field names `J_OOD_mean` and `J_OOD_worst` map only to `J_pert,mean` and `J_pert,worst`; they do not denote strict OOD evidence.

### Table S1. Formal paired seed effects (DRTP minus UTR)

| Training seed | \(\Delta J_{nominal}\) | \(\Delta J_{F0}\) | \(\Delta J_{pert,mean}\) | \(\Delta J_{pert,worst}\) | \(\Delta\) collision | \(\Delta\) timeout | Catastrophic under the frozen rule |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2301 | +26.66 | +35.04 | +33.00 | +29.78 | -0.010 | -0.485 | No |
| 2302 | -26.90 | +5.79 | +17.01 | +11.71 | +0.000 | -0.001 | No |
| 2303 | +96.84 | +108.15 | +103.78 | +117.39 | -0.014 | -0.338 | No |
| 2304 | +9.53 | +20.55 | +24.42 | +38.40 | +0.040 | +0.018 | No |
| 2305 | +61.29 | +91.14 | +96.79 | +117.78 | -0.002 | -0.095 | No |

### Table S2. Formal failure-condition safety and trigger-validity audit

Each row aggregates the 1,100 planned failure episodes for one method--seed cell. Pre-onset collision remains a policy safety outcome and is included in unconditional safety and mission-score denominators. Trigger validity is conditional on the risk set of episodes alive at scheduled onset.

| Method | Seed | Collision | Timeout | Constraint violation | Pre-onset collisions | Risk set | Trigger validity in risk set |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| UTR | 2301 | 0.0100 | 0.9809 | 0.0000 | 8 | 1092 | 1.000 |
| UTR | 2302 | 0.0000 | 0.9436 | 0.0000 | 0 | 1100 | 1.000 |
| UTR | 2303 | 0.0136 | 0.9845 | 0.0000 | 0 | 1100 | 1.000 |
| UTR | 2304 | 0.0000 | 0.7009 | 0.0000 | 0 | 1100 | 1.000 |
| UTR | 2305 | 0.0018 | 0.7609 | 0.0000 | 0 | 1100 | 1.000 |
| DRTP | 2301 | 0.0000 | 0.4955 | 0.0000 | 0 | 1100 | 1.000 |
| DRTP | 2302 | 0.0000 | 0.9427 | 0.0000 | 0 | 1100 | 1.000 |
| DRTP | 2303 | 0.0000 | 0.6464 | 0.0000 | 0 | 1100 | 1.000 |
| DRTP | 2304 | 0.0400 | 0.7191 | 0.0000 | 36 | 1064 | 1.000 |
| DRTP | 2305 | 0.0000 | 0.6655 | 0.0000 | 0 | 1100 | 1.000 |

The formal cohort should not be read as uniformly safer: DRTP has lower aggregate timeout but its collision increase is concentrated in seed 2304. The complete condition-level records retain all planned failure episodes and do not delete or relabel pre-onset terminations.

## S2. Training, PPO, and sampler diagnostics

These diagnostics audit optimization logs and sampler activity. They are not used for checkpoint selection and do not replace the common 10M final-checkpoint evaluation. Formal source files include a 500-update-binned monitor of training return, approximate KL, and clip fraction for all ten formal trajectories, and a sampler-telemetry summary containing the six DRTP group weights, realized episode counts, EMA/difficulty state, and integrity information.

Because UTR and DRTP intentionally use different training weights, batch return is not a common test distribution. The diagnostics can verify that no intermediate checkpoint was promoted and that DRTP changed group exposure; they cannot establish that a given sampler weight caused a particular final policy behavior. The final paper should render the existing training-diagnostics figure as Supplementary Figure S1 after target-template migration.

## S3. Frozen training contract and provenance

The formal protocol is `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1`. Both arms use the same 116,728-parameter SG actor--critic, PPO settings, environment, reward, seven-group training universe, 50% nominal-condition anchor, 10,000,128 environment steps, and paired seeds 2301--2305. UTR samples six failure groups conditionally uniformly; DRTP is the only arm that reallocates the fixed 50% failure mass with its frozen six-dimensional bounded update.

| Item | Frozen value |
| --- | --- |
| PPO learning rate | \(3\times10^{-4}\) |
| Discount / GAE coefficient | 0.99 / 0.95 |
| PPO clipping / entropy / value coefficient | 0.2 / 0.01 / 0.5 |
| Maximum gradient norm / PPO epochs | 0.5 / 4 |
| DRTP initial \(q\), warm-up, adaptation cadence | \(1/6\), 128 updates, every 32 updates |
| \(q\) bounds | \([0.05,0.35]\), with unit total mass |
| \(\kappa,\eta,\beta,d_{max},\epsilon\) | 0.20, 1.00, 0.50, 2.00, \(10^{-8}\) |
| Formal tape | IDs 490000--490099; 12 conditions; 12,000 raw records |
| Formal tape SHA256 | `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2` |
| Formal archive SHA256 | `cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd` |
| NoGraph archive SHA256 | `2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5` |
| Independent three-method archive SHA256 | `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1` |
| Independent tape SHA256 | `c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2` |

The bounded-simplex projection uses 100 bisection iterations to obtain the projection scalar, applies a deterministic residual correction only if needed, and asserts total mass and bounds after projection. All completed seeds, including unfavorable seeds and the independent reversal, remain in the provenance package. Checkpoint promotion, seed exclusion, performance-driven reruns, and cross-cohort \(n=10\) pooling are prohibited.

## S4. Independent three-method cohort and cross-cohort reliability boundary

The independent protocol `DRTP-SNR-Q2-MECHANISM-COMPARATOR-TRAINING-V1` is a completed three-method cohort, not five additional formal seeds. UTR, fixed non-uniform SNR, and DRTP each used seeds 2401--2405 and were trained from scratch to 10,000,128 steps under the common final-checkpoint rule. The cohort used a separate 12-condition tape with IDs 500000--500099 and 18,000 raw records. The failure trigger was valid for every episode alive at planned onset; pre-onset collisions remain in unconditional outcome denominators.

### Table S3. Independent cohort outcomes

| Method | \(n\) | \(J_{nominal}\) | \(J_{F0}\) | \(J_{pert,mean}\) | \(J_{pert,worst}\) | Failure collision | Failure timeout | Constraint violation | Risk-set trigger validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| UTR | 5 | 225.70 | 199.40 | 200.48 | 181.98 | 0.009 | 0.646 | 0.000 | 1.000 |
| Fixed non-uniform SNR | 5 | 184.64 | 183.07 | 178.00 | 159.63 | 0.014 | 0.661 | 0.000 | 1.000 |
| DRTP | 5 | 187.35 | 166.13 | 166.41 | 149.61 | 0.052 | 0.678 | 0.000 | 1.000 |

### Table S4. Independent paired DRTP-minus-UTR effects

| Seed | \(\Delta J_{nominal}\) | \(\Delta J_{F0}\) | \(\Delta J_{pert,mean}\) | \(\Delta J_{pert,worst}\) | \(\Delta\) collision | \(\Delta\) timeout |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2401 | -25.16 | -49.30 | -54.26 | -51.66 | +0.199 | -0.009 |
| 2402 | -41.22 | +21.12 | +11.66 | +25.94 | -0.001 | -0.015 |
| 2403 | -115.41 | -141.57 | -123.87 | -131.50 | +0.010 | +0.143 |
| 2404 | -27.96 | -25.10 | -29.14 | -53.01 | -0.020 | +0.009 |
| 2405 | +18.02 | +28.52 | +25.26 | +48.41 | +0.024 | +0.031 |
| **Mean paired effect** | **-38.35** | **-33.27** | **-34.07** | **-32.36** | -- | -- |
| **Median paired effect** | **-27.96** | **-25.10** | **-29.14** | **-51.66** | -- | -- |
| **Positive seeds** | **1/5** | **2/5** | **2/5** | **2/5** | -- | -- |
| **Worst paired effect** | **-115.41** | **-141.57** | **-123.87** | **-131.50** | -- | -- |

DRTP therefore does not reproduce its formal-cohort direction in this cohort; one DRTP seed meets the pre-frozen catastrophic-seed rule, and SNR does not outperform UTR. This result does not modify or erase the completed formal cohort. The two cohorts have different seeds, tapes, and pre-frozen purposes and must never be pooled into an apparent \(n=10\) result. It also does not show that every fixed non-uniform sampler is ineffective.

## S5. Exploratory stabilization stress tests and negative-result boundary

The following post-formal studies are not additional primary methods. Their purpose was to test whether a simple local intervention had already eliminated the Original DRTP seed/cohort risk. Each row belongs to its own development or validation contract; seeds, budgets, tapes, and candidate semantics are not pooled. Training seed is the sole independent unit. No candidate used performance-based seed replacement, rerunning, or checkpoint promotion.

| Route | Local design goal | Most favorable completed signal | Independent or subsequent test | Final status |
| --- | --- | --- | --- | --- |
| Trust-region sampler bound | Limit one sampler-weight movement | Preserved some high-reward seeds | 0.5M gate did not protect the worst seed or reduce dispersion | Closed |
| Uniform anchor | Retain a uniform sampling floor | Removed frozen catastrophic labels in an early cohort | Five-seed R1 reversed and increased dispersion | Closed |
| KLR/KLB | Roll back or protect high-KL actor updates | KLR three-seed pilot had positive mean and worst paired gain | Two independent KLR cohorts added catastrophic seeds and increased gain dispersion; KLB did not restore gain | Closed |
| Paired probe | Use training-only paired probes to alter exposure | Short-term lower-tail improvement in P3 | Independent P4 included catastrophic candidates and higher dispersion | Closed |
| Population/priority selector | Select conservative interventions from training signals | Local benefit in individual development seeds | Did not retain relative UTR advantage across cohorts | Closed |
| Selective-KLR shadow audit | Determine whether an individual rollback is useful | 88 KL alarms included a small number of beneficial and harmful events | 84 events were near-zero; no reusable seed-level selector signal | Selector not trained |
| CV-DRTP | Reduce agent credit variance with a counterfactual critic | No transferable positive signal | Two fresh five-seed cohorts systematically lost relative UTR gain and added catastrophic seeds | Permanently closed |

The bounded conclusion is that these simple sampler, KL, probe, selector, and critic modifications did not jointly retain gain, protect the lower tail, and reduce dispersion across cohorts in the frozen environment and PPO implementation. This does not prove that no stabilization method can work and does not establish a single causal mechanism for Original DRTP sensitivity. These candidates must not be reintroduced as main methods, a leaderboard, or a mechanism proof.

## S6. Reproducibility release status

Local anonymous-package staging and checksum verification are technically complete. The staged package preserves formal UTR--DRTP records, NoGraph reference records, independent three-method records, cross-tape diagnostics, manifests, sampler logs, code, configurations, plotting scripts, and provenance. This is not yet a public-availability claim: external anonymous hosting, external download verification, licence choice, checkpoint/runtime-state access policy, and author/funding/CRediT/conflict metadata remain author-owned actions. The release gate is therefore `TECHNICAL_READY_AUTHOR_ACTION_REQUIRED` until an author-supplied private metadata file enables a successful external release check.
