# RNG invariance report

Status: `PASS`.

With identical seed and stochastic policy stream, enabling the telemetry
writer did not change action, reward, done, failure-active, PPO log, sampler
log, or model hash. The writer is invoked after `env.step` and returns no
value to policy, critic, sampler, reward, or termination code. It also does
not request a second actor forward pass to obtain unexposed action
probabilities.
