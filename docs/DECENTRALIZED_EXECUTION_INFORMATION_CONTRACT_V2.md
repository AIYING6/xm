# Decentralized execution information contract v2

This contract is an audit target, not a claim that all rows have passed implementation validation.

| Information | Actor access | Source | Hidden global truth required? | Failure/dropout effect |
|---|---|---|---|---|
| Own kinematics | legal | actor-local observation | no | own state remains available unless episode terminates |
| Role identity | legal | role embedding / role feature | no | fixed by agent identity |
| Locally sensed target | legal | local radar and `detected_by` | no | removed by sensing/dropout |
| Cached target | legal only when valid/delivered | `target_cache_*` | no | age/confidence/hop/path control validity |
| Delivered message | legal | communication update and cache delivery | no | delay/dropout suppresses delivery |
| Dropped/undelivered message contents | forbidden | environment bookkeeping only | yes | must not affect actor inputs |
| Remote UAV state | forbidden unless represented by legal delivered information | environment truth | yes | hidden changes must not affect actor output |
| Hidden target truth | forbidden | `red_pos` / target dynamics | yes | only legal sensing/cache projections may enter actor input |
| Perception relation | legal summary | `_get_graph_obs` | no if derived from legal sensing | changes with sensing |
| Communication relation | legal summary | `_get_graph_obs` | no if derived from reachable delivery | changes with range/dropout/failure |
| Task-support relation | legal summary | `_get_graph_obs` | no if derived from legal cache/closure state | changes after failure and cache loss |
| Union/global relation | legal union of legal relations | `_get_graph_obs` | no, subject to relation legality | must not add hidden truth |
| Centralized critic state | critic/environment-only | `share_obs` | allowed for CTDE critic only | never passed to actor |

Code anchors: `envs/uav_intercept_3d_env.py` (`_get_obs`, `_get_graph_obs`, `_update_sensing_and_comm`, `_info`) and `algorithms/ri_gmappo/simple_ri_gmappo.py` (`RIGMAPPOAgent.get_action_and_value`).

## Current disposition

The source contains legal-information projections and a centralized critic, but the required adversarial hidden-state invariance tests and mechanism provenance checks are not yet complete. Gate I remains pending until those tests pass.
