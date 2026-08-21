# T7 — Calibrated Support Sensitivity Formalization

## Scope and outcome

T7 is a zero-training design review. The only frozen T6 target was
**calibrated actor-legal support sensitivity**. This document formalizes the
minimal object that such a method would need, then records why no executable
calibration objective can be justified from the frozen evidence.

## Candidate mathematical object

Let `x_i=(u_i,s_i)` be agent `i`'s legal observation, where `s_i` is the
already legal support-relevant component; `M_s(x_i)=(u_i,0_s)` is its fixed
local-missing counterfactual. For a shared SG actor,

\[
z_i=f_{SG}(x_i), \qquad \pi_\theta(a_i\mid x_i),
\]

the only direct behavioral sensitivity object supported by T4/T6 is

\[
S_i(x_i)=D_{TV}\!\left(\pi_\theta(\cdot\mid x_i),
\pi_\theta(\cdot\mid M_s(x_i))\right).
\]

This is neither a Jacobian norm nor a statement that large `S_i` is desirable.
It is a finite, action-distribution effect of removing a named legal support
tuple.

## What calibration would require

A legitimate calibrated objective would require a state-conditional target
`\tau_i(x_i)` such that the training-only form

\[
\mathcal{L}_{cal}=\mathbb{E}\left[(S_i(x_i)-\tau_i(x_i))^2\right]
\]

has an independently justified direction and scale. The only available
actor-legal candidate reference is a local support-quality summary

\[
q_i=\frac{1}{5}(d_i+c_i+1-a_i+1-\bar a_i+\mathrm{conf}_i),
\]

formed from direct detection, inbound connectivity, inbound-message age,
cache age, and cache confidence. This would be a valid execution-time input;
GOOD/WEAK labels, T2 returns, future continuity, global paths, and failure truth
would not be.

## Formalization result

The T7 premise audit rejects `q_i` as a calibration reference. The matched
quality-conditioned sensitivity gap is negative for seed 2201, positive for
both weak seeds, and lacks a common GOOD-over-WEAK direction for timing OOD.
There is also no matched pre/early transition evidence. Therefore neither an
absolute `\tau(q)` nor an ordered range derived from `q` is identified.

Using `\mathcal{L}_{cal}` despite this result would reduce to one of the
prohibited forms: a generic finite-difference sensitivity penalty, an
input-gradient surrogate, or ordinary support conditioning with an arbitrary
target. It would not be a calibrated-support method. No final loss, decision
operator, inference rule, or method name is consequently defined.
