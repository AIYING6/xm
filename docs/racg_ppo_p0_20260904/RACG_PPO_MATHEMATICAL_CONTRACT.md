# RACG-PPO mathematical contract

## 1. Fixed group objective

For topology groups \(\mathcal G=\{N,F0,TE,TL,DS,DL,CP\}\), collection mass is fixed at

\[
p_N=\tfrac12,\qquad p_g=\tfrac1{12}\quad(g\ne N).
\]

No return, difficulty, confidence score or evaluation result changes these probabilities. Let \(S_g(\theta)\) denote the on-policy clipped actor surrogate for group \(g\). The complete ordinary actor ascent direction is

\[
g_0=\sum_g p_g\nabla S_g+\beta_H\nabla\mathcal H
\]

where \(\mathcal H\) is the matched PPO entropy objective. Group conflict statistics use only the group-specific surrogate terms, but the ordinary anchor and its norm include the shared entropy term. This distinction is required for the non-freezing bound to apply to the complete actor direction actually passed to the optimizer.

## 2. Cross-fitted group-gradient information

Each group has two stream sets fixed before rollout, giving gradient matrices

\[
G^A=[g_N^A,\ldots,g_{CP}^A],\qquad
G^B=[g_N^B,\ldots,g_{CP}^B].
\]

For independent zero-mean gradient noise, the same-sample Gram matrix has the positive noise term

\[
\mathbb E[(G+E)^\top(G+E)]=G^\top G+\mathbb E[E^\top E],
\]

whereas the symmetrized cross-fitted estimator

\[
\widehat H=\tfrac12\left[(G^A)^\top G^B+(G^B)^\top G^A\right]
\]

has expectation \(G^\top G\) when split noises are independent. This does not make one estimate exact; it removes the leading same-sample noise-product bias under the stated assumption.

Groupwise split agreement is

\[
a_g=\max\!\left(0,\frac{\langle g_g^A,g_g^B\rangle}
{\|g_g^A\|\,\|g_g^B\|+\varepsilon}\right).
\]

A future C1 implementation may combine these values with a scale-free regularity measure of \(\widehat H\) to produce \(\rho\in[0,1]\). P0 deliberately does not freeze the exact estimator until its identifiability and cost are measured on the five seen source states.

## 3. Average-oriented robust proposal

Let \(u\) be a low-dimensional conflict-regularized proposal computed from the seven group gradients, with the average objective as its anchor. The permitted family includes a CAGrad- or direction-oriented subproblem in seven coefficient dimensions. It excludes:

- a hard constraint \(g_g^\top d\ge0\) for every noisy group estimate;
- empirical worst-group-only optimization;
- evaluation-conditioned group weights;
- any adaptive collection distribution.

## 4. Non-freezing anchored blend

Define correction \(c=u-g_0\) and clip it to

\[
\bar c=c\min\!\left(1,\frac{\eta\|g_0\|}{\|c\|+\varepsilon}\right),
\qquad \eta=0.5.
\]

The actor direction is

\[
d=g_0+\rho\bar c,\qquad 0\le\rho\le1.
\]

Therefore

\[
\|d\|\ge \|g_0\|-\rho\|\bar c\|
\ge(1-\eta)\|g_0\|=0.5\|g_0\|.
\]

When \(\rho=0\), \(d=g_0\) exactly. Unlike TGTR, uncertainty cannot produce a rejected or zero actor step unless the ordinary PPO actor direction itself is zero.

The entropy term is already part of \(g_0\) and must not be added a second time after blending. Gradient clipping, Adam, critic learning, GAE and PPO epochs stay matched to fixed-UTR PPO. The stated lower bound is on the pre-Adam actor direction; C1 must separately verify the realized parameter displacement because Adam preconditioning changes parameter-space geometry.

## 5. Claim boundary

The norm lower bound is an optimization-liveness property, not a return guarantee. Cross-fitting reduces a specific gradient-product bias under independence; it does not establish cross-seed reliability. Only future fresh, independently replicated training can support performance or reliability claims.
