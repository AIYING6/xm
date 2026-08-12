# Phase 2IA4 timestep-level cohort reconstruction report

## Scope

This is an independent, post-training reconstruction of the frozen strict
recovery endpoint from DEVELOPMENT_ONLY validation traces. It neither changes
the endpoint nor runs new training or new evaluation.

- Arms: `full_gate`, `no_role_gate`
- Development seeds: `101`, `202`, `303`
- Frozen scenarios: early, nominal, delayed, and late relay failure
- Validation suite: 50 episodes per arm × seed × scenario = 1,200 episodes
- Primary strict endpoint: pre-failure chain established AND post-failure loss
  AND post-loss chain recovery.

## Evidence integrity

The reconstruction consumed the 1,200-row raw episode table and all 24
arm/seed/scenario timestep trace files. Trace episode rows covered all 1,200
raw observations. The deliberately paired development episode IDs are unique
only within an arm; `(arm, development_episode_id)` was used as the audit key.

For every observation, independently reconstructed `pre_failure_chain_established`,
`chain_lost_after_failure`, recovery indicator, timing fields, event, and
censoring field matched the evaluator output exactly (0 mismatches).

The maintained audit tables are generated under
`results/development/role_gate_phase2ia4_validation/summaries/`:

- `timestep_cohort_classification.csv`
- `timestep_per_seed_scenario.csv`
- `timestep_arm_summary.csv`
- `V0_RISKSET_ADEQUACY.json`

## Reconstructed cohorts

| Arm | Episodes | A: no pre/post chain | B: pre-chain, no observed loss | C: strict recovered | D: strict unrecovered | E: first post-failure chain | Strict risk set C+D |
|---|---:|---:|---:|---:|---:|---:|---:|
| full_gate | 600 | 332 | 69 | 0 | 0 | 199 | 0 |
| no_role_gate | 600 | 311 | 79 | 0 | 0 | 210 | 0 |

Episodes in cohort B terminated before an active failure was observed or
otherwise showed no observed post-failure loss; cohort E established a chain
only after failure onset. Neither is eligible for the primary strict recovery
risk set. Success, return, timeout, and operational first establishment were
not substituted for strict recovery.

## V0 adequacy decision

Both arms have zero C+D episodes in every development seed and every frozen
scenario. Therefore every pre-registered V0 condition fails for both arms,
including the required non-zero risk set and the minimum total of 40.

**V0 RISK-SET ADEQUACY: FAIL.**

This is an observability/endpoint-eligibility failure for the present
development validation suite. It is not evidence that either Role-Gate arm is
better or worse.
