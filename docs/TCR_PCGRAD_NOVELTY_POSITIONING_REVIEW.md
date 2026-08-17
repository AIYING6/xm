# TCR–PCGrad Novelty Positioning and Projection-Minibatch Review

## Status and scope

**Status: POSITIONING PASS WITH MANDATORY SYMMETRIC CONTROL.** This is a zero-training review. It preserves all historical conclusions, including the DRTP held-out `FAIL`, and does not authorize TCR code, tapes, development runs, held-out runs, canonical seeds, or a paper claim.

The only candidate covered here is **TCR-SG-MAPPO** (Topology-Conflict-Regularized SG-MAPPO). Its proposed scope remains deliberately narrow: it changes only the actor-gradient combination rule of the frozen 116,728-parameter matched Single-Graph MAPPO. The SG encoder, critic, PPO losses and hyperparameters, S2 environment, reward, topology groups, fixed exposure schedule, failure semantics, and actor information boundary remain unchanged.

## Prior-method relationship

PCGrad projects a task gradient to remove its component conflicting with another task gradient. The negative-inner-product trigger and orthogonal projection used by TCR are therefore inherited from the published gradient-surgery principle; they are not a new generic optimization operation. PCGrad is model-agnostic and its source explicitly discusses actor-critic reinforcement-learning use. CAGrad is a further relevant multi-objective gradient method that seeks conflict-averse updates for the average objective.

Sources: Yu et al., *Gradient Surgery for Multi-Task Learning*, NeurIPS 2020; Liu et al., *Conflict-Averse Gradient Descent for Multi-task Learning*, NeurIPS 2021.

**Claim boundary.** The project must never claim that it first introduces projection of conflicting gradients, gradient surgery, or PCGrad-style optimization in MARL. If later evidence supports it, the contribution may only be framed as a task-specific formulation and evaluation of a nominal-anchored, one-sided conflict regularizer under frozen topology-perturbation exposure.

## Exact relationship to PCGrad

For one actor update, let the PPO actor gradients of the nominal and pooled failure subsets be:

\[
g_N = \nabla_\theta L_N, \qquad g_F = \nabla_\theta L_F.
\]

TCR proposes:

\[
\tilde g_F =
g_F-
\mathbf{1}\{\langle g_F,g_N\rangle<0\}
\frac{\langle g_F,g_N\rangle}{\lVert g_N\rVert_2^2+\delta}g_N,
\qquad
g_{\mathrm{TCR}}=0.5g_N+0.5\tilde g_F.
\]

Thus TCR is a **one-sided, two-class PCGrad-style projection**: it protects the nominal gradient and removes only the antagonistic component of the pooled failure gradient. It is not symmetric PCGrad, and it is not a new projection family.

## Task-specific formulation to be tested, not assumed

The proposed scientific hypothesis is narrower than generic multi-task learning:

1. Nominal operation is the mission-competence anchor; it is not an arbitrary peer task.
2. The six topology-perturbation groups are different realizations of one deployment concern: robustness to legal topology disruption.
3. UTR and TCR have the same fixed training exposure: 50% nominal and equal mass over the six non-nominal groups. Any advantage cannot be attributed to more failure exposure.
4. Condition labels are training-only sampler metadata. They must never enter the actor, critic, graph features, or decentralized execution inputs.
5. Failure policies may legitimately replan. TCR does not constrain hidden states, actions, attention, paths, or maneuvers to match nominal trajectories.

The asymmetry is therefore a falsifiable **nominal-competence anchor hypothesis**, not a claim that failure gradients are intrinsically less important. If its future evidence is absent, the asymmetric formulation must be rejected.

## Why the six failure groups are pooled into \(g_F\)

Pooling encodes one nominal-versus-perturbation interference hypothesis while avoiding a second adaptive weighting mechanism. It also keeps the comparison aligned with UTR: the group sampler is fixed and uniform conditional on a failure stream.

Pairwise projection among all six failure groups is not authorized. With the frozen four-environment rollout, a six-way split would create sparse, unstable per-group gradients and would introduce a materially different multi-objective method. Group-specific return, exposure, safety, and evaluation results must nevertheless remain separately logged and reported. Pooling is an experimental simplification, not a statement that all failure groups are identical.

