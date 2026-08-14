# DRTP-SG-MAPPO Method & Experiment Contract

## 0. Status and scope

**FROZEN METHOD CONTRACT / NO TRAINING AUTHORIZED.**

This is the sole Route-B follow-up to
`POST_MSR_OOD_GAP_SCAN_AND_FINAL_ALGORITHM_DECISION_REPORT.md`. It defines the
future **Distributionally Robust Topology-Perturbation Single-Graph MAPPO
(DRTP-SG-MAPPO)** direction and the mandatory capacity-matched comparator. It
does not implement DRTP, generate tapes, run tests, or start training.

The S2 scientific question and primary estimand remain unchanged:

\[
\Delta_J=J_{\mathrm{nominal}}-J_{\mathrm{failure}}.
\]

Strict recovery, Relay necessity, information-loss mediation, Full, RSG-TC,
CTP, ENMM, and new encoder directions remain closed.

## 1. Immutable components

| component | frozen value |
|---|---|
| graph encoder | existing matched Single-Graph only (`single`) |
| parameter count | **116,728** |
| role gate | `none` |
| PPO/optimizer | existing matched-SG settings unchanged: LR `3e-4`, gamma `0.99`, GAE `0.95`, clip `0.2`, entropy `0.01`, value coefficient `0.5`, max grad norm `0.5`, 4 PPO epochs |
| rollout/budget | 4 environments × 64 steps × 3,907 updates = **1,000,192 steps** per run |
| checkpoint rule | from scratch; fixed final update only; no resume, early stopping, best-checkpoint selection, or promotion |
| task contract | S2 environment, reward, topology/failure semantics, and actor information boundary unchanged |
| canonical seeds | `0–4` prohibited |

DRTP changes only the training episode-sampling distribution. It adds no neural
module, no new PPO/critic loss, no reward term, and no actor/critic feature.

## 2. Frozen topology training groups

| id | group | frozen scenario members `(onset,duration)` | within-group probability |
|---|---|---|---:|
| `N` | nominal anchor | no Relay failure | 1.0 |
| `F0` | seen canonical failure | `(44,80)` | 1.0 |
| `TE` | early timing | `(28,80)`, `(36,80)` | 0.5 / 0.5 |
| `TL` | late timing | `(52,80)`, `(60,80)` | 0.5 / 0.5 |
| `DS` | short duration | `(44,40)`, `(44,60)` | 0.5 / 0.5 |
| `DL` | long duration | `(44,100)`, `(44,120)` | 0.5 / 0.5 |
| `CP` | compound perturbation | `(28,120)`, `(60,120)` | 0.5 / 0.5 |

For every non-nominal member, `failed_blue_agent=1`; only onset and duration are
selected. The group/condition identifier is training-sampler metadata only and
never reaches policy execution.

## 3. Mandatory matched baseline: UTR-SG-MAPPO

The comparator is **Uniform Topology Randomization SG-MAPPO (UTR-SG-MAPPO)**.
It has identical SG architecture, parameter count, PPO, budget, task, reward,
actor inputs, groups, within-group members, logging, and final-checkpoint rule.
Only the group-weight controller differs.

Both methods have the same immutable nominal exposure anchor:

\[
p_N=0.50.
\]

For UTR, the other six groups are conditionally uniform:

\[
q_k^{\mathrm{UTR}}=\frac{1}{6},\qquad
p_k^{\mathrm{UTR}}=(1-p_N)q_k^{\mathrm{UTR}}=\frac{1}{12},
\quad k\in\mathcal F=\{F0,TE,TL,DS,DL,CP\}.
\]

UTR therefore sees exactly the same topology-training universe as DRTP.

## 4. DRTP robust objective and frozen update equation

The conceptual objective is

\[
\max_\theta\left[p_NJ_N(\theta)+(1-p_N)
\min_{q\in\mathcal Q}\sum_{k\in\mathcal F}q_kJ_k(\theta)\right],
\]

with bounded adversarial group distribution

\[
\mathcal Q=\left\{q\in\Delta^6:0.05\le q_k\le0.35\right\}.
\]

PPO remains unchanged. The inner robust distribution is approximated only by
episode-sampling weights. Let \(\widehat J_{k,u}\) be the mean undiscounted
completed-episode return for group \(k\) since the preceding adaptation boundary.
For an observed group:

