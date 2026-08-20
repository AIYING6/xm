# T2 Baseline Mechanism Analysis

## Scope

T2 is a **zero-training, existing-assets-only** analysis. It streams the
source-closed T1 step telemetry and writes only offline derivatives. It does
not instantiate an environment, replay a checkpoint, generate a rollout, or
alter T1 outputs.

- Raw source: five T1 `raw_step_telemetry.jsonl` files, 6,000 evaluated
  episodes.
- Derived evidence: `results/development/t2_telemetry_native_mechanism_final`.
- Source analysis: `scripts/analyze_t2_t1_native_mechanism.py`.
- Failure families intentionally examined: canonical F0 `44/80`, timing
  `28/80`, and duration `44/120`.
- Alignment: \(\tau=t-t_{\mathrm{actual\ onset}}\). All 5,460 failure records
  that were exposed had actual onset equal to their scheduled onset; there
  were zero onset mismatches. For non-exposed pre-trigger terminations, the
  scheduled onset defines only the pre window; these episodes are retained.

## Exact telemetry schema and access classification

| Raw field | Classification | T2 use / boundary |
|---|---|---|
| `protocol`, `schema_version`, `episode_id`, `scenario`, `timestep`, `post_step`, `scheduled_failure_onset`, `scheduled_failure_duration` | ENVIRONMENT_DIAGNOSTIC | Evaluation provenance and offline time alignment; never actor input. |
| `actor.classification` | ACTOR_LEGAL | Declares the legal-actor container. |
| `actor.obs`, `actor.graph_node_feat`, `actor.graph_edge_feat`, `actor.graph_adj`, `actor.graph_relation_adj`, `actor.graph_role` | ACTOR_LEGAL | Frozen decentralized actor inputs. T2 does not add any of them to a policy. |
| `actor.share_obs` | ACTOR_LEGAL / CRITIC_ONLY | CTDE critic input under the frozen contract; explicitly not an actor input. |
| `action_index`, `applied_action_components` | ACTOR_LEGAL OUTPUT | Executed policy outputs; used only to derive action magnitude/change offline. |
| `control_effort`, `movement_distance`, `reward_sum_step`, `failure_active_post`, `terminal` | ENVIRONMENT_DIAGNOSTIC | Outcome/event fields; not actor information. |
| `diagnostic.classification`, `diagnostic.blue_position`, `red_position`, `blue_speed`, `blue_heading`, `blue_gamma` | ENVIRONMENT_DIAGNOSTIC | Used only for role-motion and target-relative analysis. |
| `diagnostic.info.node_failure_active`, `chain_support_t`, `attacker_cache_paths_t`, `attacker_legal_target_information_t`, `target_cache_age_mean`, `collision`, `timeout`, `constraint_violation`, `success`, `step` | ENVIRONMENT_DIAGNOSTIC | Used only for offline mechanism and safety analysis. Exact diagnostic values must never be added to the actor. |
| Failure-aligned windows; role path/net displacement; target-relative progress; action magnitude/change; path-switch and dwell fractions; terminal-window precursors; descriptor-paired GOOD-minus-WEAK statistics | DERIVED_OFFLINE | Deterministic functions of the preceding existing fields. |

## Technical validity and denominators

There are 1,100 scheduled failure episodes per seed. The risk-set trigger rate
is 100% for every seed: 5,460/5,460 episodes alive immediately before onset
triggered correctly. The only pre-trigger loss is seed 2202's 40 collisions;
they remain part of unconditional safety and score summaries. No exposed
episode had an actual onset different from its scheduled onset.

## Failure-aligned GOOD-vs-WEAK evidence

The comparison unit is first an episode mean and then a training-seed mean;
raw timesteps are not treated as independent replicates. For each same
descriptor/episode-id, the table also tests the difference between the two
GOOD and two WEAK policy means. “4/4” means every GOOD-versus-WEAK seed pair
has the same direction.

