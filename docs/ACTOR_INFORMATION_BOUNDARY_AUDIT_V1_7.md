# Actor information-boundary audit v1.7

**Result: P0 BLOCKER — stop manuscript rewrite pending author decision.**

## Code path audited

The environment builds one whole graph in `UAVIntercept3DEnv._get_graph_obs()`.
`stack_graphs()` batches that graph, and `RIGMAPPOActor.forward()` consumes the
whole `node_feat`, `edge_feat`, `role`, `adj`, and `relation_adj` tensors before
selecting the first `num_agents` graph rows for policy logits. The graph is
software-centralized/vectorized; this audit does not infer a distributed graph
builder from that implementation.

## Actor-visible field trace

| Input | Code source / physical source | Availability control | Actor-visible conclusion |
|---|---|---|---|
| Self position, speed, heading, velocity, energy | `_get_obs()` and all blue rows of `_get_graph_obs()` | Always present | Actor-visible local/self state |
| Teammate position, speed, heading, velocity, energy | Other blue node rows in `_get_graph_obs()` | Node rows are populated globally; only graph attention adjacency gates message aggregation | Potential leakage: no per-UAV provenance mask proves these physical states were locally sensed or delivered |
| Target position/velocity | `_target_state_for_graph_observation()` | Zero-masked in strict target sensing + agent-target-info-bottleneck; otherwise global target state | Target node is masked under the locked bottleneck, but this does not solve teammate-state provenance |
| Per-agent `detected_by` and `local_attack_window` | Blue node features | Populated for every blue node; no recipient-specific masking | Actor-visible global per-agent status through graph rows/attention |
| Local observation target relative state, range, velocity | `_get_obs()` | Zeroed when the acting agent lacks target information; cache/detection rules apply | Correctly masked for the acting agent |
| Communication history / message age | `message_age`, local obs and edge feature `age` | Delivered communication updates `comm_adj`; age is included in edge features | Actor-visible, but edge/node provenance is not independently access-controlled |
| Message loss and delay | `comm_adj`, `message_age`, config fields | Applied by environment delivery logic | Observable through adjacency/age; no evidence that unrelated node state is masked when delivery is absent |
| Target cache | Per-agent cache in `_get_obs()`; graph target is zeroed under bottleneck | Fresh-cache test for local observation | Local cache path is controlled; graph does not expose target cache contents |
| Relation adjacency: perception | `detected_by[i]` for blue-to-target | Environment relation mask | Actor-visible as an attention mask |
| Relation adjacency: communication | Delivered `comm_adj[i,j]` | Environment delivery mask | Actor-visible as an attention mask |
| Relation adjacency: task support | Role compatibility plus delivered communication and source information | `_active_support_edge()` | Actor-visible as an attention mask; not an independent physical channel |
| Edge features | Relative position/velocity, distance, LOS, same-team, sensing, comm, support, age, confidence | Edge values are populated for every pair; masks affect attention | Potential leakage through relative physical geometry for pairs lacking an admissible observation path |
| Failure state | `node_failure_active` is used in environment and metrics; no explicit failure scalar in actor node/obs schema | Failure affects delivered communication and relations | Indirectly actor-visible through adjacency/age; not a separately audited local observation |
| Attack-window state | `local_attack_window` per blue node; global `attack_window` in critic share state | Local field is not recipient-masked in graph | Actor-visible per-agent status; global versus local provenance must be distinguished |
| Role information | Role one-hot in obs and node features; role embedding in actor | Always present; `no_role_identity` ablation zeros it | Actor-visible identity, intended static metadata |
| Critic shared state | `_get_share_obs()` includes all blue states, target state, mean connectivity/age/detection/attack hold and step | Passed only to `critic_value()` | Critic-only by call path; CTDE claim depends on actor leakage audit above |

## Boundary findings

### A. Centralized/vectorized software graph construction

**Confirmed.** One environment instance constructs a complete graph tensor and
the policy receives the batched tensor. This is a software implementation fact,
not evidence of distributed per-UAV graph construction.

### B. Decentralized actor information dependence

**Not established; P0 blocker.** The target-state bottleneck and local target
mask are real controls. However, every blue node's physical state and local
status are inserted into the shared graph, and pairwise edge geometry is
computed centrally. Attention masks gate aggregation but do not themselves
prove that the underlying node/edge features were legitimately available to the
receiving UAV. In particular, “edge masked” is not equivalent to “unavailable
node feature removed from the actor.” The current implementation therefore
cannot safely support an unqualified decentralized actor-execution claim.

### C. Distributed per-UAV graph construction

**Absent in audited code.** No per-UAV graph builder or independently scoped
graph construction path was found. The manuscript must not claim that each UAV
independently constructs its own graph.

## Required stop condition

This is a real information-boundary blocker under the project decision rule.
No training code, architecture, v1.6 result, or scenario is modified here. The
author must choose whether to (i) weaken the manuscript to centralized actor
graph processing / software-vectorized execution with explicit information
limitations, or (ii) authorize a separately designed actor-boundary repair and
new evidence. Until that decision, Stage 5 claim rewriting and submission
packaging are paused.
