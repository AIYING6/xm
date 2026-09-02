# Novelty map

Nearest method families:

- [Jiang et al. (2021), Prioritized Level Replay](https://proceedings.mlr.press/v139/jiang21b.html)
- [Narvekar et al. (2020), Curriculum Learning for Reinforcement Learning Domains](https://www.jmlr.org/papers/v21/20-212.html)
- [Mehta et al. (2020), Active Domain Randomization](https://arxiv.org/abs/2002.07911)
- [Rajeswaran et al. (2017), EPOpt](https://arxiv.org/abs/1610.01283)
- [Schaul et al. (2016), Prioritized Experience Replay](https://arxiv.org/abs/1511.05952)

Prioritized Level Replay and active/self-paced domain-randomization use learning- or policy-dependent signals to alter task distributions. Prioritized replay reweights stored transitions rather than frozen environment-condition exposure. The repository's existing SNR control is a static non-uniform reset sampler, but its weights are manually fixed and not derived from topology.

No exact match was identified in this targeted audit for a policy-independent topology prior plus an L1-bounded residual sampler in this relay-failure MARL interface. That absence is not enough for a novelty claim: the proposed `p0` itself is underdetermined. **Novelty status: unresolved / not claimable.**