| Link in the temporal chain | Window | F0 44/80 | Timing 28/80 | Duration 44/120 | Seed-pair direction |
|---|---|---:|---:|---:|---|
| GOOD already has more `chain_support_t` | pre [-20,0) | +0.628 | +0.277 | +0.628 | 4/4 positive in all families; descriptor-positive fraction 0.99–1.00 |
| GOOD is closer to target (attacker distance; lower is better) | pre | −7,088 | −3,192 | −7,088 | 4/4 negative in all families; every paired descriptor negative |
| GOOD has more target approach before failure | pre | +4,026 | +4,455 | +4,026 | 4/4 positive in all families |
| GOOD preserves legal target information immediately after the topology event | early [0,20) | +1.000 | +1.000 | +1.000 | 4/4 positive; every paired descriptor positive |
| GOOD obtains direct path use early | early | +0.280 | +0.322 | +0.280 | 4/4 positive in all families |
| GOOD retains support through the post-event middle | mid [20,60) | +0.387 | +0.349 | +0.387 | 4/4 positive; paired positive fraction 1.00 |
| GOOD retains legal information through the middle | mid | +0.626 | +1.000 | +0.626 | 4/4 positive; paired positive fraction 1.00 |
| GOOD retains support late | late [60,120) | +0.428 | +0.371 | +0.500 | 4/4 positive; paired positive fraction 0.989 |
| GOOD terminal-80 has more legal information | terminal last 80 | +0.347 | +0.386 | +0.351 | 4/4 positive; paired positive fraction 0.99–1.00 |
| GOOD terminal-80 is closer to target | terminal last 80 | −2,672 | −2,123 | −3,104 | 4/4 negative in all families |

All differences are GOOD minus WEAK. They are descriptive estimates from two
GOOD and two WEAK training seeds, not p-values or causal effects.

### Earliest reliable divergence

The earliest reliable separation is **pre-onset task-support and attacker
progress**. The event then exposes a second, sharper difference in the first
20 post-onset steps: both GOOD seeds preserve legal information and obtain
some direct path use, whereas both WEAK seeds have zero mean legal target
information and zero direct-path fraction in all three examined families.

This supports the following descriptive sequence:

\[
\text{weaker pre-event task-support/progress}
\rightarrow \text{no early legal-information continuity after topology switch}
\rightarrow \text{persistent support deficit and poorer attacker progress}
\rightarrow \text{low-return, timeout-heavy trajectories}.
\]

It is deliberately not stated as `failure -> information loss`: the frozen
task permits legal compensation, and the evidence shows policy-dependent
continuity/reorganization rather than universal loss.

## Required counterexamples and rejected explanations

1. **Direct topology availability alone is insufficient.** In the late
   `44/120` duration condition, WEAK direct-path fraction is higher than GOOD
   (0.986 vs 0.456), while WEAK support remains much lower (0.046 vs 0.546)
   and its return is poorer. A direct edge is therefore not the explanatory
   endpoint; how task support is maintained after the switch matters.
2. **Low action change is not a stable explanation.** Attacker action-change
   differences do not retain one sign across all GOOD/WEAK seed pairs in the
   pre, early, mid, and late windows. T2 rejects generic “smoother actions” or
   “less oscillation” as a primary target.
3. **Timeout is not the mechanism.** GOOD seed 2204 still times out in 97.33%
   of its T1 episodes, yet has much higher return than both WEAK seeds and
   retains the support/information pattern. Conversely, GOOD seed 2202 has
   6.08% collision and 3.64% pre-trigger collision. Safety and terminal flags
   must remain separate outcomes, not substituted for the behavioral chain.
4. **The pre-event separation limits causal strength.** GOOD policies are
   already closer to the target and have more support before onset. Thus T2
   cannot isolate an effect caused solely by the topology event from broader
   training-seed competence. This is the reason for M2 rather than M1.

## Primary evidence-limited conclusion

There is a repeated, topology-relevant behavior signal: weak policies fail to
establish/maintain task support before the event and do not retain legal target
information in the immediate post-switch window. The signal repeats in F0,
timing, and duration families, across both GOOD and both WEAK seeds, and
precedes the late/terminal deficits. It is nevertheless observational and
partly pre-existing, so it cannot by itself identify the causal learning
defect or prescribe an algorithm.