## Mandatory symmetric gradient-surgery control

Future performance work must include a parameter-identical control named **SPC-SG-MAPPO** (symmetric PCGrad-style SG-MAPPO). It is a control, not an additional claimed method. It uses the same SG backbone, PPO, fixed sampler, 50% nominal anchor, rollout contract, inputs, seeds, budget, and final-checkpoint rule as UTR and TCR.

For a negative inner product, SPC applies the mutually symmetric two-class projection:

\[
\tilde g_N = g_N-
\frac{\langle g_N,g_F\rangle}{\lVert g_F\rVert_2^2+\delta}g_F,
\qquad
\tilde g_F = g_F-
\frac{\langle g_F,g_N\rangle}{\lVert g_N\rVert_2^2+\delta}g_N,
\]

and otherwise retains both gradients, with:

\[
g_{\mathrm{SPC}}=0.5\tilde g_N+0.5\tilde g_F.
\]

This is a specified symmetric-PCGrad-style control for the frozen two-class pooled setting; it must not be represented as an exact reproduction of every implementation detail of published PCGrad.

Interpretation is pre-committed:

- TCR better than UTR but comparable to SPC: no asymmetric-anchor claim.
- SPC better than UTR while TCR is worse: the nominal-anchor hypothesis fails.
- TCR stably better than both under the same exposure, safety, and seed-consistency criteria: supports the task-specific asymmetric-anchor hypothesis, but still not novelty of generic gradient surgery.

## Mandatory projection-minibatch contract

The current PPO implementation randomly shuffles rollout indices before forming minibatches. A 50/50 rollout alone does **not** guarantee that a projected actor update contains both conditions. Therefore, Phase B must add a training-only stratified actor-minibatch builder or deterministic nominal/failure pairing.

For **every** actor update that applies a TCR or SPC projection, the implementation must assert:

\[
|\mathcal B_N|>0, \qquad |\mathcal B_F|>0.
\]

The frozen rollout contract is two nominal and two failure environment streams, with four environments and 64 steps. A complete 256-sample rollout is therefore expected to contain 128 nominal and 128 failure samples. The implementation must construct projection units from the condition-class masks, rather than relying on shuffled minibatch composition.

The following are prohibited: silently skipping a projection update, using a stale gradient, resampling until a desired result appears, or falling back to an unpaired update. A missing class is a contract error that aborts the run. Advantages must be normalized once over the same full rollout used by UTR; only actor-loss gradient accumulation is partitioned. Critic updates remain ordinary frozen PPO updates.

Each projected actor update must log at least: nominal count, failure count, dot product, cosine similarity, projection-applied flag, \(\lVert g_N\rVert\), \(\lVert g_F\rVert\), projected-gradient norm, and final actor-gradient norm.

## Required Phase B tests before any long run

1. Parameter audit: UTR, SPC, and TCR each remain exactly 116,728 parameters.
2. Actor-boundary test: sampler labels and masks cannot reach actor, critic, graph features, saved observations, or evaluation inputs.
3. Fixed seven-group sampling test: 50% nominal and uniform conditional failure exposure agree with the frozen contract.
4. Stratified minibatch test: every projected update has non-empty \(\mathcal B_N\) and \(\mathcal B_F\), including deterministic replay.
5. Algebra test: non-conflicting gradients yield the UTR average; conflicting gradients satisfy the specified one-sided or symmetric equations.
6. Isolation test: no DRTP `q`, EMA, difficulty, completed-return feedback, or adaptive sampler state is instantiated.
7. Graph-legality, logging-invariance, checkpoint save/reload, deterministic replay, and one-update smoke tests.

## Future paper wording

Permitted wording after evidence exists: “We formulate fixed-exposure nominal and topology-perturbation updates as an asymmetric conflict-management problem, and evaluate a nominal-anchored projection against matched uniform and symmetric gradient-surgery controls.”

Forbidden wording: “We propose the first gradient projection method,” “we invent gradient surgery for MARL,” or any implication that TCR's projection algebra is original.

## Decision

**Positioning decision: PASS for a minimal Phase B implementation audit only, with SPC and the projection-minibatch contract mandatory.** No training, tape creation, held-out use, canonical use, or method-performance decision is authorized by this review.
