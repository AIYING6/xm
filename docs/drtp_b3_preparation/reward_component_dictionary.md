# B3 reward-component dictionary

This dictionary is observational. B3 reads only the environment's existing
`info["reward_components"]`; it does not add, rename, proxy, or reweight a
reward term.

| Logged key | Production definition | Scope |
|---|---|---|
| `progress` | `0.25 * clip((previous_range-current_range)/1000,-1,1)` | shared base reward |
| `tracking` | `0.12 * tracking` | shared base reward |
| `attack_window` | `0.18 * window` | shared base reward |
| `connectivity` | `0.05 * communication_connectivity` | shared base reward |
| `message_age_penalty` | `-0.03 * min(1, mean_message_age/80)` | shared base reward |
| `tracking_gain` | `0.05 * max(0, tracking-previous_tracking)` | shared base reward |
| `attack_window_gain` | `0.08 * max(0, window-previous_window)` | shared base reward |
| `attack_geometry` | configured `attack_geometry_reward_weight * attack_geometry_score` | shared base reward |
| `reclosure_bonus` | existing `post_loss_chain_reclosure_bonus` | shared base reward |
| `safety_proximity_penalty` | configured negative proximity penalty | shared base reward |
| `success` | terminal `+2.0` when success | terminal shared term when present |
| `collision` | terminal `-2.0` when collision | terminal shared term when present |
| `constraint_violation` | terminal `-1.5` when violated | terminal shared term when present |
| `role_specific_bonus_by_agent` | existing Scout detection, Relay connectivity, and Attacker/interceptor window bonuses | per-agent vector |
| `energy_penalty_by_agent` | existing `-0.02 * (1-energy)` | per-agent vector |

The alternative `v16r_mission_mode` has a smaller component set. B3's frozen
production contract does not change mode; if that mode is ever selected by a
validated configuration, the telemetry records exactly the keys emitted by
the environment rather than synthesizing the standard-mode keys.
