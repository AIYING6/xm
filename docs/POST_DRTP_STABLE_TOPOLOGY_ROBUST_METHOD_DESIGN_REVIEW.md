# Post-DRTP Stable Topology-Robust MARL Method Design Review

**Phase:** A — zero-training method design review
**Date:** 2026-08-17
**Decision:** **A — GO — one clearly justified method**
**Authorized by this document:** method specification only.
**Explicitly not authorized:** implementation, tape generation, training, new held-out runs, canonical seeds, or a change to any historical result.

## 1. Scope, immutable history, and terminology

### 1.1 One-sentence argument

For heterogeneous UAV coordination under a frozen Relay-node topology perturbation, we propose a fixed-exposure, nominal-anchored actor-gradient projection that removes only failure-training updates that oppose nominal task competence, while leaving topology-specific re-planning updates available; its cross-seed stability remains a prospective hypothesis to be tested before any performance claim.

### 1.2 Terminology ledger

| Canonical term | Definition in this review | Variants that must not be used interchangeably |
|---|---|---|
| SG-MAPPO | Existing parameter-matched Single-Graph MAPPO backbone with **116,728** parameters | Single Graph, matched SG |
| UTR-SG-MAPPO | Fixed, non-adaptive topology exposure: nominal mass 0.50 and conditional uniform mass over the six frozen failure groups | uniform curriculum, random curriculum |
| DRTP-SG-MAPPO | Historical adaptive return-weighted topology sampler; permanently closed as a paper-main candidate | robust SG, adaptive baseline |
| TCR-SG-MAPPO | **Topology-Conflict-Regularized SG-MAPPO**, the sole prospective candidate specified here | Topology-Consistent Robust SG-MAPPO (earlier working expansion) |
| nominal anchor | The immutable 0.50 nominal exposure and its actor PPO gradient in a TCR update | reward constraint, nominal reward shaping |
| failure gradient | Actor PPO gradient from the fixed-exposure, non-nominal half of a rollout batch | failure label input |
| topology group | One of `N`, `F0`, `TE`, `TL`, `DS`, `DL`, `CP`; it is training metadata, never an actor or critic feature | topology state, graph observation |
| F0 | Seen canonical Relay failure, onset 44 and duration 80 | primary endpoint |
| OOD worst | Minimum absolute return across the frozen OOD conditions | self-reference ratio |

### 1.3 Non-negotiable scientific boundary

The frozen problem remains:

\[
\text{Relay failure}
\rightarrow
\text{communication topology/path reconfiguration}
\rightarrow
\text{heterogeneous coordination degradation}
\rightarrow
\text{topology-robust MARL}.
\]

It does **not** reinstate a claim of unique Relay necessity, information-loss mediation, information restoration, or strict recovery.  The completed DRTP development and held-out histories remain immutable: the held-out result is `HELD_OUT_FAIL`, and the zero-training forensic classification is `C — no actionable cause / intrinsic seed sensitivity`.  In particular, this review does not treat a favourable pooled DRTP result as a substitute for the failed independent seed-level evidence.

## 2. Design input and why the old intuitive regularizer is rejected

The existing 3D actor has no usable intent supervision: `UAVIntercept3DEnv._get_graph_obs()` emits `has_intent_label=False`, and `effective_intent_coef()` therefore disables the old intent auxiliary loss for `3d_intercept`.  Calling the unused intent head a topology-invariant task-semantic target would be scientifically incorrect.

Likewise, a post-failure nominal/failure trajectory pair no longer occupies the same physical state after the intervention.  A direct latent loss of the form \(\lVert h^{N}_t-h^{F}_t\rVert^2\), an action KL, or an attention-equality loss would incorrectly penalize legitimate maneuver, path, and support-source changes.  These options are rejected rather than implemented.

The retained design target is therefore **policy-update compatibility**, not literal equality of a hidden representation or action.  This is measurable from the training objective without needing a privileged semantic label.

## 3. Sole candidate: TCR-SG-MAPPO

### 3.1 Method statement

