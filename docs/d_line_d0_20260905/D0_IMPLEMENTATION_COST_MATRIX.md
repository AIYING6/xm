# D0 implementation-cost and asset matrix

| Item | A service continuity | B version consistency | C recovery-state migration |
|---|---:|---:|---:|
| Reusable repository assets | Dynamic topology, fault traces, reproducible runner | Packet caches, timestamps, topology traces, reproducible runner | Dynamic topology, failure/recovery traces, reproducible runner |
| Existing semantic gap | No routing, capacity, or migration transition action | No distributed synchronization/ownership/version-feasibility action contract | No route state, migration state, reservation, or failback action |
| New environment contract size | High | High | High |
| Exact oracle design | Time-expanded MCF/MILP (available but generic) | DCOP/MIP, potentially exponential in version conflicts | DP/MIP under recovery state (available but generic) |
| Main-solver development risk | High: duplicate of ILP/online reconfiguration | Very high: special structure unknown | High: likely generic switching control |
| Deterministic paired-instance evaluation | Yes | Yes | Yes |
| D0 cost conclusion | Not justified by novelty | Not justified until a distinct graph structure is proved | Not justified by novelty |

## Static source evidence

`envs/redundant_topology_uav_env.py` already stores terminal caches, sensing/receipt timestamps, active adjacency, failures, and recovery times. Its routing is fixed scout→relay→terminal inside `_sense_and_route`; relay non-idle actions do not become route/capacity/migration decisions. Therefore the old code is useful infrastructure and a semantic trace generator, not a pre-existing implementation of any D0 solver problem.