\[
\bar J_{k,u}=(1-\kappa)\bar J_{k,u-1}+\kappa\widehat J_{k,u};
\]

for an unobserved group its EMA remains unchanged. The nominal EMA is updated
identically. Relative group difficulty is

\[
d_{k,u}=\operatorname{clip}\!\left(
\frac{\bar J_{N,u}-\bar J_{k,u}}
{\max(|\bar J_{N,u}|,\epsilon)},0,d_{\max}\right),
\quad
\tilde d_{k,u}=d_{k,u}-\frac{1}{6}\sum_{j\in\mathcal F}d_{j,u}.
\]

The exponentiated-gradient candidate and the bounded projected update are

\[
\tilde q_{k,u+1}=
\frac{q_{k,u}\exp(\eta\tilde d_{k,u})}
{\sum_{j\in\mathcal F}q_{j,u}\exp(\eta\tilde d_{j,u})},
\]

\[
q_{u+1}=\Pi_{\mathcal Q}\left((1-\beta)q_u+\beta\tilde q_{u+1}\right).
\]

| control | frozen value |
|---|---:|
| initialization | `q_k=1/6` |
| nominal mass | `p_N=0.50` |
| uniform warm-up | first 128 updates |
| adaptation interval | 32 updates after warm-up |
| EMA `kappa` | 0.20 |
| temperature `eta` | 1.00 |
| smoothing `beta` | 0.50 |
| `d_max` / `epsilon` | 2.00 / `1e-8` |
| `q_min` / `q_max` | 0.05 / 0.35 |

At reset, DRTP samples `N` with probability 0.50. Otherwise it samples group
`k` with `q_k` and then uniformly samples that group's listed scenario member.
The fixed nominal mass is the exposure anchor; \(\bar J_N\) is the competence
anchor. Neither is an auxiliary loss or policy input.

## 5. Information boundary

Only the training sampler/logger may access group labels, selected onset/duration,
group returns, EMA values, difficulty scores, or `q`. They are prohibited from
actor and critic observations, together with failure labels, global topology,
shortest paths, future links, ground-truth routes/targets, and hidden cache truth.

The actor retains only the legal S2 decentralized inputs: existing observations,
node/edge features, roles, adjacency, and relation adjacency. Receiver/sender
adjacency convention and edge-feature schema remain unchanged. The critic receives
no DRTP-specific field. The sampler is absent at evaluation time.

## 6. Frozen experiment resources

| stage | methods | seeds | budget | evaluation tape | authorization |
|---|---|---|---:|---|---|
| development | UTR-SG, DRTP-SG | `1901,1902` | 1,000,192/run | `420000–420099` | not authorized |
| held-out confirmation | UTR-SG, DRTP-SG | `2001,2002,2003` | 1,000,192/run | `430000–430099` | not authorized |
| canonical paper study | separately decided only | `0–4` | separately frozen | new canonical tapes | prohibited |

Each future tape contains 100 paired base IDs reused across nominal, F0, four
timing, four duration, and two compound conditions. Its manifest must bind the
condition table, failure semantics, `canonical=false`, prior forbidden namespaces,
and SHA256. These tapes are reserved by this document only; neither is generated
in this stage.

## 7. Frozen evaluation and retention gates

Only final checkpoints may be evaluated. All planned pairs, including episodes
terminating before the failure, remain in the primary return summaries. Exposure
is reported separately and cannot be used for post-hoc filtering.

For the ten OOD conditions:

\[
J_{\mathrm{OOD,mean}}=\frac{1}{10}\sum_{c\in\mathrm{OOD}}J_c,
\qquad
J_{\mathrm{OOD,worst}}=\min_{c\in\mathrm{OOD}}J_c.
\]

`R_OOD_mean` and `R_OOD_worst` are descriptive same-policy ratios to seen F0;
they do not replace the S2 primary \(\Delta_J\) endpoint.

### Development-to-held-out gate

DRTP may enter held-out confirmation only if every criterion holds on development
seeds `1901/1902` and tape `420000–420099`, relative to UTR:

