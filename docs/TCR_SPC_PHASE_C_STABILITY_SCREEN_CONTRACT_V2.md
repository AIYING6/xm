# TCR/SPC Phase-C Stability Screen Contract v2

- Status: prospective contract; frozen as a protocol amendment only
- Purpose: define a technically valid exposure estimand after the v1 exposure-gate adequacy review
- Authorization: this document does not authorize re-analysis, training, 3M, held-out, canonical, or formal experiments
- Historical v1 status: permanently retained as TECHNICAL INVALID

## 1. Historical boundary

Phase-C v1 used an all-scheduled-episode exposure gate. The forensic audit found 69 natural pre-trigger collision episodes and no evaluator/trigger defect. Therefore v1 remains a valid historical report under its own contract, but its all-episode exposure quantity is not reused as the sole evaluator technical-validity quantity.

No v2 result may overwrite, relabel, or retroactively repair the v1 decision.

## 2. Frozen method and experiment invariants

The following remain unchanged:

- UTR-SG-MAPPO, SPC-SG-MAPPO, and TCR-SG-MAPPO only;
- matched Single-Graph actor/critic with 116,728 parameters;
- PPO hyperparameters;
- 4x64 rollout and stratified actor-minibatch bookkeeping;
- fixed 50% nominal exposure;
- uniform six-group failure exposure;
- environment, reward, failure semantics, and actor information boundary;
- Phase-C final checkpoints;
- Phase-C development tape 440000–440099 and its frozen conditions;
- development seeds 2002, 2101, 2102, 2103, 2104;
- no canonical seeds, held-out seeds, new encoder, new loss, new curriculum, or threshold tuning.

This v2 document changes no algorithm and no checkpoint.

## 3. Two mandatory exposure quantities

For each method × seed × failure condition, retain every scheduled episode in the raw table.

### 3.1 Onset risk set

R_(m,s,c) = { i in F_sched,(m,s,c) : i is alive immediately before onset }.

Operational evaluator definition:

i is in R_(m,s,c) if and only if terminal_step_i >= scheduled_onset_c.

The boundary convention must be implemented identically for all methods and documented in the evaluation manifest.

### 3.2 Trigger validity

V_trigger,(m,s,c) = number of i in R_(m,s,c) with failure active at least once / |R_(m,s,c)|.

This is the technical evaluator/trigger validity quantity.

- If |R| > 0, every risk-set episode must be checked for correct trigger activation.
- If |R| = 0, trigger validity is not estimable for that cell and must be reported as an adequacy warning.
- An episode with terminal_step < onset is not a trigger failure; it is a pre-trigger policy termination.

## 4. Mandatory policy performance and safety reporting

All scheduled episodes remain in unconditional metrics. No pre-trigger episode may be removed or censored.

For nominal, F0, and every OOD condition, report:

- overall J over all evaluation episodes;
- success, where defined by the frozen contract;
- collision;
- pre-trigger collision;
- timeout;
- constraint violation;
- pre-trigger termination for any terminal reason;
- fraction surviving to onset, |R| / |F_sched|;
- trigger validity V_trigger among R;
- risk-set cardinality;
- per-condition raw episode counts.

The unconditional J, safety, and exposure-denominator tables must remain linked to the complete raw episode manifest.

## 5. Conditional robustness analysis

Any post-failure robustness quantity that conditions on the failure being encountered must be computed on R, not on all scheduled episodes.

The report must show both namespaces:

1. Unconditional: all-episode performance and safety, including pre-trigger collisions.
2. Conditional: post-onset failure response among R, with V_trigger, risk-set size, and survival fraction shown beside it.

Conditional estimates are descriptive of post-onset response. They cannot by themselves establish overall robustness or safety.

A method with a smaller risk set cannot improve its overall standing by receiving a more favorable conditional denominator.

## 6. Preserved decision logic

The original v1 catastrophic-seed, safety, and seed-consistency logic remains unchanged, including:

- paired reference to UTR on the same training seed;
- the frozen catastrophic performance combinations;
- the frozen timeout/safety conditions;
- seed-level inference rather than pooled episodes;
- no seed exclusion;
- no checkpoint promotion.

No superiority threshold is added, removed, or inferred from the current TCR result.

Where a decision table uses post-onset conditional metrics, the table must also display the corresponding unconditional all-episode metrics and risk-set adequacy. Conditional results cannot override an unconditional safety failure.

## 7. Anti-gaming safeguards

The following are mandatory:

- complete raw episode retention;
- pre-trigger collision as a separate safety diagnostic;
- risk-set size and survival fraction per method × seed × condition;
- trigger validity only within R;
- identical tape and paired episode IDs;
- no policy-dependent episode deletion;
- no post-result risk-set threshold selection;
- no claim based only on J among exposed episodes;
- explicit flag for empty or small risk sets;
- audit trail linking each aggregate to episode-level records.

Any future minimum risk-set adequacy rule must be frozen in a separate prospective amendment before analysis and must apply symmetrically to UTR, SPC, and TCR. This v2 contract does not set a new favorable numerical threshold.

## 8. Checkpoint and authorization boundary

The v2 contract permits only a separately authorized re-analysis of the existing Phase-C 1M final checkpoints. It does not authorize:

- new training;
- 1M to 3M continuation;
- held-out seeds;
- canonical seeds;
- new tape generation;
- algorithm, PPO, environment, reward, or failure-semantics changes;
- checkpoint promotion or selection.

## 9. Final status

- Phase-C v1 historical decision: TECHNICAL INVALID — immutable
- v2 exposure validity: risk-set trigger validity
- pre-trigger collision: mandatory policy safety diagnostic
- overall performance denominator: all scheduled episodes
- post-onset conditional analysis: risk set R only
- next action: stop and wait for separate authorization
