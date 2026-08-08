# Fixed sender-status packet schema v1.8

**Status:** frozen before implementation/pilot.

## Packet fields

| Field | dtype / shape | Sender-side source | Send-time value | Delivery/cache semantics | Unavailable encoding | Actor/relation use |
|---|---|---|---|---|---|---|
| `sender_id` | int scalar | sender index | sender index | static in every delivered/cache record | `-1` only for empty record | node identity/debug |
| `sender_role` | int scalar | static UAV type | configured role | static metadata | known from configuration | role embedding/support relation |
| `position` | float32[3] | sender `blue_pos[sender]` | copied at send step | fixed at send; cache never truth-refreshes | zeros + `validity=0` | teammate node/derived geometry |
| `velocity` | float32[3] | sender speed/heading/gamma | converted at send step | fixed at send | zeros + validity=0 | teammate node/derived geometry |
| `heading` | float32 scalar | sender heading | copied at send step | fixed at send | zero + validity=0 | teammate node |
| `energy` | float32 scalar | sender energy | copied at send step | fixed at send | zero + validity=0 | teammate node |
| `detected_by` | float32 scalar | sender local detection flag | copied at send step | fixed at send | zero + validity=0 | local-status feature/support |
| `local_attack_window` | float32 scalar | sender local attack-window flag | copied at send step | fixed at send | zero + validity=0 | local-status feature/support |
| `target_pos` | float32[3] | sender target cache position | copied from eligible target cache | existing target-cache delivery semantics | zeros + target validity=0 | target estimate/support |
| `target_vel` | float32[3] | sender target cache velocity | copied from eligible target cache | existing target-cache delivery semantics | zeros + target validity=0 | target estimate/support |
| `target_confidence` | float32 scalar | sender target-cache confidence | copied at send | decays only when a new packet is created; cache holds last value | zero | target feature |
| `target_generation_step` | int scalar | sender cache metadata | copied at send | fixed in cache | `-1` | target age/debug |
| `target_hop_count` | int scalar | sender cache metadata | copied at send | fixed in cache | `-1` | target provenance |
| `send_step` | int scalar | environment step counter | current step | fixed | `-1` | age |
| `delivery_step` | int scalar | environment delivery event | actual delivery step | set only on delivery; pending remains unavailable | `-1` | age/availability |
| `validity` | float32 scalar | delivery/cache resolver | 1 only after valid delivery | zero on empty/expired/dropped record | zero | provenance mask |

## Delivery rules

- Pending packets are unavailable and cannot update actor views.
- Dropped packets are never inserted into receiver cache.
- Delayed packets become available only at their delivery step.
- A delivered packet snapshots sender fields at send time.
- A cached packet retains the last delivered snapshot; simulator truth changes
  do not refresh it.
- Relay failure prevents delivery when either endpoint is failed, preserving the
  existing failure/loss/delay mechanics.
- No failure label, global connectivity, aggregate attack-hold state, critic
  shared state or future packet payload is included.

The schema changes the communication payload and actor-information protocol;
sensing physics, UAV/target dynamics, packet loss/delay mechanics and relay
failure dynamics remain unchanged.
