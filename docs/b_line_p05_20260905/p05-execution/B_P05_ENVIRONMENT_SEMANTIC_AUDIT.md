# B-line P0.5 environment semantic audit

**Verdict:** `B_P05_SEMANTIC_PARTIAL`.

This static audit reads source files only: zero environment construction or steps, PPO updates, solver calls, training, checkpoint loading, evaluation episodes, and evaluation-tape reads.

## Decision

The current environments do contain native, time-dependent information semantics: message/cache age, cache freshness limits, and—within the six-UAV environment—an action mask that removes actions lacking a fresh routed token. The relevant age/topology information is actor-legal in the existing interfaces, while `info`-only failure labels are excluded.

However, neither audited environment contains the exact pair assumed in B-line P0: a maximum **consecutive route-outage** contract coupled to an available `reconfigure_relay` action. Therefore the P0 toy counterexample cannot be upgraded as an exact reconfiguration problem for the present environment.

## Classification ledger

| Item | Classification | Consequence |
| --- | --- | --- |
| 3D message/cache freshness | `environment_native_semantics` | Native information validity / targeting availability changes; it is not a route-outage termination or mandatory reconfiguration rule. |
| 3D node-failure schedule | `environment_native_semantics` | Failure is native, but no maximum consecutive outage or relay-reconfiguration action is imposed. |
| 6-UAV cache freshness | `environment_native_semantics` | Native cache age changes the real currently legal terminal-action set, but it is data freshness, not a measured consecutive route-outage duration. |
| Temporal reconstruction | `legally_derivable_internal_state` | Supports a future history-aware formulation, but does not create a native reconfiguration requirement by itself. |
| P0 maximum consecutive outage with relay reconfiguration | `newly_introduced_assumption` | The existing P0 counterexample cannot be promoted as an exact target-environment reconfiguration problem. |

## Boundary

This is not `B_P05_SEMANTIC_NO_GO`: a native history-sensitive freshness problem exists. It is not `B_P05_SEMANTIC_PASS`: the exact P0 continuity/reconfiguration assumption is new rather than environment-native.

The only scientifically permitted follow-up is a fresh, zero-training P0 reformulation that uses an explicitly chosen native freshness state and an existing action interface. It must again establish whether same current snapshot but distinct legal histories force distinct decisions. Solver design, PPO, benchmark training, parameter changes, and environment/reward changes remain prohibited.
