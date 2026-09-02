# Role capability contract

| Role | CAN | CANNOT | observation / communication | success and failure meaning |
|---|---|---|---|---|
| Scout | acquire one objective token per decision interval; sense and timestamp target estimate; transmit to a legal relay | terminal action; invent target truth | local flight state plus its sensed objective; emits provenance-tagged token | loss reduces parallel sensing capacity; surviving Scout can cover outstanding objectives sequentially |
| Relay | receive, cache, deduplicate and forward valid Scout-originated tokens | sense target ground truth; terminal action | local flight/radio/cache state; forwards only legal fresh tokens | loss reduces routing capacity/redundancy; no bypass is opened |
| Terminal | receive fresh valid relay-forwarded token; execute one assigned/unassigned objective action per interval | scout-level remote observation; fabricate valid support | local flight state plus valid token age/provenance | loss reduces parallel execution capacity; survivor may complete remaining objective if deadline margin permits |

Instances within a role are exchangeable: no agent-ID ability, observation feature or reward bonus exists. Their real value is finite per-interval capacity: multiple Scouts can acquire multiple objectives, Relays provide independent forwarding branches, and Terminals complete multiple objectives in parallel or sequentially after failure.
