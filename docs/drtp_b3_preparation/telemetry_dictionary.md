# B3 read-only telemetry dictionary

Two JSONL layers are written: every completed/partial episode is retained in
`episode_summary.jsonl`; step records are retained only for failure-relative
`tau = -20..60`. Nominal episodes use the frozen pseudo-onset 44. All fields
are captured after the production transition and are not actor/critic inputs.

| Field family | Source and meaning | Missing-value rule |
|---|---|---|
| identity | protocol, method, training seed, update, environment, episode and step IDs | never inferred |
| scenario and exposure | sampler group/member, scheduled onset/duration, failure active, `tau` | nominal uses pseudo-onset; unavailable values become JSON `null` |
| UAV state | three blue positions, reconstructed velocities, heading, gamma, target position, pairwise distances | arrays are immutable snapshots |
| topology | legal relation/union edges; direct/relay/no-path state; `path_switch_event` | first step has no prior path and cannot be a switch |
| information | Scout detection, Attacker valid/fresh target information, cache source/age/confidence/stale rate | environment-provided values only |
| task support | attack-window state, chain support/closure, relay-dependency eligibility | environment-provided values only |
| actions | sampled discrete actions and the corresponding existing `[turn, climb, accel]` command table entry | `max_action_probability=null`: production action API does not expose it and telemetry does not add a second actor forward pass |
| PPO | policy entropy is recorded where supplied by the training loop; existing PPO CSV remains the authority for loss/KL/clip/value/advantage/gradient diagnostics | no invented PPO quantity |
| outcome and reward | per-step reward, existing reward-component mapping, cumulative return, success/collision/timeout/constraint/terminal reason | non-finite values are converted to JSON `null` |

`failure_telemetry_state` (including buffered event rows, path state, counts,
and reward sums) is part of the runtime checkpoint. This is required for
mid-window save/resume equivalence.