| domain | frozen criterion |
|---|---|
| nominal retention | pooled `J_N(DRTP)/J_N(UTR) >= 0.95`; neither seed below `0.90` |
| F0 retention | pooled `J_F0(DRTP)/J_F0(UTR) >= 0.98`; neither seed below `0.90` |
| OOD mean | pooled `J_OOD_mean(DRTP)/J_OOD_mean(UTR) >= 1.05`; both seed directions non-negative |
| OOD worst | pooled `J_OOD_worst(DRTP)/J_OOD_worst(UTR) >= 1.05`; both seed directions non-negative |
| self-reference | pooled `R_OOD_mean` and `R_OOD_worst` not lower than UTR |
| exposure | all planned pairs retained and reported; no hidden seed/episode exclusion |
| constraints | pooled constraint violation exactly `0.0` |
| collision safety | DRTP−UTR pooled rate `<=0.05`; no seed-condition increase `>0.10` |
| timeout safety | DRTP−UTR pooled rate `<=0.05`; no seed-condition increase `>0.10` |

Any failed row is a DRTP development NO-GO. It does not authorize retries, a
second robust candidate, held-out runs, canonical runs, or protocol changes.

### Held-out confirmation gate

After separate authorization, apply the same pooled thresholds to seeds
`2001/2002/2003` on tape `430000–430099`. At least two of three seed directions
must be non-negative for both OOD mean and OOD worst. A held-out failure closes
DRTP; it cannot trigger a new candidate method.

## 8. Required provenance and fairness artifacts

Before future training, each run must record:

- immutable SG/PPO/environment snapshot and SHA256;
- sampler manifest with Section-2 groups, member scenarios, constants, seed, and
  sampler hash;
- parameter count (`116,728`) and architecture identity;
- no-resume/no-early-stop/final-checkpoint-only declarations;
- realized group/member episode counts;
- DRTP weight, difficulty, EMA, and update-boundary logs; UTR's equivalent fixed
  uniform-group log;
- final/milestone checkpoint hashes, where milestones are learning-curve-only;
- raw paired evaluation CSV, tape hash, per-seed/pooled returns, safety/exposure,
  and topology/path telemetry.

UTR and DRTP must differ only in fixed versus adaptive `q`. No result may change
groups, probabilities, sampler constants, seeds, tapes, checkpoints, environment,
reward, PPO settings, or aggregation rules.

## 9. Future code mapping — not implemented now

| responsibility | existing anchor | future mapping |
|---|---|---|
| SG/PPO construction | `algorithms/ri_gmappo/simple_ri_gmappo.py`; `scripts/run_phase_fl_single.py` | reuse unchanged |
| current static sampler | `algorithms/ri_gmappo/fixed_condition_mixture.py` | reference only; cannot express seven groups or adaptive weights |
| group sampler/projection | no existing code | future `algorithms/ri_gmappo/drtp_topology_sampler.py` implements Sections 2–4 exactly |
| reset-time application | `collect_rollout()` in `algorithms/ri_gmappo/simple_ri_gmappo.py` | future opt-in sampler hook; no policy tensor/reward-path change |
| frozen final-run provenance | `scripts/run_phase_msr_mixed50_single.py` | future `scripts/run_phase_drtp_sg.py` binds arm/config hashes and final-only policy |
| tape generation | `scripts/create_phase_msr_tape.py` | future generator creates only reserved 420k/430k manifests |
| evaluation/aggregation | current S3/MSR/OGS evaluator path | future scripts enforce Section-7 gates without filtering |
| tests | no DRTP tests exist | determinism, projection bounds, legality, parameter equality, logging invariance, and tape replay tests mandatory |

No DRTP module, sampler, launcher, tape, checkpoint, loss, or training code has
been created in this phase. The table is a frozen implementation map, not an
authorization to implement it.

## 10. Explicit prohibitions

Until a later separate authorization:

- no DRTP training, smoke, held-out run, canonical run, or OOD extension;
- no new encoder, recurrent memory, relation branch, gate, residual, or loss family;
- no reward, environment, failure-semantic, observation, critic-input, or PPO change;
- no canonical seeds `0–4`;
- no result-driven change to any sampler constant or retention threshold;
- no checkpoint promotion, seed exclusion, unfavorable-run retry, or alternate
  comparator.

## 11. Freeze decision

**DRTP-SG-MAPPO method and experiment contract: FROZEN.**

The only future path is separate authorization for implementation, source-level
tests, and a launch gate. This phase stops here; training remains unauthorized.
