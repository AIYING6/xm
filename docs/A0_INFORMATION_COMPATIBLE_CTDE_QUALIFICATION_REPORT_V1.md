# A0 information-compatible CTDE qualification report (v1)

Status: `A0_NO_GO__CURRENT_LEGAL_ADVANTAGE_PROJECTION_REDUCES_TO_EXISTING_HISTORY_LOCAL_CRITIC_LINE`

## Frozen read-only audit

The audit replayed the two frozen strict-contract L4 MAPPO checkpoints
(`8901`, `8902`) on the 32 frozen episode seeds `890000..890031`.  It neither
trained a model nor executed a counterfactually altered transition.

At selected states, the Attacker had no fresh/cache-valid target evidence while
the simulator-wide last-detected target estimate existed.  The audit changed
only that global estimate in the centralized `share_obs`, asserting byte-exact
invariance of every Attacker actor input: local observation, recipient graph
node/edge features, roles, adjacency and relation adjacency.

| Frozen checkpoint | Selected actor-blind / critic-visible states | Actor-input invariance | Median \(|ΔV_c|\) | P90 \(|ΔV_c|\) | One-step TD sign conflict |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8901 | 2,586 | 100% | 0.725 | 0.813 | 58.4% |
| 8902 | 2,580 | 100% | 0.545 | 0.779 | 62.5% |

Across selected states, `SD(V_c)=1.586`.  Thus both median shifts exceed the
pre-registered materiality threshold `0.10 × SD(V_c)=0.159`.  The phenomenon
gate therefore passes:

`A0_PRIVILEGED_CRITIC_MISMATCH_OBSERVED`

This is evidence that the current centralized critic is materially sensitive
to a training-only estimate that an actor cannot distinguish at the audited
decision point.  The TD result is an evaluator-side one-step proxy: it does
not prove policy-gradient bias, performance harm, or that replacing the critic
will improve mission completion.

Raw records and hashes are retained only under the untracked results directory
`results/a0_information_compatible_ctde_audit/`.

## Novelty red-team decision

The candidate actor update,

`A_legal(I_i, a_i) = E[A_central | I_i^legal, a_i]`,

is not, as currently specified, a new estimator.  It is an
information-conditional regression target implementable by a local/history
critic; its residual subtraction is a standard conditional-projection or
control-variate operation.  Existing work already analyzes history/state
critics under partial observability, asymmetric privileged critics, and local
advantage critics.  In particular, Lyu et al. analyze state/history critic
trade-offs and history-state critics; Lambrechts et al. establish asymmetric
actor-critic theory; and ROLA provides a local advantage critic with
centralized training.  See the linked sources in
`A0_INFORMATION_COMPATIBLE_CTDE_NOVELTY_RED_TEAM_V1.md`.

Therefore, the present phenomenon is scientifically real but **does not
qualify the proposed mechanism as a defensible new main algorithm**.  No
implementation, pilot, or training is authorized from A0.

## What remains valid

The strict actor contract and the A0 audit are useful research infrastructure.
They establish a reusable diagnostic requirement for any future CTDE proposal:
it must state exactly which critic information is incompatible with the actor,
and it must prove a distinction from local/history critic, history-state critic,
ROLA-style advantage, and ordinary critic-distillation baselines before
training.
