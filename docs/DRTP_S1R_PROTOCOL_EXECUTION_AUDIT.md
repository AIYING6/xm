# DRTP S1-R — Protocol Execution Audit

## Decision

`F_PROTOCOL_UNDERSPECIFIED`

`STOP — no G/B freeze, no telemetry smoke, no reference reproduction, and no
scientific training runs authorized.`

Audit base commit: `24f7841`  
Audit branch: `codex/drtp-seed-s1r-exec`  
Training started: **NO**

## Scope

This audit checks whether
`docs/DRTP_S1R_SEED_RELIABILITY_CAUSAL_SCREEN_PROTOCOL.md` is sufficiently
machine-executable before any later stage. The attached S1-R execution
contract requires an immediate stop if any gate definition is only qualitative
or if the training/evaluation contract is not frozen.

## Completeness matrix

| Item | Present | Machine-executable | Result |
|---|---:|---:|---|
| G selection rule | yes | no | missing deterministic tie-break and exact paired-margin threshold |
| B selection rule | yes | partial | “unfavorable” and catastrophic qualification lack complete numeric gate |
| rescue definition | partial | no | no formula, effect threshold, or comparison window |
| reverse degradation definition | partial | no | no formula, effect threshold, or comparison window |
| trajectory precursor consistency | partial | no | no fixed precursor metrics, time windows, tolerance, or pass rule |
| primary metrics | partial | no | protocol does not freeze the exact metric aggregation and direction rules |
| secondary metrics | no | no | no complete frozen list and aggregation contract |
| evaluation tapes | no | no | S1-R does not bind a tape manifest/hash or episode namespace |
| evaluation conditions | partial | no | condition names are discussed but not bound to a manifest/hash |
| milestones | no | no | no exact milestone set is frozen in the protocol |
| training budget | no | no | no exact step-aligned budget is frozen |
| RNG stream definitions | partial | no | stream names exist, but derivation, seeds, and state serialization are absent |
| technical-invalid rules | partial | partial | examples exist, but machine checks and precedence are not fully specified |
| PASS/FAIL gates | partial | no | downstream gates depend on the missing definitions above |
| STOP rules | yes | yes | stop instruction is clear once a failure is established |

## Blocking findings

### 1. G/B cannot be frozen deterministically

The protocol requires cross-tape favorable/unfavorable behavior and refers to
paired margin and catastrophic qualification, but does not define the exact
numeric margin, the timeout/safety combination, or a deterministic tie-break
when multiple seeds qualify. Selecting G or B from the observed results would
therefore be post-hoc.

### 2. Rescue and reverse degradation are not estimands

The protocol says that `B + good source` must improve and `G + bad source` must
worsen, but does not define whether improvement is measured by absolute return,
paired degradation, timeout, a standardized effect, or a composite. It also
does not define the minimum effect, confidence/replicate rule, or the interval
over which the comparison is made.

### 3. Precursor consistency is qualitative

“Same-direction precursor” is not bound to a field set, milestone window,
episode alignment rule, tolerance, or pass threshold. A post-hoc search could
therefore manufacture a precursor after seeing the trajectories.

### 4. Training and evaluation contracts are incomplete

The protocol does not freeze the exact S1-R training budget, step-aligned
milestones, RNG tuple derivation, runtime-state format, or an evaluation tape
manifest/hash. These cannot be inferred from REL-A0 without changing the S1-R
contract.

## Historical and scientific boundaries preserved

- REL-A0 remains complete and unchanged.
- DRTP remains described as high mean/median gain with reproducible seed
  sensitivity.
- seed2002 remains a catastrophic training-seed candidate, not a proven root
  cause.
- policy-basin divergence remains a candidate hypothesis only.
- No new algorithm, RNG intervention, checkpoint, tape, or training result was
  created by this audit.

## Required next action

Do not proceed to P1–P6. If S1-R is still desired, first issue a new versioned
protocol amendment that freezes numeric G/B, rescue, reverse-degradation, and
precursor criteria, plus exact budgets, milestones, RNG derivation, runtime
state, and evaluation tape hashes. That amendment requires separate review;
it must not be filled in after observing S1-R results.