**Topology-Conflict-Regularized SG-MAPPO (TCR-SG-MAPPO)** keeps the exact SG-MAPPO actor, critic, parameter count, PPO hyperparameters, S2 environment, reward, failure semantics, and legal actor inputs unchanged.  It also keeps the fixed UTR exposure distribution:

\[
p(N)=0.50,\qquad p(k)=\frac{1}{12},\quad
k\in\{F0,TE,TL,DS,DL,CP\}.
\]

Its sole change is an optimizer-side projection of the **actor** gradient from the failure half of a fixed-exposure rollout when, and only when, that gradient locally opposes the nominal-anchor actor gradient.  The critic, reward, graph encoder, action head, and evaluation policy are unchanged.

This is a topology-robust **policy regularization through the update rule**.  It is not a new encoder, an adaptive sampler, a new reward, a failure detector, or a privileged-information channel.

### 3.2 Objects that should remain stable (Q1)

No complete latent vector, attention map, action distribution, or physical trajectory is declared topology-invariant.  Such a declaration is not identifiable from the current legal 3D observations after trajectories diverge.

The sole stable object is the **local nominal-competence descent direction** in actor-parameter space.  On an update with matched fixed exposure, the nominal actor PPO gradient \(g_N\) represents the immediate update that improves the still-valid mission objective under the nominal condition.  TCR preserves this direction and prevents the simultaneous failure-training update from moving directly against it.

This is deliberately narrower than claiming that a hidden state is semantic.  It protects a measurable competence anchor, while PPO continues to learn task-relevant representations from reward.

### 3.3 Objects that must adapt (Q2)

The following are explicitly free to differ between nominal and failure trajectories:

- legal adjacency, edge features, relation masks, graph attention, and message-age use;
- communication-path and task-support source selection;
- local target cache use and confidence;
- maneuver, action distribution, flight path, control effort, and episode duration;
- all actor parameter components orthogonal to, or aligned with, the nominal gradient.

TCR neither compares action logits across conditions nor constrains the final policy to make the same action.  A Relay failure can therefore induce a different legal response, including a topology/path reconfiguration.

## 4. Legal paired-sample contract (Q3)

### 4.1 Pairing unit

A pair is an **episode descriptor**, not an assertion that post-failure states are equal.  For each descriptor \(d\), the training scheduler creates one nominal member and one member from a pre-frozen failure group.  They share the deterministic initial-state, target-realization, and exogenous-noise descriptor.  The intervention is only the pre-registered Relay failure condition.

After the intervention, policies may choose different actions and therefore reach different states.  TCR never aligns their states, observations, actions, attention, or latents at equal wall-clock time.  The pairing is used only to ensure balanced exposure and to form a nominal/failure actor-gradient comparison within an optimizer update.

### 4.2 Legal data flow

The actor still receives only the frozen S2 decentralized tensors:

\[
(o_i,\;\texttt{node\_feat},\;\texttt{edge\_feat},\;\texttt{role},\;\texttt{adj},\;\texttt{relation\_adj}).
\]

The condition-group field may route already-collected samples to either the nominal or failure loss **inside the training optimizer only**.  It is forbidden from actor and critic forward inputs, checkpoints intended for evaluation, recurrent/runtime observations, graph features, reward calculation, or deployment.  Episode identifiers and pair membership are likewise scheduler metadata, not policy inputs.

Prohibited information remains prohibited: actual failure labels at execution time, global connectivity, shortest paths, ground-truth routes/targets, hidden cache truth, future links, and centralized-only critic data.  The critic receives no TCR-specific feature.

### 4.3 Fixed paired exposure implementation requirement

The future Phase-B sampler must make each four-environment rollout contain two nominal and two non-nominal environment streams.  Failure-group/member descriptors are assigned by a pre-generated, balanced schedule so that the full run has exactly the frozen nominal mass and equal failure-group mass up to the unavoidable terminal partial block.  The UTR control receives the identical descriptor schedule.

This is stratified implementation of the same fixed UTR distribution, not an adaptive curriculum.  It ensures both gradient subsets are present at every projected actor update without sampling a group according to return, EMA, difficulty, or policy performance.

