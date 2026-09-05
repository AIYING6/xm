# B-line baseline and novelty map — P0 only

No named external method is asserted here. A later literature audit must populate any specific comparator with a verified source.

| Comparator layer | Required capability | Candidate comparator class | What it tests |
| --- | --- | --- | --- |
| L1 | No topology reconfiguration | fixed assignment / no action | Whether reconfiguration matters at all |
| L2 | Current topology only | snapshot-aware deterministic replan | Whether transition history adds information beyond `A_t` |
| L3 | Current topology plus feasibility | connectivity-constrained snapshot assignment | Whether history helps beyond ordinary connectivity constraints |
| L4 | Transition-aware | verified transition-aware deterministic comparator | Whether the eventual method is distinguishable from prior transition-aware planning |

P0 novelty is not a performance claim. Its sole potential novelty premise is the decision insufficiency of an otherwise identical current topology under a legitimate transition-continuity state.
