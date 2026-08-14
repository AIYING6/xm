# DRTP-SG-MAPPO Training Maturity Addendum

## 0. Status and precedence

**FROZEN DEVELOPMENT-BUDGET ADDENDUM / LONG TRAINING AUTHORIZED ONLY UNDER THIS DOCUMENT.**

This addendum is bound to `docs/DRTP_SG_MAPPO_METHOD_CONTRACT.md`,
`docs/DRTP_SG_MAPPO_IMPLEMENTATION_REPORT.md`, and implementation commit
`8267887`. It freezes only the rule for deciding whether the common UTR/DRTP
development budget is mature. It does not change the method, optimizer, task,
sampler groups, evaluation definitions, or performance retention criteria in the
method contract. If there is a conflict, the method contract governs every
scientific definition; this addendum governs only the common training-budget
extension decision.

The stage remains development-only. Held-out seeds, canonical seeds, formal
five-seed experiments, paper results, and any new candidate method are outside
scope.

## 1. Frozen development arms

| arm | seed | sampler mode |
|---|---:|---|
| UTR-SG-MAPPO | 1901 | `utr` |
| UTR-SG-MAPPO | 1902 | `utr` |
| DRTP-SG-MAPPO | 1901 | `drtp` |
| DRTP-SG-MAPPO | 1902 | `drtp` |

Every run is from scratch and uses the identical matched Single-Graph agent
(**116,728 trainable parameters**), PPO configuration, S2 environment, reward,
failure semantics, actor information boundary, seven topology training groups,
within-group members, and fixed 50% nominal exposure anchor. UTR and DRTP
differ only in fixed-uniform versus bounded-adaptive conditional failure-group
weights.

All runs prohibit resume, early stopping, seed exclusion, checkpoint promotion,
best-checkpoint selection, and method-specific extra training. The final
checkpoint at the common frozen budget is the only checkpoint used for the
UTR-versus-DRTP method comparison.

If the symmetric extension rule triggers, the next common budget is implemented
as four new **from-scratch** trajectories with the same arm/seed assignments and
immutable configuration. No optimizer, sampler, environment, or model state is
loaded from a previous-budget run. This is the only interpretation consistent
with the frozen no-resume rule; the earlier-budget artifacts remain retained for
curve analysis and are never promoted into the next-budget training trajectory.

## 2. Development evaluation tape

Before the first development training run, generate and freeze exactly one
non-canonical paired development tape:

| resource | frozen value |
|---|---|
| base-ID namespace | `420000–420099` |
| paired conditions | nominal, F0, four timing, four duration, two compound conditions |
| purpose | development evaluation only |
| manifest requirements | condition table, S2 failure semantics, `canonical=false`, forbidden namespaces, SHA256 |

The held-out namespace `430000–430099` must not be generated, inspected, or
used in this stage.

## 3. Fixed milestones and first maturity check

All four arms begin with the frozen rollout contract `4 environments x 64 steps`.
The first common budget is **3,907 updates = 1,000,192 environment steps**.
Each run saves fixed milestones closest to:

| milestone label | target update | purpose |
|---|---:|---|
| approximately 500k | 1,954 | learning-curve analysis only |
| approximately 750k | 2,930 | learning-curve analysis only |
| final 1M | 3,907 | final checkpoint at the 1M common budget |

No milestone can be promoted, selected, or substituted for a final checkpoint.
At 1M, the four final checkpoints are evaluated on the same frozen 420k tape.

The primary maturity metric is the primary robustness metric already frozen by
the method contract. If that contract does not supply a separate maturity
metric, this addendum fixes **pooled `J_OOD_worst`** as the primary maturity
metric. `J_nominal`, `J_F0`, `J_OOD_mean`, failure exposure, and all safety
metrics remain mandatory accompanying checks.

## 4. Pre-registered common-budget extension rule

Let `M_b(method)` denote the pooled primary maturity metric at common budget
`b`, computed only from final checkpoints on the 420k tape. At the 1M boundary,
an extension is mandatory if either UTR or DRTP satisfies both:

\[
\frac{M_{1\mathrm{M}}-M_{750\mathrm{k}}}
{|M_{750\mathrm{k}}|+10^{-8}} \ge 0.05
\]

and the improvement direction is non-negative for **both** development seeds.

For this rule, milestone evaluation is curve-only: it decides whether the
budget is mature and never chooses a method-result checkpoint. The rule is
applied symmetrically. If either method triggers it, **both methods and both
seeds** continue from their own fixed trajectory to the next shared budget.

An observed change that fails either the pooled 5% threshold or the two-seed
direction requirement does not trigger an extension. No result may alter this
threshold, its denominator, its aggregation, or the seed-consistency rule.

## 5. 2M and 3M limits

If the 1M rule triggers, all four arms start fresh 2M trajectories at **7,813
updates = 2,000,128 environment steps**, with fixed curve-only milestones:

| common budget | additional required milestones |
|---|---|
| 2M | update 5,859 (approximately 1.5M) and final update 7,813 |
| 3M, only if triggered at 2M | update 9,766 (approximately 2.5M) and final update 11,719 (3,000,064 steps) |

The same 5% pooled-primary-metric and both-seed-direction rule is applied from
approximately 1.5M to final 2M. If either method triggers, all four arms start
fresh 3M trajectories under the same assignments and configuration. At 3M, no
automatic extension is permitted. If either method still shows the stipulated
sustained improvement from approximately 2.5M to final 3M, the sole recorded
conclusion is:

> `training maturity unresolved at <=3M`.

The project then stops for a separately authorized decision; it may not extend
to 5M/10M, choose an intermediate checkpoint, or claim mature final performance.

## 6. Fair comparison and development decision

The final UTR-versus-DRTP comparison must use the same common frozen mature
budget for every arm: all four 1M finals if mature at 1M; otherwise all four 2M
finals; otherwise all four 3M finals. The forbidden comparison includes, for
example, UTR at 1M versus DRTP at 2M, or a method-selected milestone.

At the jointly frozen budget, apply every pre-registered development-to-held-out
row in the method contract without modification:

- nominal competence;
- canonical F0 retention;
- OOD mean and OOD worst;
- self-reference ratios;
- collision, timeout, and constraint safety;
- exposure reporting and seed consistency.

Because UTR and DRTP see the same seven topology-group universe and identical
nominal anchor, an observed DRTP advantage cannot be attributed to broader
topology-condition exposure. Only the adaptive versus uniform group weighting
may explain a difference within this contract.

## 7. Required artifacts and stop condition

For each arm, retain run-completeness declarations, immutable configuration and
sampler hashes, realized group/member counts, final and milestone checkpoint
SHA256 values, and learning-curve logs. The final report must provide each seed
and pooled `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`, safety,
failure-exposure, episode/path telemetry, DRTP-versus-UTR effects, and the
development retention verdict.

It must additionally record the 1M maturity verdict, any triggered 2M/3M
milestones, and the final common mature budget. Completion stops after this
development decision. It does **not** authorize the held-out seeds `2001/2002/2003`,
the 430k tape, canonical seeds `0–4`, OOD formal studies, or paper-scale
training.