## 5. Mathematical objective and update operator (Q4)

Let \(\theta_A\) denote all existing actor parameters.  On one PPO minibatch, let \(\mathcal B_N\) and \(\mathcal B_F\) be the nominal and pooled non-nominal samples, respectively.  Each uses the ordinary clipped PPO actor objective, including the existing entropy term but excluding the value loss:

\[
\mathcal L_A^c(\theta_A)=
\mathbb E_{x\in\mathcal B_c}
\left[
\max\left(-r_\theta(x)\hat A(x),
-\operatorname{clip}(r_\theta(x),1-\epsilon,1+\epsilon)\hat A(x)\right)
-\beta\,\mathcal H(\pi_\theta(\cdot\mid x))
\right],\quad c\in\{N,F\}.
\]

Define

\[
g_N=\nabla_{\theta_A}\mathcal L_A^N,
\qquad
g_F=\nabla_{\theta_A}\mathcal L_A^F.
\]

TCR leaves a non-conflicting failure gradient unchanged and projects only its component that opposes the nominal anchor:

\[
\widetilde g_F=
g_F-
\min\!\left(0,
\frac{\langle g_F,g_N\rangle}
{\lVert g_N\rVert_2^2+\delta}
\right)g_N,
\qquad \delta=10^{-12}.
\]

The actor update direction is then

\[
g_{\mathrm{TCR}}=0.5\,g_N+0.5\,\widetilde g_F.
\]

Thus, when \(\langle g_F,g_N\rangle\ge0\), TCR is exactly the same actor-gradient combination as fixed-exposure UTR.  When the inner product is negative,

\[
\langle \widetilde g_F,g_N\rangle=0,
\]

up to numerical tolerance.  The ordinary UTR actor direction is \(0.5g_N+0.5g_F\).

The critic uses the ordinary fixed-exposure PPO value objective and optimizer step; it receives neither a projected gradient nor a group feature.  This isolates the intervention to nominal–failure actor-gradient conflict.

### 5.1 What this objective does not do

- It does not optimize a worst-group distribution.
- It does not use a DRTP \(q\), EMA, difficulty, completed return, or group-return window.
- It does not introduce an auxiliary reward, contrastive loss, latent target, action-consistency loss, or topology label as a policy input.
- It does not reweight `F0` versus `TE/TL/DS/DL/CP`; their exposure remains uniform conditional on failure.

## 6. Why topology reconfiguration is not suppressed (Q5)

The failure gradient is discarded **only in its locally nominal-opposing component**.  Its aligned component and every orthogonal component remain.  In particular, an update that improves failure behavior by changing communication use, route choice, maneuver, or task-support use without directly decreasing the nominal actor objective is retained in full.

No loss asks for \(\pi_N=\pi_F\), \(h_N=h_F\), equal attention, equal message use, equal paths, or equal actions.  The method therefore has a clear falsifiable boundary: if the correct robust behavior intrinsically requires an update that is directly anti-nominal at the same parameters, TCR may be too conservative and will fail the future multi-seed screen.  This trade-off is an intended testable limitation, not a hidden claim of universal robustness.

## 7. Expected stability mechanism and distinction from DRTP (Q6)

DRTP changed the next training distribution through a feedback loop:

\[
\text{completed return}\rightarrow\text{EMA/difficulty}\rightarrow q
\rightarrow\text{future exposure}\rightarrow\text{completed return}.
\]

The held-out forensic review showed that this route had an early seed2002 deficit and return-dependent F0 under-exposure, but no unique, actionable mechanism explaining why that seed failed while other seeds with similar allocations succeeded.  It is therefore closed, not repaired here.

TCR removes that feedback loop.  Its condition schedule is pre-generated and fixed, and its only adaptive quantity is the current minibatch's deterministic first-order actor-gradient geometry.  Given identical state, action, optimizer, and sampler runtime states, the projection is deterministic and bounded: it cannot concentrate exposure on a group, alter the reward, or make future group frequencies depend on historical return.

