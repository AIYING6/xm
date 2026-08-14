# DRTP-SG-MAPPO Implementation & Technical Smoke Report

## Scope and stop status

This report completes the implementation-only authorization following
`DRTP_SG_MAPPO_METHOD_CONTRACT.md`.

- Contract implementation commit: recorded together with this report
- Protocol: `DRTP-SG-MAPPO-TECHNICAL-VERIFICATION-V1`
- Final technical artifact: `results/development/drtp_sg_technical_verification_v2/DRTP_TECHNICAL_VERIFICATION.json`
- Final technical status: **PASS**
- Long training: **not started**
- Development seeds `1901/1902`: **not used**
- Held-out seeds `2001/2002/2003`: **not used**
- Canonical seeds `0–4`: **not used**
- Reserved tapes `420000–420099` and `430000–430099`: **not generated**

The one-update technical smoke used only non-protocol technical seeds `9101`
(UTR) and `9102` (DRTP), on CPU. It is not a development result, a model
selection result, or a paper result.

## Implemented source mapping

| contract component | implementation | status |
|---|---|---|
| seven frozen groups and members | `algorithms/ri_gmappo/drtp_topology_sampler.py` | PASS |
| UTR fixed conditional uniform weights | `DRTPTopologySampler(mode="utr")` | PASS |
| DRTP bounded exponential weighting | `DRTPTopologySampler(mode="drtp")` | PASS |
| reset-time environment application | opt-in hook in `collect_rollout()` | PASS |
| training-only manifests/logs | `drtp_topology_sampler_manifest.json`, `drtp_topology_sampler_log.csv` | PASS |
| unchanged SG/PPO path | opt-in fields in `RIGMAPPOConfig`; no agent/optimizer/loss edits | PASS |
| technical verifier | `scripts/run_drtp_sg_technical_verification.py` | PASS |

No encoder, relation branch, gate, residual, actor feature, critic feature,
reward term, PPO coefficient, environment rule, or new loss family was added.

## Contract-formula verification

The implementation freezes the contract values:

| item | verified value |
|---|---:|
| nominal anchor | `p_N=0.50` |
| UTR conditional failure weight | `q_k=1/6` |
| DRTP warm-up | 128 updates |
| adaptive boundary | every 32 updates after warm-up |
| EMA `kappa` | 0.20 |
| exponential temperature `eta` | 1.00 |
| smoothing `beta` | 0.50 |
| difficulty clip | 2.00 |
| simplex bounds | `[0.05, 0.35]` |
| numerical epsilon | `1e-8` |

The unit test supplied deterministic synthetic completed-episode returns
`J_N=100`, `J_F0=-200`, `J_TE=90`, `J_TL=80`, `J_DS=70`, `J_DL=60`, and
`J_CP=50`. It verified four uniform warm-up boundaries (32/64/96/128), then a
bounded exponentiated-gradient update at 160. The resulting difficulty and
weights exactly matched an independently computed reference projection:

| group | difficulty | updated q |
|---|---:|---:|
| F0 | 2.000000 | 0.343401 |
| TE | 0.100000 | 0.122231 |
| TL | 0.200000 | 0.126322 |
| DS | 0.300000 | 0.130843 |
| DL | 0.400000 | 0.135840 |
| CP | 0.500000 | 0.141362 |

The weights sum to one, all remain inside the frozen bounds, and the hardest
synthetic group receives the highest weight. This validates the contract update
equations; it does not claim that F0 will be hardest in a real future run.

## Group sampling and deterministic replay

UTR sampled 60,000 deterministic reset selections. Observed frequencies were:

| group | observed | contract target |
|---|---:|---:|
| N | 0.498117 | 0.500000 |
| F0 | 0.081917 | 0.083333 |
| TE | 0.084567 | 0.083333 |
| TL | 0.083083 | 0.083333 |
| DS | 0.085633 | 0.083333 |
| DL | 0.084900 | 0.083333 |
| CP | 0.081783 | 0.083333 |

All values meet the predeclared technical tolerance. Replaying the same seed,
update, environment index, and episode index produces identical selections.
Calling logging-row constructors does not alter the selection sequence, EMA
state, difficulty state, or adaptive weights.

## Architecture, information boundary, and legality

| check | result |
|---|---|
| UTR trainable parameters | 116,728 |
| DRTP trainable parameters | 116,728 |
| state-dict keys/initial values | identical |
| graph encoder | Single-Graph for both arms |
| sampler parameters in policy | none |
| sampler declares actor/critic condition input | false |
| existing information-boundary regression | PASS |
| existing S2 graph-legality regression | PASS |
| existing S2 telemetry logging-invariance regression | PASS |
| failure reset mutation | only `failed_blue_agent`, onset, duration |
| canonical F0 timing | active at steps 44–123, inactive at 43 and 124 |

Group labels, sampler weights, EMAs, difficulties, selected conditions, and
completed returns exist only in reset-time training bookkeeping and logs. They
are not inserted into observations, graph features, actor inputs, critic inputs,
or reward computation.

## Checkpoint and 1-update smoke

| arm | technical seed | updates | sampler log | final checkpoint | reload |
|---|---:|---:|---|---|---|
| UTR-SG | 9101 | 1 | present | PASS | PASS |
| DRTP-SG, logging on | 9102 | 1 | present | PASS | PASS |
| DRTP-SG, logging off | 9102 | 1 | intentionally absent | PASS | PASS |

The DRTP logging-on and logging-off checkpoints are bitwise identical after the
same one-update run. This closes the DRTP-specific logging-invariance check.
No checkpoint was selected for quality; every smoke uses its sole final update.

An initial verification output under `drtp_sg_technical_verification_v1` stopped
because a test incorrectly required both onset and duration to change when moving
between failure-group members. Some valid members share onset 44 and differ only
in duration. The test was corrected to require that only the frozen failure fields
may change; the sampler equations, conditions, and implementation were unchanged.
The clean v2 technical artifact above is the authoritative result.

## Final decision

**DRTP-SG-MAPPO and UTR-SG-MAPPO implementation: TECHNICAL PASS.**

This is an engineering gate only. It authorizes neither 1M development training
nor tape generation. The project remains stopped pending separate authorization
for the frozen development protocol.
