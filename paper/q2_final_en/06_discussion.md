# 6. Discussion

## 6.1 What the formal comparison establishes

The contribution of DRTP is deliberately narrow. With model capacity, PPO, reward, perturbation support, nominal exposure, and execution-time information fixed, the formal cohort showed that bounded adaptive reweighting of failure groups outperformed uniform reweighting on canonical F0 and the two frozen cross-perturbation endpoints. The result was not driven solely by a higher nominal score: the aggregate degradation from nominal performance was also smaller for DRTP. However, the formal nominal-retention rule was cohort-level; the nominal decline in seed 2302 shows that it must not be read as a guarantee for every initialization.

The formal experiment does not establish that online adaptation is superior to all static non-uniform distributions. A fixed non-uniform comparator was not trained concurrently in the primary cohort, and the later SNR comparator did not outperform UTR in the independent cohort. DRTP is consequently an empirical, cohort-bounded training-distribution intervention rather than a general distributionally robust optimization method.

## 6.2 Training-cohort sensitivity limits generalization of the gain

The independent three-method cohort reversed the direction of all four aggregate DRTP-minus-UTR task endpoints and contained a catastrophic DRTP seed. This observation does not invalidate the completed formal comparison: its five-seed protocol, final checkpoints, and positive paired results remain factual. It does limit the scope of any general claim. In particular, the formal outcome cannot be promoted to stable superiority across training cohorts, random initializations, or arbitrary training realizations.

The cross-tape diagnosis makes an evaluation-tape explanation insufficient. Both cohorts retained their respective directions when evaluated on tape490 and tape500. The additional evaluation on six training-excluded onset--duration members likewise reproduced positive formal-cohort and negative independent-cohort directions. These checks localize the unresolved issue to the training-cohort/seed level. They do not demonstrate that a specific random source, optimization basin, sampler excursion, or policy mechanism caused the reversal.

## 6.3 Reliability stress tests strengthen the boundary rather than add a method claim

Exploratory stabilization studies were conducted after the formal comparison to test whether the observed risk could be removed by readily available local interventions. Bounded sampler steps, a uniform anchor, fixed KL-based actor protection, training-only paired probes, candidate selection, and a counterfactual critic each produced local positive signals in some development seeds or pilots. None retained task gain, upper-tail behavior, and reduced seed dispersion in its subsequent independent cohort. The counterfactual critic produced systematic task degradation in two fresh five-seed cohorts.

These negative studies do not constitute alternative main methods, are not pooled with the formal DRTP evidence, and do not identify a failure mechanism. Their narrower value is to rule out the claim that the independent reversal is already resolved by a simple sampler, KL, probe, selector, or critic patch. We therefore retain training-cohort sensitivity as a current applicability boundary instead of selectively reporting a locally favorable stabilization candidate. A compact evidence ledger is provided in Supplementary Table S5.

## 6.4 Safety, information-path interpretation, and alternative explanations

Higher mission score did not imply uniform safety improvement. In the formal cohort, DRTP reduced mean timeout but slightly increased collision, with the increment concentrated in one seed. The result should consequently be read as a task--safety trade-off. Risk-set trigger validity established that failures were correctly injected for all episodes alive at their scheduled onset; it did not remove pre-onset collisions from the task or safety denominators.

The matched UTR control also excludes one simple exposure explanation: both methods encountered the same seven training groups and shared the same nominal anchor, so the formal contrast cannot be explained by DRTP seeing a failure class unavailable to UTR. Sampler telemetry confirmed changed training exposure and was consistent with altered task-support/path utilization. It did not demonstrate that a particular weight change caused a particular policy behavior or restored unavailable information. Relay failure can leave a legal direct Scout-to-Attacker path intact; the problem is therefore topology/path reconfiguration, not universal communication blackout.

## 6.5 Scope and future research

The evidence is limited to a frozen three-UAV, lightweight 3DOF simulation with predefined relay-failure conditions. It contains neither larger teams, hardware-in-the-loop validation, nor flight tests. The primary causal evidence is the matched UTR--DRTP comparison; MAPPO-NoGraph is an external performance reference with different capacity and inputs. The ten primary perturbation members were seen by the training sampler, while the six excluded-member tests were post hoc and cannot be presented as confirmatory OOD generalization.

Future reliability work requires a new mechanism-focused contract rather than another result-driven stabilizer. Such a contract would need a repeated, time-leading, DRTP-specific precursor and a single intervention that targets it, followed by prospective validation in separate fresh-seed cohorts. Until then, the appropriate interpretation is that DRTP has substantial formal-cohort upside under the stated contract, with an unresolved cross-cohort reliability limitation.