This does **not** prove cross-seed stability.  The prospective claim is narrower: fixed exposure plus a local conflict rule removes one plausible source of condition-interference amplification without creating another return-driven sampling trajectory.  The planned five-seed screen must test whether catastrophic seeds nevertheless remain.

## 8. Difference from UTR-SG-MAPPO (Q7)

| Aspect | UTR-SG-MAPPO control | TCR-SG-MAPPO candidate |
|---|---|---|
| SG actor/critic, parameters, PPO, environment, reward | identical | identical |
| Nominal anchor | fixed 0.50 exposure | fixed 0.50 exposure |
| Six failure groups | fixed conditional uniform exposure | fixed conditional uniform exposure |
| Scheduler | pre-generated balanced descriptor schedule | same schedule |
| Actor input / critic input | legal S2 tensors only | exactly the same legal tensors |
| Actor update | ordinary fixed-exposure PPO gradient | nominal-anchored projection of a conflicting pooled failure gradient |
| Adaptive return-weighting | absent | absent |

The algorithmic contribution is consequently narrow and isolatable: **under identical fixed topology exposure, TCR modifies only the interaction of nominal and failure actor gradients.**  A result can be attributed neither to extra model capacity nor to seeing more of any topology group.

## 9. Legality, CTDE, capacity, and fairness audit (Q8)

| Audit item | Design conclusion | Evidence / future verification |
|---|---|---|
| Actor information legality | PASS by construction | `RIActor.forward()` receives the same S2 tensors; condition metadata never enters it. |
| CTDE boundary | PASS by construction | The centralized critic remains unchanged and receives no condition or projection field. |
| Graph legality | PASS by construction | `adj`, `edge_feat`, and `relation_adj` retain the frozen receiver/sender convention and schema. |
| Simulator privilege | PASS by construction | Pair/group identifier is optimizer-only training metadata; no global topology, path, ground truth, cache truth, or future link is exposed. |
| Parameter fairness | PASS in design | No neural module is added or removed; TCR and UTR both remain **116,728** parameters. A Phase-B parameter audit must assert equality. |
| Computational fairness | CONDITIONAL PASS | TCR needs two actor gradient evaluations from the same minibatch; UTR must receive an equally instrumented split/minibatch path, with projection disabled, and wall-clock/memory overhead reported. |
| Evaluation fairness | PASS in design | Same final-checkpoint-only rule, seed, budget, environment, and frozen paired tape per arm; group identifiers are absent at evaluation. |

The relevant existing implementation anchors are `RIActor.forward()` and `update_policy()` in `algorithms/ri_gmappo/simple_ri_gmappo.py`, the frozen graph construction in `envs/uav_intercept_3d_env.py`, and the seven-group table in `algorithms/ri_gmappo/drtp_topology_sampler.py`.  Phase B may add optimizer-side code only; it must not change these actor-visible environment contracts.

## 10. Minimal implementation specification for a future Phase B

This section is a design mapping, **not implementation authorization**.

1. Add an opt-in `tcr` optimizer mode beside existing fixed-exposure UTR; do not reuse `drtp` adaptive fields or code paths.
2. Add a pre-generated paired descriptor scheduler with exactly 0.50 nominal and 1/12 mass per failure group.  Its state must be included in existing runtime persistence.
3. In `update_policy()`, separate existing actor-loss samples by the optimizer-only binary condition class `N` versus `F`; compute the two actor gradients; apply the stated projection only to actor parameters; update the unchanged critic normally.
4. Use a parameter-identical UTR control with the same descriptor schedule, condition-split bookkeeping, optimizer state persistence, and logging; set projection off.
5. Record, without changing the optimization objective: conflict rate, pre-projection cosine, post-projection cosine, \(\lVert g_N\rVert\), \(\lVert g_F\rVert\), \(\lVert\widetilde g_F\rVert\), and projection magnitude.  These are diagnostics, not actor features or selection criteria.

Mandatory Phase-B tests before any long run:

