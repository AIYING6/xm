# FINAL_CONFIRMATORY_PREFLIGHT_V1_8

**Decision: BLOCKED_BY_PROTOCOL_INCONSISTENCY.** Formal training, formal
held-out evaluation, OOD, and manuscript changes were not started.

## 1. Comparator hierarchy — corrected before the block

The hierarchy is now frozen as:

1. **Primary architecture comparison:** corrected EA-RG Full vs corrected wider
   single-graph.
2. **Secondary matched-information comparison:** corrected EA-RG Full vs
   matched-information non-graph.
3. **System-level comparison:** corrected EA-RG vs standard MAPPO and HAPPO.

This order follows the claimed multi-relational representation innovation and
cannot be changed after formal results. MAPPO/HAPPO are not pure architecture
comparators.

## 2. Early/Nominal correction

The prior Early (anchor episodes 0–149) and Nominal (150–299) halves used the
same environment and failure parameters; only deterministic episode seeds
differed. They are not distinct scientific populations. The confirmatory unit
is now a single 300-episode population per method × trained-seed checkpoint.
The two halves may be shown only as non-scientific descriptive anchor halves.
The same 300 episode seeds are applied to each trained-seed checkpoint.

## 3. Failure-duration trace — blocking inconsistency

| Path | observed failure configuration |
|---|---|
| legacy formal protocol/evidence | relay agent 1, start 40, duration 80; dropout 0.30, delay 2; `attack_hold_steps=4`, `min_success_step=80` |
| corrected R6 engineering pilot | engineering-only start 4, duration 4; not a formal protocol |
| current corrected training defaults | duration 0 unless explicitly supplied; no single formal corrected duration is encoded |
| current confirmatory document | start 80, duration 4, `K=4`, tau 80/220 |
| nominal checkpoint-selection utility | no failure (`failed_blue_agent=-1`, duration 0), as expected for a nominal non-failure validation utility |

`node_failure_duration_steps=4` is numerically identical to the stable-window /
attack-hold `K=4`, while legacy formal evidence uses duration 80. The repository
does not establish that this equality was an intentional scientific design;
therefore duration 4 cannot be treated as settled.

If persistent failure exposure is the research question, the recommended author
decision is to align v1.8 with the legacy formal exposure (`start=40`,
`duration=80`, `K=4`) and retain tau 80/220. Under that design, tau=80 is a
restricted horizon from onset, not a label for the full active failure window.
The alternative transient design (`start=80`, `duration=4`) would make tau=80
post-failure and must be explicitly justified as such. No choice was made here.

## 4. Checkpoint-selection estimand — corrected

The uncensored-only endpoint gate is removed. Selection is frozen as:

1. validation RMST at tau=80;
2. establishment probability reported jointly with censoring rate;
3. validation RMST at tau=220;
4. earlier checkpoint on ties.

Validation remains independent of confirmation; confirmatory episodes never
select checkpoints. This is a censoring-aware rule, not conditional selection
on successful episodes.

## 5. Expanded no-graph invariance audit

The audit now uses the formal stochastic configuration (strict sensing and
target bottleneck, communication dropout 0.30, delay 2, radar dropout 0.10,
relay agent 1, start 40, duration 80), three fixed seeds `(431, 517, 809)`,
and per-seed pre-generated action sequences. Across 192 transitions, legacy
v1.6 and corrected v1.8 were exactly equal for obs, share_obs, rewards, done,
termination reason, blue/red states, sensing outcome, failure timing,
attack-window state, and emitted info fields.

Result: `NO_GRAPH_BASELINE_INVARIANCE_AUDIT_V1_8: PASS`.
MAPPO/HAPPO checkpoint reuse is therefore approved **conditional on resolving
the failure-duration protocol and using this same formal configuration**. Any
future change to environment parameters revokes reuse.

## 6. Confirmatory episode unit and bootstrap

The unit is **300 episodes per method × trained-seed checkpoint**, not 300
episodes for an entire method. With three training seeds, each corrected method
has 900 evaluation episodes and the three-method corrected matrix has 2,700
episodes. The hierarchy is:

```text
training seed → selected checkpoint → 300 shared confirmatory episode seeds
```

The same 300 episode seeds are applied to all three checkpoints within a method
comparison. Hierarchical bootstrap resamples training seeds first, then episodes
within the selected seed, preserving training seed as the independent unit.

## Final status

`BLOCKED_BY_PROTOCOL_INCONSISTENCY`: author must choose and explicitly freeze
the failure exposure design before v1.8 formal training. No architecture change
is recommended, and no formal run may begin until that decision updates the
protocol version consistently across legacy reference, corrected training,
validation, confirmatory evaluation, endpoint, and tau interpretation.
