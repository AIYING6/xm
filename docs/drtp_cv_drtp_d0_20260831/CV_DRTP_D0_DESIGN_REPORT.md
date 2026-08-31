# CV-DRTP D0 design report

**Status:** `D0_DESIGN_FROZEN — TRAINING_NOT_AUTHORIZED`.

## Why this is a new route

All sampler-side candidates (trust region, uniform anchor and paired probe) and
post-update guards (KLR/KLB) are closed. Their results show that locally
constraining an adaptive sampler or a large PPO update does not reliably remove
training-seed downside. CV-DRTP therefore does **not** add another sampler
gate, KL threshold, probe rollout, reward term or policy input.

The single new hypothesis is that the scalar centralized state-value critic is
an inadequate variance-control device for the three-agent policy-gradient
update. A centralized action-value critic can supply a counterfactual baseline
for each agent while holding the other agents' sampled actions fixed:

`b_i(s, a_-i) = sum_a pi_i(a|o_i) Q_i(s, a, a_-i)`.

The actor uses `A_i^cf = stopgrad(Q_i(s,a_i,a_-i)-b_i(s,a_-i))`. The actor
observation and action interface are unchanged. The critic alone receives the
training-time legal centralized state and the sampled joint action; it receives
neither evaluation outcomes nor sampler state.

This is a new research hypothesis motivated by multi-agent policy-gradient
variance control, not a causal conclusion from the closed B1/B3/B5 mechanism
audits.

## Exact implementation boundary

The existing `RIGMAPPOAgent` uses a centralized scalar `V(share_obs, role)`.
CV-DRTP may replace that branch with `Q(share_obs, role, joint_action)` and
evaluate the finite action alternatives for the acting agent. It must preserve:

- Original DRTP selection semantics and every sampler constant;
- actor parameters, actor inputs, actor logits and PPO clipping rule;
- reward, environment, failure semantics, rollout length, optimizer and seeds;
- a default-off mode that is bitwise trajectory-equivalent to Original DRTP.

No claim of an exact low-variance guarantee is allowed with a learned critic.
The claim to test is empirical training reliability under a prospective,
two-cohort protocol.

## D1 technical acceptance, before any environment interaction

1. Default-off trajectory equivalence to Original DRTP.
2. Counterfactual baseline equals the policy-weighted finite-action Q average.
3. Actor receives no new observation or sampler information.
4. The critic target and reward tensors are unchanged.
5. Actor gradient is finite; the critic-gradient path is detached from the
   actor advantage exactly as specified.
6. Save/resume, RNG isolation, checkpoint compatibility and action-ordering
   checks pass.
7. Per-update telemetry records counterfactual advantage dispersion, Q spread,
   critic loss, policy KL and additional wall-clock cost.

Any failure ends the candidate as `CV_DRTP_D1_TECHNICAL_NO_GO`.

## Prospective outcome gate

If D1 passes and a separate cloud authorization is given, train
`UTR / Original DRTP / CV-DRTP` on two independently frozen cohorts of five
new seeds. At 0.5M the cohorts are assessed separately. Both must show a
strictly positive mean paired `J_pert_mean` gain versus UTR, at least four of
five non-negative gains, no new catastrophic seed, and lower range and sample
SD than Original DRTP. Mean loss versus Original DRTP may be at most the
frozen measurement margin `epsilon_J=7.874919837916801`; safety cannot worsen.

Failure of either cohort permanently closes CV-DRTP. No automatic 1M/3M run,
parameter sweep or CV-DRTP-v2 is permitted.
