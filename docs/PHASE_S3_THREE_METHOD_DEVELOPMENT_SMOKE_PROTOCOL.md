# Phase S3 Three-Method Development MARL Smoke Protocol

**Protocol ID:** `PHASE-S3-TMDS-V1`  
**Status:** FROZEN BEFORE LAUNCH  
**Scope:** development-only learnability and robustness-signal screening

## Scientific question

Can MAPPO, Parameter-Matched Single-Graph, and Multi-Relation Full learn the
frozen topology-reconfiguration task, and does Full show a coherent reason to
continue to canonical confirmation?

## Fixed training contract

- methods: MAPPO (`no_graph`, width 64), Parameter-Matched Single-Graph
  (`single`, width 115), Multi-Relation Full (`multi_relation`, width 64);
- development seeds: `1501`, `1502`, `1503` only;
- nine independent runs: 3 methods × 3 seeds;
- 782 updates × 4 environments × 64 rollout steps = **200,192 environment
  steps** per run;
- frozen business-grounded geometry, strict sensing, legal target-information
  bottleneck, Relay-dependent task semantics, target policy `straight`;
- training failure intervention ON: Relay 1, step 44, 80 steps;
- identical reward, dynamics, environment, PPO hyperparameters, and budget;
- no resume, no initialization checkpoint, no early stopping, no in-training
  evaluation, no best-checkpoint selection, and no seed exclusion.

The fixed final update is the only checkpoint evaluated.

## Paired final evaluation

Each final checkpoint is evaluated on 100 deterministic nominal/failure pairs.
Within a pair, episode ID, initial state, target realization, and exogenous
processes are shared. Only the failure intervention differs. Raw episode and
timestep provenance are mandatory.

Primary diagnostic is `Delta_J = J_nominal - J_failure`. Nominal competence
(`J_nominal`) and failure competence (`J_failure`) are always inspected with
`Delta_J`; a low nominal score cannot be called robustness. Mechanism
diagnostics include edge/path composition, task-chain availability, cache age,
control effort, traveled distance, and safety outcomes.

## S3 decision rule

S3 is not paper evidence and does not require formal significance testing.
It passes to S4 only if all three methods train stably and Full has
non-degenerate nominal competence plus a coherent robustness signal relative
to both MAPPO and matched Single-Graph across the development seeds. If Full
does not show such a signal, S4/canonical training remain NO-GO. No S2 setting,
endpoint, metric, seed set, failure timing, or checkpoint rule may be changed
after a result is observed.

Role-Gate is recorded as part of the current Full implementation but is not
tested or claimed in S3. Phase 3A canonical training remains NO-GO.
