# Experiment Section Draft: Strict-Sensing Relay-Failure Recovery

Last updated: 2026-07-19

This draft is paper-facing text for the fixed-update-60 hardened safety evidence package. It should be adapted to the final manuscript style before submission.

## Section Title

Robust Kill-Chain Recovery under Strict Intermittent Sensing and Relay Failure

## Experimental Setting

We evaluate the proposed method in a 3DOF heterogeneous cooperative interception task with strict intermittent target sensing and a relay-node communication failure. The blue team contains role-specialized agents that must maintain a sensing-communication-task chain after a temporary relay failure. The target state is not globally exposed to decentralized actors: target information is available only through direct sensing or valid communication messages subject to freshness and confidence constraints. Delayed communication follows post-step timing, and stale or low-confidence target caches are invalid for kill-chain closure.

All methods are evaluated under the same fixed-budget protocol. Each method is trained from the same source-policy family for 60 safety-continuation PPO updates and is evaluated at the fixed checkpoint `actor_critic_update_0060.pt`. No validation-based checkpoint selection is used in this fixed-budget result package. The test set contains five independent training seeds and 100 matched test episodes per seed. The evaluation scenario is `dropout030_relay_failure`, with strict target sensing, target-information bottleneck, and the light proximity safety auxiliary enabled.

The main metrics are post-failure chain recovery rate, tracking rate during failure, communication connectivity during failure, chain-closure rate during failure, timeout rate, and collision rate. Statistical intervals are computed using a hierarchical bootstrap that first resamples training seeds and then resamples matched episodes within each seed.

## Main Comparison Text

Table `tab:gate1-safety-fx60-main` summarizes the fixed-budget main comparison. The full multi-relation method achieves an `88.6%` post-failure recovery rate, compared with `53.2%` for the single-graph baseline and `21.8%` for the no-graph MAPPO-style baseline. The full method also improves failure-window tracking from `47.5%` to `77.6%` relative to the single-graph baseline, and from `14.8%` to `77.6%` relative to the no-graph baseline.

The seed-aware bootstrap confirms that these gains are not only episode-level fluctuations. The recovery-rate improvement over the single-graph baseline is `+35.4` percentage points with a 95% confidence interval of `[+1.2, +73.0]` percentage points. Against the no-graph baseline, the recovery-rate improvement is `+66.8` percentage points with a 95% confidence interval of `[+28.6, +93.8]` percentage points. The full method also maintains zero test collisions in this fixed-budget evaluation, while the single-graph baseline has a `2.8%` mean collision rate.

These results indicate that under strict information constraints, explicit multi-relation role-graph reasoning improves the ability to recover a cooperative kill chain after a critical communication-node failure.

## Ablation Text

Table `tab:gate1-safety-fx60-ablation` evaluates two mechanism ablations of the full multi-relation model.

Removing role-pair-conditioned message gating reduces recovery from `88.6%` to `64.8%`. The seed-aware recovery-rate delta is `+23.8` percentage points with a 95% confidence interval of `[+2.8, +59.2]` percentage points. This ablation also increases the timeout rate from `11.4%` to `35.2%` and reduces failure-window tracking from `77.6%` to `60.7%`. Because the collision rate remains zero for both variants, the degradation is not explained by unsafe flight termination. This supports the role-pair message gate as the clearest current mechanism contribution.

Removing task-support relations also reduces mean recovery from `88.6%` to `64.8%`, but the seed-aware recovery interval `[-9.2, +63.6]` percentage points crosses zero. This suggests that the task-support relation is useful on average but has stronger seed-level heterogeneity. Therefore, this ablation should be reported as supportive mechanism evidence rather than as a statistically decisive result.

Overall, the ablation results support the interpretation that the proposed model benefits from role-conditioned message passing over heterogeneous relation channels. The strongest ablation evidence is the role-pair gate comparison; the task-support relation provides secondary support and motivates further stability analysis.

## Mechanism Figure Text

Figure `fig:gate1-safety-fx60-mechanism` shows failure-aligned tracking, connectivity, chain-closure, and recovery-CDF curves. All curves are aligned to the relay-failure start time and aggregated over the matched fixed-budget test set. After relay failure, overall connectivity drops sharply for all methods, indicating that the full method's advantage is not simply caused by maintaining a fully connected communication graph. Instead, the full method preserves higher target tracking and accumulates recovery events earlier and more consistently after the failure.

The recovery-CDF curve is the most direct mechanism evidence: the full multi-relation method rapidly reaches a substantially higher recovery probability than the single-graph and no-graph baselines. The tracking curve further shows that the full method maintains or reconstructs useful target information more effectively during the failure window.

Figure `fig:gate1-safety-fx60-case` presents a representative matched episode selected automatically by a median-positive-difference rule rather than by hand-picking the largest gap. In this episode, the single-graph baseline fails to recover the chain and times out, whereas the full method re-establishes chain closure shortly after the relay failure. This case illustrates the aggregate trend shown in the failure-aligned curves.

## Suggested Table Captions

`tab:gate1-safety-fx60-main`:

Fixed-update-60 hardened safety comparison under strict intermittent sensing and relay failure. Values are mean plus standard deviation over five training seeds, with 100 matched test episodes per seed. The full multi-relation method improves post-failure recovery and failure-window tracking while maintaining zero test collisions.

`tab:gate1-safety-fx60-ablation`:

Mechanism ablations under the same fixed-update-60 hardened safety protocol. Removing role-pair-conditioned message gating produces a seed-aware recovery degradation with a separated confidence interval. Removing task-support relations lowers mean recovery but shows stronger seed-level heterogeneity.

`tab:gate1-safety-fx60-bootstrap`:

Seed-aware hierarchical bootstrap deltas. Positive values indicate improvement of the full multi-relation method over the comparison method except for timeout, where negative values are better. Bootstrap resamples training seeds first and matched episodes second.

## Suggested Figure Captions

`fig:gate1-safety-fx60-mechanism`:

Failure-aligned mechanism curves under relay failure. Curves are aligned to the relay-failure start time and aggregated over five training seeds and 500 matched test episodes. The full multi-relation method achieves higher post-failure recovery and better target tracking despite the sharp connectivity drop after relay failure.

`fig:gate1-safety-fx60-case`:

Representative matched recovery case selected by a median-positive-difference rule. The full multi-relation method re-establishes kill-chain closure shortly after relay failure, whereas the single-graph baseline loses the chain and times out.

## Limitations Text

This fixed-budget package focuses on graph/message mechanisms under a 3v1 strict-sensing relay-failure task. It does not by itself prove that the topology curriculum is the sole cause of the performance gain; the no-curriculum ablation is deferred. The current evidence also remains a 3DOF mechanism study rather than a full 4v2 red-blue system with online missile, radar, and 6DOF dynamics. These extensions should be treated as future work or as later scenario-depth experiments rather than as claims of the present result.

## Paper Positioning

Use this experiment as the core mechanism result for the current paper package:

1. Main comparison proves that the proposed graph/message architecture beats no-graph and single-graph baselines.
2. Role-pair gate ablation gives the cleanest mechanism evidence.
3. Task-support ablation provides supportive but statistically mixed evidence.
4. Failure-aligned curves explain why recovery improves.
5. Limitations are explicit about fixed-budget checkpointing, deferred no-curriculum ablation, and 3DOF scope.