- exact `116,728` parameter equality for UTR and TCR;
- fixed-group count and member-frequency test;
- projection algebra test: identity for non-negative inner product and non-negative post-projection dot product within tolerance for negative inner product;
- actor/critic information-boundary and graph-legality regression;
- deterministic replay and save–reload–next-update continuation with the descriptor-scheduler runtime state;
- logging-on/off invariance;
- 1-update smoke with finite PPO, gradient, and projection diagnostics.

Failure of any item returns the route to `REVISE`; it does not authorize a workaround training run.

## 11. Prospective Phase-C 1M multi-seed stability-screen protocol

This section defines a future rejection screen only.  It does **not** authorize it now.

### 11.1 Pre-registration required before launch

Before any Phase-C execution, freeze in one separate contract:

- five development seeds: `2002` as the declared stress-development seed and four currently unused non-canonical seeds `2101, 2102, 2103, 2104` (their unused status must be re-audited immediately before launch);
- both arms: UTR-SG-MAPPO and TCR-SG-MAPPO;
- identical from-scratch, strict-continuous 1,000,192-step budgets, runtime persistence, and final-checkpoint-only rule;
- one new, unused paired development tape and its complete condition manifest;
- fixed 50% nominal anchor, uniform six-group exposure, pair schedule, PPO, environment, reward, failure semantics, actor boundary, and all safety/exposure definitions;
- the exact numerical definition of a severe/catastrophic seed before any result is visible.  It must be set independently of the historical seed2002 outcome and cannot be altered after launch.

`2001–2003` are permanently development-only because they have already been viewed.  They cannot be renamed held-out.  Canonical seeds `0–4` remain prohibited.

### 11.2 Required outcomes

Report every training seed, without exclusion, on all planned paired episodes:

\[
J_{\mathrm{nominal}},\quad J_{F0},\quad J_{\mathrm{OOD,mean}},\quad
J_{\mathrm{OOD,worst}},
\]

plus collision, timeout, constraint violation, exposure, per-seed direction versus UTR, seed dispersion, topology/path telemetry, and the TCR conflict/projection diagnostics.  Repeated tape episodes are measurements within a training seed; the training seed remains the unit for cross-seed stability decisions.

### 11.3 Rejection logic

The 1M screen is an instability filter, not a superiority claim.  It must stop with `EARLY NO-GO` if the pre-registered rule finds two or more severe/catastrophic TCR seeds, a systematic safety deterioration, or an unmistakable seed bifurcation that is worse than UTR.  A favourable pooled mean cannot override any such outcome.

Only if all five TCR trajectories meet the frozen safety/exposure requirements and no catastrophic seed occurs may a separately authorized continuous 1M→3M stage be considered.  A non-catastrophic but weak pooled effect is `NO-GO` for a final-method route, not grounds for adding another network, another loss, adaptive sampling, or a seed search.

## 12. Claim–evidence map and decision boundary

| Proposed statement | Evidence now | Status |
|---|---|---|
| DRTP must remain closed as a main candidate | immutable held-out `FAIL` and forensic classification C | supported |
| The 3D actor lacks valid intent supervision | `has_intent_label=False`; 3D intent coefficient is zero | supported |
| Direct nominal/failure latent or action equality would be semantically unsafe | paired trajectories legitimately diverge after failure; frozen problem requires reconfiguration | supported design inference |
| TCR preserves every non-conflicting and orthogonal failure actor-gradient component | projection equation | mathematically supported |
| TCR will reduce seed variance or improve robustness | no TCR data exists | **needs prospective multi-seed evidence** |
| TCR is better than UTR | no TCR data exists | **not claimed** |

### Final Phase-A decision

**A — GO — one clearly justified method: TCR-SG-MAPPO.**

The candidate is accepted for a future minimal implementation audit because it has one operational objective, preserves the exact SG capacity and legal actor boundary, does not require unavailable 3D semantic supervision, and has a clear counterfactual limitation.  This is a design `GO`, not a performance `GO`.  Phase A ends here: no code, tape, checkpoint, training, held-out, canonical, OOD, or ablation action is authorized by this document.
