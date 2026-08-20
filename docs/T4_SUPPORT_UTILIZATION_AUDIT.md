# T4 — Task-Support Utilization Gap Audit

## Scope and frozen boundary

T4 is a **zero-training, existing-assets-only** audit. It preserves the T3 `D — NO_GO` conclusion: the task-support continuity evidence does not authorize a belief-state, recurrent-memory, temporal-graph-history, or continuity-auxiliary method route. T4 asks a narrower question: whether frozen UTR/SG actors use already legal task-support information differently across the pre-ranked good and weak seeds.

No environment was constructed, reset, or stepped. No optimizer update, rollout, new tape, checkpoint modification, reward change, actor-boundary change, or policy change occurred.

| Frozen rank | Seeds |
|---|---|
| Good | 2202, 2204 |
| Intermediate | 2201 |
| Weak | 2203, 2205 |

## Assets and boundary audit

The analysis used the five final frozen T1 UTR/SG checkpoints and their native raw-step telemetry. Each checkpoint reconstructed an identical 116,728-parameter actor/critic and loaded exactly. The audit selected 3,600 recorded actor-legal samples per seed (1,800 each for the pre-defined future-continuity labels), for 18,000 samples total.

Actor forward inputs were restricted to `actor.obs`, graph node/edge features, adjacency, relation adjacency, and graph role. `share_obs`, simulator truth, schedule/failure labels, terminal state, global routes, and future outcomes were excluded from actor forward passes. `chain_support_t`, current legal-information availability, and the future 16-step label were diagnostic strata only.

## Matched utilization comparison

Good and weak samples were compared only within overlapping strata of: failure family, failure-relative phase, attacker progress bin, actor-legal topology, future continuity label, current chain-support state, and current legal-information state. This gives 55 overlapping strata for each role; it is descriptive matching, not a causal intervention.

| Role | Good minus weak entropy | Action-norm difference | Confidence difference |
|---|---:|---:|---:|
| Scout (0) | -0.134 | +0.108 | +0.040 |
| Relay (1) | +0.144 | -0.161 | -0.011 |
| Attacker (2) | -0.250 | +0.147 | +0.080 |

The attacker difference is most relevant: under the same legal support/topology/progress strata, good seeds have lower action entropy, higher confidence, and higher action magnitude. The expected action components also differ (turn -0.340, climb -0.185, acceleration -0.044; good minus weak). This supports a policy-utilization difference, while not establishing that any individual component is causal.

## Seed-level consistency with existing performance evidence

Using the fixed T2 per-seed summaries only, failure-condition support sensitivity has descriptive Spearman correlation `+0.80` with each of `J_F0`, `J_OOD_mean`, and `J_OOD_worst`; its association with timeout is `-0.20`. There are only five training seeds, so these are direction checks rather than inferential statistics.

## Audit outcome

The pre-registered outcome is **U1 — SUPPORT_UTILIZATION_GAP_IDENTIFIED**. This finding is bounded: it identifies a reproducible gap in how frozen policies respond to recorded legal support states; it does not name, implement, or validate a follow-on method, nor does it reopen any T3-closed temporal route.

Primary machine-readable artifact: `results/development/t4_support_utilization_audit_run1/t4_utilization_audit.json`.
