# RACG-PPO C0.5 exact formula contract

## Status and boundary

This document freezes one RACG-PPO formula before any model implementation or same-rollout outcome is inspected. It authorizes no environment step, PPO update, evaluation, cloud execution or fresh-seed training.

## Cross-fitted reliability

For fixed group masses \(p_g\), two stream assignments fixed before rollout produce \(g_g^A\) and \(g_g^B\). Define

\[
a_g=\left[\frac{\langle g_g^A,g_g^B\rangle}{\|g_g^A\|\|g_g^B\|+\epsilon_g}\right]_+,
\quad
a_0=\left[\cos\!\left(\sum_g p_g g_g^A,\sum_g p_g g_g^B\right)\right]_+,
\]

and

\[
\rho=a_0\sum_g p_g a_g\in[0,1].
\]

There is no reliability threshold. Split disagreement continuously weakens the correction; \(\rho=0\) gives exact ordinary PPO.

## Reliability-shrunk group directions

Let

\[
\bar g_g=\tfrac12(g_g^A+g_g^B),\qquad
\bar g=\sum_g p_g\bar g_g,
\]

and shrink each unreliable group estimate toward the fixed-mass average:

\[
\widetilde g_g=a_g\bar g_g+(1-a_g)\bar g.
\]

This changes update construction, never the collection distribution.

## Seven-dimensional average-anchored proposal

Set \(c_t=0.5\rho\). With \(\widetilde G=[\widetilde g_1,\ldots,\widetilde g_7]\), solve exactly one frozen simplex problem:

\[
w^*=\arg\min_{w\in\Delta_7}
(\widetilde Gw)^\top\bar g
+c_t\|\bar g\|\sqrt{\|\widetilde Gw\|^2+\epsilon_g^2}.
\]

The implementation first divides every gradient in this homogeneous objective by one common local gradient scale. This leaves the minimizer unchanged and prevents solver termination from depending on raw gradient units. It then uses SLSQP, initialization \(w=p\), bounds \([0,1]\), equality \(\sum w_g=1\), `ftol=1e-12`, and at most 256 iterations. Solver failure or nonfinite output causes exact ordinary fallback, not a rejected update.

The surrogate correction is

\[
c=c_t\|\bar g\|\frac{\widetilde Gw^*}{\max(\|\widetilde Gw^*\|,\epsilon_g)}.
\]

## Complete ordinary anchor and liveness bound

Entropy is included once in the complete ordinary actor direction:

\[
g_0=\bar g+\beta_H\nabla\mathcal H.
\]

Clip the correction only by its norm:

\[
\bar c=c\min\left(1,\frac{0.5\|g_0\|}{\|c\|+\epsilon_g}\right),
\qquad d=g_0+\bar c.
\]

Thus \(\|d\|\ge0.5\|g_0\|\) before Adam. No hard per-group certificate and no zero-step rejection exists. Critic learning, GAE, PPO clipping, entropy coefficient, optimizer and gradient clipping remain matched to ordinary fixed-exposure PPO.

## Numerical and scientific limits

The relative epsilon is `1e-12` times the local gradient scale. The liveness bound is not a return guarantee. Cross-fit agreement is a training-only reliability proxy, not a classifier of good and bad seeds. C1 must falsify the mechanism on already-seen same-rollout states before any fresh-seed experiment can be considered.
