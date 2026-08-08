# Actor feature provenance specification v1.8 (R3)

**Status:** design specification; code changes deferred to R4.

The table defines the intended source of every actor feature. “Delivered” means
the packet has reached the receiver at the current simulator step; a pending
or dropped packet is unavailable. Cache values remain frozen at their last
delivery and expose age/confidence.

| Feature | Raw source | Sender → receiver | Local sensing? | Delivered comm? | Cache? | Validity / unavailable rule | Age/confidence | Actor or critic |
|---|---|---|---|---|---|---|---|---|
| self position | receiver UAV state | self → self | Yes | No | Optional | Always valid; self value | n/a | Actor |
| self velocity | receiver UAV state | self → self | Yes | No | Optional | Always valid | n/a | Actor |
| self heading | receiver UAV state | self → self | Yes | No | Optional | Always valid | n/a | Actor |
| self energy | receiver UAV state | self → self | Yes | No | Optional | Always valid | n/a | Actor |
| teammate position | explicit sender packet only | sender j → receiver i | No | Required unless local sensor | Yes | Zero/unavailable if no valid packet/cache; never simulator fallback | Packet age/confidence | Actor |
| teammate velocity | explicit sender packet only | j → i | No | Required unless local sensor | Yes | Same as teammate position | Age/confidence | Actor |
| teammate heading | explicit sender packet only | j → i | No | Required unless local sensor | Yes | Same as teammate position | Age/confidence | Actor |
| teammate energy | explicit sender packet only | j → i | No | Required unless local sensor | Yes | Same as teammate position | Age/confidence | Actor |
| teammate `detected_by` | sender packet field | j → i | No | Required | Yes | Unavailable without packet/cache; no global copy | Age/confidence | Actor |
| teammate `local_attack_window` | sender packet field | j → i | No | Required | Yes | Unavailable without packet/cache; no global copy | Age/confidence | Actor |
| target estimate | own radar or delivered target packet | self/j → i | Yes or no | Required for remote estimate | Yes | Zero/unavailable when no valid source | Estimate age/confidence | Actor |
| message age | environment delivery record | j → i | No | Required for non-self message | Yes | Max age/unavailable sentinel if no packet | Exact delivery age | Actor |
| message confidence | packet metadata | j → i | No | Required | Yes | Zero when invalid | Confidence plus age | Actor |
| relative position | derived | self/valid sender or target estimate → i | Uses legal inputs only | Indirect | Indirect | Zero/unavailable if either endpoint invalid | Derived from endpoint ages | Actor |
| relative velocity | derived | self/valid sender or target estimate → i | Uses legal inputs only | Indirect | Indirect | Zero/unavailable if endpoint invalid | Derived | Actor |
| distance | derived norm | legal endpoint pair → i | Uses legal inputs only | Indirect | Indirect | Zero/unavailable if endpoint invalid | Derived | Actor |
| LOS | derived from legal relative position | legal endpoint pair → i | Uses legal inputs only | Indirect | Indirect | Zero/unavailable if endpoint invalid | Derived | Actor |
| communication availability | delivered packet record | j → i | No | Yes | Current/cache status | 1 only after delivery; 0 for pending/drop/failure | Age of last delivery | Actor relation feature |
| perception relation | local sensing/valid target estimate | target → i | Yes or valid cache | Not by itself | Yes | 1 only with valid receiver-side target information | Target age/confidence | Actor relation mask |
| task-support relation | derived role + legal target/packet fields | legal sources → i | Possibly | Possibly | Possibly | 1 only when all required sources valid and delivered/known | Minimum source confidence | Actor relation mask |
| role identity | deployment configuration | static → all actors | No | No | No | Always valid static metadata | n/a | Actor and critic |
| relay-failure status | local observable delivery/age effects or explicit delivered status | environment → i only if observable | No global label | Only if packet field | Cache if explicitly sent | No simulator-global failure scalar; otherwise unavailable | Delivery age | Actor only when legal |
| target global state | simulator `red_pos`/`red_vel` | simulator → none | No | No | No | Forbidden in actor graph | n/a | Critic/evaluation only if protocol allows |
| all-blue shared state | simulator blue arrays | simulator → none | No | No | No | Forbidden in actor graph | n/a | Critic/evaluation only |
| aggregate connectivity / attack hold | simulator aggregate metrics | simulator → none | No | No | No | Forbidden in actor graph | n/a | Critic/evaluation only |

## Pairwise-geometry rule

Actor (i) may compute geometry to teammate (j) only from (i)'s own state
and the latest legal (j)-state in (i)'s packet/cache. The implementation must
not call simulator `blue_pos[j]`, `blue_speed[j]` or equivalent true state for
an unavailable teammate. For target geometry, use only (i)'s own radar/cache
estimate. If an endpoint is invalid, relative position, relative velocity,
distance and LOS receive the frozen unavailable encoding and cannot activate a
relation.

## Provenance versus relation masks

The provenance mask is a per-receiver, per-feature access decision made before
embedding. The relation mask is a separate decision about whether an already
legal feature participates in perception, communication or task-support
aggregation. A zero relation mask cannot legalize a globally constructed raw
feature. R4 tests must verify both masks independently.

## Matched-view requirement

Corrected EA-RG and corrected wider single-graph must receive byte-equivalent
raw recipient views before their encoder-specific relation processing, apart
from representation-specific derived relation masks that are explicitly part
of the frozen protocol. No external baseline may be given simulator-global
state to “repair” fairness.
