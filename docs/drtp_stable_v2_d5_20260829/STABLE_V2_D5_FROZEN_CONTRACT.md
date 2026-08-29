# Stable-v2 D5 frozen pilot contract

## Scientific question

Does the technically validated DRTP-KLB candidate preserve Original DRTP's high-return capability while reducing paired downside and cross-seed dispersion at the 0.5M development horizon?

D5 is development-only. It neither changes nor delays mainline A and cannot be merged with any formal or independent cohort already used by the paper.

## Frozen design

- Arms: `UTR / Original DRTP / DRTP-KLB`.
- Clean paired training seeds: `3201 / 3202 / 3203`.
- Budget: exactly 1,953 updates = 499,968 environment steps per trajectory.
- Total: nine from-scratch trajectories.
- Milestones: 0.25M and final 0.5M, without checkpoint promotion.
- Evaluation: final 0.5M only on the independent development tape `560000–560099`.
- Conditions: Nominal, F0, T28, D120 and C28-120; 100 paired episodes per condition.
- DRTP-KLB: `target_kl=0.02`, 24 fixed bisection steps, `post_step_actor_backtrack`.
- PPO, architecture, reward, environment, sampler and actor information boundary remain frozen.

The experiment forbids early stopping, seed replacement, performance reruns, target-KL changes, bisection changes, checkpoint promotion, automatic continuation, or a parallel candidate.

## Frozen success criteria

Let paired robust-mean gain be

\[
G_{m,s}=J_{\mathrm{pert,mean}}(m,s)-J_{\mathrm{pert,mean}}(\mathrm{UTR},s).
\]

`D5_PILOT_GO_SIGNAL` requires all of the following:

1. **Four-endpoint advantage retention:** mean DRTP-KLB performance at Nominal, F0, perturbation mean and perturbation worst is no lower than Original DRTP by more than `epsilon_J=7.874919837916801`.
2. **Downside protection:** the worst paired gain improves over Original DRTP by more than the same frozen practical margin, and DRTP-KLB has zero catastrophic seeds.
3. **Seed reliability:** both paired-gain range and sample SD are strictly below Original DRTP.
4. **Direction consistency:** all three DRTP-KLB paired robust-mean gains are non-negative.
5. **Upper-tail retention:** for every seed where Original DRTP gain exceeds `epsilon_J`, DRTP-KLB is no more than `epsilon_J` below Original DRTP.
6. **Safety:** frozen pooled and seed-condition collision/timeout margins pass against both UTR and Original DRTP; no constraint-violation increase is allowed.
7. **Mechanism validity:** at least one but no more than 10% of actor epochs invoke backtracking, and every intervention obeys the frozen KL, projection, optimizer and critic transaction semantics.
8. **Integrity:** all nine final checkpoints, 4,500 raw evaluation records, manifests, telemetry and hashes are complete.

If every criterion except upper-tail assessability passes because none of the three Original DRTP seeds has gain above `epsilon_J`, the decision is `D5_PILOT_INCONCLUSIVE_UPPER_TAIL`. This does not authorize more seeds or continuation. Any other failure is `D5_PILOT_NO_GO`.

No D5 outcome automatically authorizes 1M, 3M, 10M, threshold tuning, or Stable-v3. A separate human decision is mandatory.
