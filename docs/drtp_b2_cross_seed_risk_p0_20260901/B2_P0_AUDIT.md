# B2 P0: cross-seed lower-tail risk optimization feasibility audit

**Protocol:** `DRTP-B2-CROSS-SEED-LOWER-TAIL-RISK-P0-V1`  
**Scope:** zero training, zero evaluation, zero algorithm implementation  
**Mainline A:** unchanged  
**Decision:** `B2_P0_NO_GO`

## Question

Can a new update rule be trained to improve the lower tail over **complete
training-seed draws** while retaining DRTP's upside?  Let a training seed
`s` include initialization, environment and rollout randomness, minibatch
order, and all other training stochasticity. For an update-rule parameter
`phi`, the relevant outer quantity would be

`Z_s(phi) = training-run outcome after Train(s; phi)`.

A conceptual lower-tail objective is then, for example,

`max_phi E_s[Z_s(phi)] + lambda * LowerTail_alpha({Z_s(phi)})`.

This is **not** an episodic CVaR objective. Episodic risk-sensitive RL applies
a risk measure to returns drawn within an MDP under a policy. Here the random
variable is the outcome of an entire training run. The distinction is
material: an episode-level risk objective neither observes nor estimates the
cross-seed distribution of `Z_s(phi)`.

The methods literature supports the distinction, rather than closing it:

- [Prashanth et al., *Policy Gradients for CVaR-Constrained MDPs* (2014)](https://arxiv.org/abs/1405.2690)
  optimizes CVaR of stochastic-path costs in an MDP.
- [Tamar et al., *Policy Gradient for Coherent Risk Measures* (2015)](https://arxiv.org/abs/1502.03919)
  likewise treats risk measures in the policy/trajectory objective.
- [Xu et al., *Meta-Gradient Reinforcement Learning* (NeurIPS 2018)](https://proceedings.neurips.cc/paper_files/paper/2018/hash/2715518c875999308842e3455eda2fe3-Abstract.html)
  shows that an online meta-objective requires a separately defined proxy and
  update path; it does not make a complete-training-seed tail observable for
  free.
- [Jaderberg et al., *Population Based Training* (2017)](https://arxiv.org/abs/1711.09846)
  is an outer population optimization procedure, illustrating that robustness
  to training randomness requires multiple complete members and selection
  infrastructure.

These papers are method foundations only. They are not evidence that this
project already has a valid cross-seed objective or implementation.

## Frozen three-gate decision

| Core gate | Result | Audit finding |
| --- | --- | --- |
| Mathematical definition and estimator | **FAIL** | `Z_s(phi)` is well-defined conceptually, but no training-only observable estimator of its lower tail has been identified. B5 found no repeatable precursor chain and SR-P1 found no PP-disagreement rule that predicted conditional intervention utility. Replacing this missing estimator with episode CVaR would change the estimand. |
| Training-only interface | **FAIL** | `train_ri_gmappo` is a single-seed PPO entry point with ordinary `optimizer.step()` updates. It contains no cross-seed outer estimator or training-only outer endpoint. Building them would be a new algorithm/interface, prohibited at P0. |
| Affordable computation | **FAIL** | A deliberately optimistic lower bound for one finite-difference outer estimate is `2 sides × 4 controller coordinates × 8 independent full-training seeds × 499,968 = 31,997,952` environment steps. It excludes validation, UTR/Original comparisons, repeated estimates, and every later outer update. No such outer-loop budget is authorized. |

Because all three gates must pass, the final status is `B2_P0_NO_GO`.

## Static interface evidence

The read-only code audit found `train_ri_gmappo` and normal Adam
`optimizer.step()` calls in `algorithms/ri_gmappo/simple_ri_gmappo.py`. It did
not find an existing `meta_gradient`, `cross_seed_risk`, or
`training_only_outer_endpoint` interface. This does not say that such an
interface can never be engineered; it says it is absent now and cannot be
assumed valid without a separate implementation and verification project.

## Consequence and stop rule

No B2 P1 is authorized. No training, evaluation, hyperparameter sweep,
episode-CVaR substitution, or algorithm implementation follows from this
audit. This is a NO-GO for the proposed *current* B2 route, not a theorem that
cross-seed reliability research is impossible. Any future outer-loop project
would first need to establish a new training-only lower-tail proxy and prepay
an explicit replication budget; it must begin under a new contract rather than
as B2 continuation.
