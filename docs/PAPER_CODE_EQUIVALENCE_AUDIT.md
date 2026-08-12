# Paper–Code Equivalence Audit (Phase 1)

Status: **FAIL / repair required before headline update**

Scope: `paper_latex_3d_en/sections/04_method.tex` versus `algorithms/ri_gmappo/simple_ri_gmappo.py` and `envs/uav_intercept_3d_env.py` at frozen baseline `4122f6d`.

## Findings

| Paper statement or symbol | Code evidence | Match | Required action |
|---|---|---|---|
| `A_ij=1` means sender `j` connects to receiver `i` | `envs/uav_intercept_3d_env.py:1209-1228` constructs `adj[i,j]` and relation arrays with receiver–sender convention | Yes | Preserve convention and add direct code anchor |
| Three relation channels: perception, communication, task support | `RELATION_PERCEPTION=0`, `RELATION_COMMUNICATION=1`, `RELATION_TASK_SUPPORT=2` | Yes | Keep, but verify every figure/table label |
| Edge features enter the message payload through `g^r(h_i,h_j,e_ij)` | `GraphAttentionLayer` and `RoleConditionedGraphAttentionLayer` use `edge_score(edge_feat)` to add a scalar attention-score bias; sender payload is `h_j` multiplied by a gate | **No** | Rewrite equations as edge-feature-modulated attention bias, not payload concatenation |
| Independent query/key projections `W_q h_i`, `W_k h_j` | Both graph layers expose a single shared `self.proj`; attention uses concatenated projected receiver/sender embeddings | **No** | Replace with the actual shared projection form |
| Relation-specific message function `g^r` | The same edge feature tensor is passed to each relation layer; relation-specificity comes from separate layer parameters and relation mask | Partial | State exactly where relation-specific parameters enter |
| Global residual connection across relations | `global_layer1`, `global_layer2`, union adjacency, `global_residual_weight`, concatenation into `fuse1/fuse2` | Partial / under-described | Explicitly include union/global branch in method and ablation plan |
| Role-pair gate is relation-specific | `role_pair_gate` exists per relation layer in each `ModuleList` | Yes | Add exact receiver/sender index formula |
| Gate Prior strength is 0.4 in the full method | `configs/paper/ea_rg_mappo_gate_prior.yaml` and code initializer | Verify per selected run | Link result provenance to exact config; do not infer from current CSV alone |
| Critic does not use graph gate | `RIGMAPPOAgent.critic_value` consumes shared observation and roles | Yes | Keep |
| 3DOF method uses an intent auxiliary head as a main computational component | The 3DOF graph stores `has_intent_label=False`; intent context is disabled in evaluator construction | Partial | Describe it as shape-compatible inactive auxiliary path unless training config proves otherwise |

## Conclusion

The method section is scientifically close in high-level graph semantics but is not equation-level equivalent to the frozen implementation. In particular, the attention equation and the treatment of edge features must be corrected before any new headline claim or confirmatory experiment is interpreted as validating the paper method.

No code or scientific protocol was changed by this audit.
