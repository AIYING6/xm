# Stable-v2 D4 frozen design: DRTP-KLB

## Decision boundary

This stage is a zero-training design and implementation audit. It does not authorize training, checkpoint evaluation, seed selection, threshold tuning, or any change to mainline A.

The sole D4 candidate is **DRTP-KLB (DRTP with a KL-boundary backtracking projection)**. No parallel Stable-v2 candidate is defined.

## Evidence basis and claim boundary

The D2 pilot showed that full actor rollback converted one catastrophic Original-DRTP seed into three positive DRTP-KLR seeds and sharply reduced dispersion, but it failed the frozen upper-tail-retention criterion. The D3 forensic audit found that only 36 of 23,426 attempted actor epochs triggered rollback, yet those rare interventions preceded persistent policy divergence. Trigger count, trigger timing, maximum attempted KL, sampler weights, and late training return did not provide a stable outcome discriminator.

These observations do **not** prove that DRTP-KLB will improve return or reliability. They only authorize one minimal design question:

> Can retaining the direction and the largest KL-safe fraction of each rare offending actor update preserve the downside protection observed under DRTP-KLR without discarding Original DRTP's upper-tail benefit?

## Frozen update semantics

All DRTP sampler, network, PPO, environment, reward, actor information boundary, and safety semantics remain unchanged. The default guard mode remains `none`.

For the opt-in `post_step_actor_backtrack` mode at each full-rollout PPO epoch:

1. Save the pre-step actor parameters and the complete model/optimizer transaction state.
2. Execute the ordinary Adam actor-and-critic step.
3. Evaluate empirical policy KL on the complete frozen rollout against its stored behavior-policy log probabilities.
4. If KL is at most `0.02`, accept the ordinary step exactly.
5. If KL exceeds `0.02`, keep the critic step and define

   \[
   \theta(\alpha)=\theta_{\mathrm{before}}+
   \alpha\left(\theta_{\mathrm{attempted}}-\theta_{\mathrm{before}}\right),
   \qquad \alpha\in[0,1].
   \]

6. Use exactly 24 deterministic bisection iterations to find the largest tested `alpha` whose complete-rollout empirical KL is at most `0.02`.
7. Set the actor parameters to that accepted point and stop the remaining PPO epochs for the update.
8. Retain the attempted Adam actor optimizer slots. This is a projected-Adam transaction: parameters are projected, while the attempted update's optimizer moments are not erased.
9. Restore the complete pre-step model and optimizer transaction and fail fast if any state, KL value, or final boundary assertion is non-finite or invalid.

The 24 bisection iterations are a fixed numerical resolution, not a tunable scientific parameter. The KL threshold remains the D1 value and may not be changed from D4 results.

## Required telemetry

The existing attempted/accepted KL and update telemetry is retained. D4 adds:

- `actor_projection_l2`;
- `policy_backtrack_alpha`;
- `policy_backtrack_iterations`;
- `actor_optimizer_state_retained_after_projection`;
- `critic_step_retained_after_policy_guard`.

Legacy DRTP-KLR telemetry and behavior remain available for archived reproducibility. No existing results are rewritten.

## Technical PASS conditions

D4 passes only if rollout-free tests establish all of the following:

- default-off and non-triggered updates are bitwise identical to ordinary PPO;
- a violating attempted step retains a non-zero actor displacement smaller than the attempted displacement;
- final empirical KL satisfies the hard boundary;
- critic updates and attempted actor Adam state are retained;
- non-finite transactions restore the complete pre-step state;
- deterministic replay and mid-course checkpoint save/reload are exact;
- legacy DRTP-KLR and frozen UTR/DRTP contracts still pass.

Even after technical PASS, no training is authorized. The next permissible action is human review followed by a separate D5 pilot-contract freeze using clean seeds not previously inspected for scientific performance.

## Mainline separation

DRTP-KLB belongs only to exploratory mainline B. It must not delay submission, replace evidence, or retroactively reinterpret the formal/independent cohorts in mainline A. A failure at any later B-line gate leaves mainline A unchanged.
