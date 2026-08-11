# M1-R2 evidence-valid robust acquisition projection qualification v1

**Final status:** `M1R2_NO_GO__NO_METHOD_IMPLEMENTATION_OR_TRAINING`

## Scope

M1-R2 examined one final pre-implementation candidate, **Evidence-Valid Robust
Acquisition Projection (EV-RAP)**. The candidate would have projected a
continuous MAPPO turn/climb command to the nearest command that makes one-step
progress toward attack-range acquisition under a target uncertainty set derived
from recipient-valid target evidence. This qualification was deliberately
limited to (i) a literature red-team and (ii) a checkpoint-only feasibility
audit. It did not implement a projection layer, alter an environment, or train
any policy.

The intended information boundary was sound in principle: target information
would be sourced only from current local sensing or a delivered, cache-valid
packet, together with its age, confidence, provenance, own 3DOF state, and
publicly frozen kinematic bounds. It would not read current target truth,
`last_detected_target`, evaluator geometry, critic state, or a target-policy
rollout.

## Candidate and pre-frozen test

For a valid target cache with packet position \(p_c\), age \(a\), public target
maximum speed \(v_{max}\), and attacker position \(p_A\), M1-R2 fixed the
conservative legal target set before replay as

\[
  \mathcal{U}(p_c,a) = \{p: \lVert p-p_c\rVert \le a v_{max}\}.
\]

The certificate used the corresponding worst-case attack-range deficit

\[
  d_{rob} = \max(0, \lVert p_c-p_A\rVert + a v_{max} - R_{attack,max}).
\]

At each decision state, it enumerated the nine actually executable
turn/climb guidance trends. A progress action existed only if its exact
one-step own-state transition strictly reduced \(d_{rob}\). The evaluator-only
`NO_ATTACK_RANGE_ACQUISITION` label selected episodes; it was not a certificate
input. The audit additionally counterfactually changed true target/global
detection values while holding the legal cache fixed and asserted that every
certificate quantity was unchanged.

The pass rule was frozen before replay: for **each** L4 checkpoint, at least
25% of valid-evidence decision states and at least 25% of selected failure
episodes had to be repairable--i.e., an enumerated progress command existed
while the checkpoint's chosen command was not progress-making.

## Offline feasibility result

The audit replayed the two frozen corrected-contract L4 checkpoints (training
seeds 8901 and 8902), using the same 32 episode seeds used in the earlier stage
localization. Each checkpoint had 12 evaluator-labeled
`NO_ATTACK_RANGE_ACQUISITION` episodes with legal attacker target evidence.

| Frozen checkpoint | Valid-evidence decision states | States with a robust progress action | Repairable states | Failure episodes with a repairable state |
| --- | ---: | ---: | ---: | ---: |
| seed 8901 | 1,082 | 0 / 1,082 | 0 / 1,082 | 0 / 12 |
| seed 8902 | 1,083 | 0 / 1,083 | 0 / 1,083 | 0 / 12 |

Thus the proposed worst-case, one-step progress set was empty in every one of
the **2,165** legal-evidence decision states selected by the existing dominant
failure mode. The pre-frozen offline verdict is
`M1R2_OFFLINE_FEASIBILITY_NO_GO__ROBUST_PROGRESS_SET_NOT_SUFFICIENTLY_AVAILABLE`.
The raw audit manifest is intentionally an untracked development artifact at
`results/m1r2_evidence_valid_robust_acquisition_audit_v2/`.

This is not a claim that the physical task is impossible, nor that no nominal
action can ever improve an estimated target range. It is a narrower and
decisive finding: under the candidate's own legally conservative, age-bounded
worst-case constraint, the central feasible set is unavailable. Relaxing the
set after seeing this result would convert EV-RAP into an unprincipled
nominal-target filter and violate this qualification's purpose.

## Literature red-team

The candidate's generic operation--minimal modification of a learned continuous
action to satisfy state-dependent Lyapunov/CBF-style constraints under
uncertainty--is established prior art. [Safe Policy Learning for Continuous
Control](https://proceedings.mlr.press/v155/chow21a.html) projects policy
outputs onto state-dependent Lyapunov constraints. [Robust Safe RL Using Robust
CBFs](https://arxiv.org/abs/2110.05415) and [robust CBFs with sector-bounded
uncertainty](https://arxiv.org/abs/2109.02537) provide uncertainty-aware,
differentiable safety filtering with minimal intervention. State-estimation
uncertainty is also directly addressed by [Safe Navigation Under State
Uncertainty](https://doi.org/10.1109/LRA.2026.3653366).

The only potentially narrower distinction was the source of the constraint:
recipient-valid, age-bounded communication evidence instead of a directly
available state estimate. That distinction is scientifically important for the
project's actor contract, but it does not by itself supply a strong new control
principle. It is especially insufficient here because the proposed robust
constraint has no applicable action set in the observed target failure states.

## Decision

`M1R2_NO_GO__NO_METHOD_IMPLEMENTATION_OR_TRAINING`

EV-RAP must not be implemented, relaxed, tuned, or evaluated as a policy
method. In particular, the following are not authorized: changing the
uncertainty radius after replay, substituting target truth for legal cache
state, replacing the worst-case condition by a post-hoc nominal condition,
adding prediction/world-model components, or launching a pilot.

M1-R2 therefore closes the current algorithm-mechanism search. The preserved
project assets remain the strict actor-information contract, independent
physical neutralization outcome, controlled learnability ladder through L4,
and the evidence-to-attack-range failure localization. Any future paper must
position those assets honestly rather than present a rejected mechanism as a
method contribution.
