# Current graph semantics audit

`A[receiver, sender] = 1`: row `receiver` aggregates information from column `sender`. The GAT masks scores by this adjacency and computes a receiver-wise weighted sum over senders.

The physical blue-team communication layer may contain all six directed channels when geometry/range/dropout allow it:

Attacker→Relay, Attacker→Scout, Relay→Attacker, Relay→Scout, Scout→Attacker, Scout→Relay.

Communication is recalculated each step from inter-agent distance, range, node-failure state, and communication-dropout RNG. The graph's communication relation contains delivered communication; task-support is never an independent hidden channel because it requires delivered communication first.

Under the relay-dependent information contract, the nominal legal target-information route is `Scout → Relay → Attacker`. Direct `Scout → Attacker` cache delivery is rejected in nominal operation and becomes legal only as a recovery route during the existing full Relay-node-failure state. Actor input is limited to `obs`, `share_obs`, and the legal graph observation; simulator state, fault labels, full cache provenance, and unmasked topology cannot be passed as an actor feature.
