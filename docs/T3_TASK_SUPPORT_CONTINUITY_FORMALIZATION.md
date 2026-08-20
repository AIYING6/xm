# T3 — Task-Support Continuity Formalization

## Status and scope

This is a development-only formalization based on source-closed T1 UTR-SG telemetry. It does not upgrade T2's M2 association to a causal claim and does not authorize a new method, implementation, rollout, or training.

The frozen framing remains: weaker topology-robust policies are associated with poorer task-support continuity across topology transitions. It does not assert that relay failure necessarily removes information. The definition is path agnostic, so legal support may switch from relay-mediated to direct.

## Actor-local execution history

For agent `i`, the execution-time legal history is

\[
\mathcal H_i^t=\{o_i^{t-L+1:t},G_i^{t-L+1:t},m_i^{t-L+1:t}\},
\]

where `o` is the actor observation, `G` is the actor-legal local graph, and `m` contains only messages admitted by the S2 actor-information boundary. No global topology, simulator truth, route reconstruction, failure label, central critic input, future state, or terminal flag is included.

## Reproducible attacker continuity label

T1 exposes the validated diagnostic-only variable `diagnostic.info.attacker_legal_target_information_t`. For attacker `A`, T3 defines the training-only future-continuity target

\[
Y_A^t(H)=\mathbb 1\left[{1\over H}\sum_{k=1}^{H}I_A^{t+k}\ge0.75\ \land\ \operatorname{maxZeroRun}(I_A^{t+1:t+H})\le4\right],\qquad H=16.
\]

`I_A` is the validated legal-target-information diagnostic, never an actor input. It is one when legal target information persists through the next 16 steps. It does not require a fixed relay/direct route, a graph path, an explicit failure event, or a future terminal/success/return label. Thus it remains meaningful under nominal operation and after topology switches. It could only be a CTDE-style auxiliary target after independent authorization; execution could at most estimate `P(Y_A^t=1 | H_A^t)`.

## Role interpretation and limits

| Role | Actor-local semantic question | Direct T1 training target status |
|---|---|---|
| Scout | Can local progress and legal messages continue to supply task evidence? | No independently validated scalar target. |
| Relay | Can legal links/routing continue to bridge task-relevant support? | No independently validated scalar target. |
| Attacker | Will legal target information remain available through the next short window? | Reproducibly constructible as `Y_A^t(16)`. |

T3 therefore does not license invented Scout/Relay labels or a three-role supervision scheme. Scout and Relay can contribute through the existing legal graph, but only attacker-side continuity is directly grounded.

## Information boundary and leakage audit

The offline predictor uses only `actor.obs[2]` plus a compact actor-legal graph summary: attacker incoming/outgoing edge-feature means, relation in/out degrees, and adjacency degrees. It excludes `share_obs`, every `diagnostic` field, simulator positions, reconstructed path truth, failure truth, final outcome, and termination state.

| Variable | Execution status | Offline control status |
|---|---|---|
| scheduled onset/duration and scenario identifier | prohibited | metadata-only shortcut control |
| `failure_active_post` | prohibited | metadata-plus-failure control |
| terminal remaining steps | future-only / prohibited | oracle shortcut control |
| `attacker_legal_target_information_t` | diagnostic-only | label source only |
| global route/connectivity | prohibited | never used |

The target is reproducibly constructible, but constructibility alone is not a method rationale. A candidate continuity-state method would also need material actor-legal temporal gain, assessed in the T3 offline report.
