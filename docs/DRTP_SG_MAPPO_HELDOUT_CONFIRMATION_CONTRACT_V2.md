# DRTP-SG-MAPPO Held-Out Confirmation Contract v2

## 0. Status, rationale, and historical record

**FROZEN FORWARD-LOOKING CONTRACT / HELD-OUT TRAINING NOT AUTHORIZED BY THIS
DOCUMENT ALONE.**

This contract follows the self-reference adequacy review.  It explicitly
preserves the v1 development record as
**`DEVELOPMENT_RETENTION_NO_GO`** under
`DRTP_SG_MAPPO_METHOD_CONTRACT.md`; no historical decision is relabelled or
overwritten.

The only v2 change is metric classification: `R_OOD_mean` and `R_OOD_worst`
remain fully reported relative-retention diagnostics, but are no longer hard
necessary gates for absolute robustness superiority.  This is a structural
metric correction derived from monotonicity, not a threshold chosen from the
observed 10M values.  No new superiority threshold is introduced.

## 1. Immutable method and task

UTR-SG-MAPPO and DRTP-SG-MAPPO retain exactly the v1 method contract:

- matched Single-Graph architecture, **116,728 parameters**, role gate `none`;
- identical PPO/optimizer and all frozen hyperparameters;
- the same seven topology groups and within-group members;
- identical 50% nominal anchor; UTR uniform conditional weights versus DRTP
  bounded exponentiated weighting only;
- unchanged S2 environment, reward, failure semantics, observation/actor and
  critic information boundaries, graph legality, and evaluation aggregation;
- no new encoder, loss family, reward, curriculum, PPO sweep, checkpoint
  promotion, seed exclusion, or result-dependent protocol change.

## 2. Held-out trajectories and strict budget

Only after separate authorization, train these twelve trajectories from scratch:

| arm | held-out training seeds | budget per run |
|---|---|---:|
| UTR-SG-MAPPO | 2001, 2002, 2003 | 39,063 updates = 10,000,128 environment steps |
| DRTP-SG-MAPPO | 2001, 2002, 2003 | 39,063 updates = 10,000,128 environment steps |

The 10M budget is the already frozen common maturity observation budget.  Each
run is a strict-continuous trajectory from update zero with runtime-state
persistence enabled from its initial invocation.  Only its 10M final
checkpoint is eligible for the UTR-versus-DRTP held-out comparison; milestones
are curve-only and cannot be promoted.

Before separate authorization, held-out seeds `2001/2002/2003` must not be
used in training, smoke tests, parameter selection, tape generation, or
inspection.  Canonical seeds `0–4` remain prohibited.

## 3. Frozen held-out evaluation resource

After, and only after, separate held-out launch authorization, generate the
non-canonical held-out paired tape `430000–430099`.  It reuses the v1
condition table: nominal, F0 `(44,80)`, four timing, four duration, and two
compound conditions.  It must bind the deterministic ID namespace, all 100
base IDs across every condition, failure semantics, SHA256, `canonical=false`,
and all prior forbidden namespaces.  It must not overlap development tape
`420000–420099`.

The primary inference unit is the **training seed** (`n=3`), never the 100
correlated episode rows.  All planned nominal/failure pairs are retained;
failure exposure is reported separately and cannot filter an endpoint.

## 4. Primary endpoints and unchanged hard gates

For each training seed, report `J_nominal`, `J_F0`, `J_OOD_mean`,
`J_OOD_worst`, collision, timeout, constraint violation, failure exposure, and
the frozen topology/path telemetry.  Apply the following unchanged v1
development-to-held-out thresholds to the pooled held-out comparison:

| domain | v2 held-out hard criterion |
|---|---|
| nominal retention | pooled `J_N(DRTP)/J_N(UTR) >= 0.95`; no seed below `0.90` |
| F0 retention | pooled `J_F0(DRTP)/J_F0(UTR) >= 0.98`; no seed below `0.90` |
| OOD mean | pooled ratio `>= 1.05`; at least 2/3 DRTP−UTR seed directions non-negative |
| OOD worst | pooled ratio `>= 1.05`; at least 2/3 DRTP−UTR seed directions non-negative |
| constraints | pooled constraint violation exactly `0.0` |
| collision safety | pooled DRTP−UTR rate `<=0.05`; no seed-condition increase `>0.10` |
| timeout safety | pooled DRTP−UTR rate `<=0.05`; no seed-condition increase `>0.10` |
| exposure | all planned pairs retained and reported; no hidden exclusion |

Any failure of these hard rows is a held-out NO-GO.  It does not authorize
retries, altered seeds, new methods, or protocol changes.

## 5. Descriptive self-reference diagnostics

Report, for every seed and pooled estimate,

\[
R_{\mathrm{OOD,mean}}=J_{\mathrm{OOD,mean}}/J_{F0},\qquad
R_{\mathrm{OOD,worst}}=J_{\mathrm{OOD,worst}}/J_{F0}.
\]

Report their UTR/DRTP values and interpretation alongside the absolute
endpoints, including any denominator sensitivity.  They cannot independently
turn an absolute-performance/safety PASS into a NO-GO, and they cannot replace
the absolute endpoints or seed-level inference.

## 6. Completion boundary

This contract stops at formalization.  It authorizes neither held-out execution
nor any canonical/paper-scale experiment.  After a separately authorized
held-out run, report all hard gates, descriptive diagnostics, uncertainty at
the training-seed level, and one final GO/NO-GO decision; do not automatically
advance further.
