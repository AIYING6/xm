# Training and Evaluation Protocol

Last updated: 2026-08-02

## Purpose

This document defines the training, validation, testing, and change-control
rules for the next formal experiment cycle.

The main objective is to prevent unplanned mid-run design changes from making
results scientifically ambiguous.

## Evidence Levels

Use these labels consistently:

```text
development evidence
freeze rehearsal evidence
formal validation evidence
formal test evidence
```

Only formal test evidence may support final paper claims.

## Development Stage

Allowed:

- change reward weights;
- change scenario difficulty;
- change observation schema;
- change graph encoder;
- change BC protocol;
- inspect failures and add tests;
- run short probes and smoke experiments.

Not allowed:

- use results as final method comparison;
- choose final test scenarios based on favorable development outcomes;
- mix pre-hardening and post-hardening checkpoints in formal tables.

## Freeze Rehearsal Stage

Purpose:

```text
verify that the protocol can run end to end before expensive formal training
```

Minimum rehearsal:

- methods: MAPPO, Single-Graph, EA-RG-MAPPO, HAPPO if available;
- seeds: 0 only;
- budget: 5% to 10% of formal budget;
- scenario: strict sensing + relay failure + dropout/delay;
- outputs: training logs, checkpoint selection, validation/test CSVs, schema
  audit, provenance, artifact gate.

Rehearsal evidence is not a paper result.

Maintained command-generation mode:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode freeze_rehearsal --methods mappo single_graph ea_rg_mappo happo --seeds 0 --include-sweeps --out-csv results/freeze_rehearsal_command_manifest.csv --out-md docs/FREEZE_REHEARSAL_COMMAND_MANIFEST.md
```

Execution and pass/fail criteria are recorded in:

```text
docs/FREEZE_REHEARSAL_PLAN.md
```

## Formal Freeze Stage

Freeze requires:

- clean Git state;
- passing information-boundary tests;
- passing config audit;
- passing checkpoint-selection schema audit;
- passing smoke tests;
- updated protocol docs;
- fixed method list;
- fixed metrics;
- fixed validation/test split.

Create a tag only after those checks pass.

Suggested tag pattern:

```text
formal-experiment-freeze-vN
```

## Formal Training Stage

Formal training must use generated command manifests rather than ad hoc shell
commands.

Primary generator:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode formal_bstar --methods mappo single_graph ea_rg_mappo happo --seeds 0 1 2 3 4 --include-sweeps
```

If starting with a lower-cost development-budget cycle:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode dev_1m --methods mappo single_graph ea_rg_mappo happo --seeds 0 1 2 --include-sweeps
```

Training must be launched through the audited manifest runner where possible.

## Checkpoint Selection

Validation selects checkpoints.

Test only evaluates validation-selected checkpoints.

The selection schema is defined in:

```text
configs/paper/checkpoint_selection_schema.yaml
```

The schema currently requires:

- validation must not use test results;
- test must use a validation `selected_checkpoints.csv`;
- selection score and tie-breaker must be recorded;
- selected checkpoint update and path must be recorded.

## Primary Metrics

Primary paper metrics:

- kill-chain recovery rate;
- restricted mean recovery time.

Secondary metrics:

- success rate;
- timeout rate;
- completion time;
- post-failure tracking rate;
- attacker fresh target-cache ratio;
- chain-closed probability;
- communication connectivity;
- collision rate;
- flight-envelope violation rate;
- mean message age.

Reward is a training diagnostic, not a primary paper metric.

## Statistical Reporting

Use seed-aware reporting:

- show seed-level metrics;
- report mean and confidence interval;
- use paired seed-level comparisons as secondary evidence;
- use hierarchical bootstrap if episode-level and seed-level data are both used.

Do not claim significance from a single favorable seed.

## Change Control

After freeze:

Allowed without invalidating formal runs:

- fix plotting labels;
- add documentation;
- add non-invasive audit scripts;
- regenerate tables from unchanged source CSVs.

Requires new freeze and invalidates affected runs:

- actor observation change;
- graph feature change;
- reward change;
- termination or success-definition change;
- communication/sensing/failure model change;
- baseline architecture or training-budget change;
- checkpoint-selection rule change;
- validation/test split change;
- discovered information leak.

Performance-improvement ideas after freeze must go to a development branch or a
new experiment cycle.

## If Formal Results Are Weak

Do not patch the running protocol.

Required process:

1. complete the scheduled validation/test analysis;
2. identify whether the issue is environment reachability, training instability,
   weak mechanism, or overly strong baseline;
3. document the failure;
4. decide whether to revise the scientific claim or start a new development
   cycle;
5. create a new freeze only after design changes are complete.

## Minimum Go/No-Go Criteria

Proceed to formal training only if:

- information-boundary audit passes;
- baseline fairness protocol is satisfied;
- freeze rehearsal runs end to end;
- all main methods can train and evaluate;
- geometric/rule feasibility remains reachable;
- no known result-generating script depends on test-set selection leakage.

Stop and redesign if:

- EA-RG-MAPPO only beats no-graph but consistently loses to Single-Graph;
- task-support and role-pair gate ablations do not support the proposed
  mechanism;
- failure recovery depends on stale target cache rather than fresh sensing or
  delivered communication;
- HAPPO or parameter-matched baselines expose an unfair capacity advantage.
