# FORMAL_EFFICIENCY_PROTOCOL_V1_5

> Status: FROZEN — defines the efficiency / communication-overhead evaluation
> for the v1.5 study. Uses the LOCKED checkpoints ONLY (no reselection, no
> retraining). This protocol is written AFTER `formal-robustness-results-lock-v1.5.0`;
> it does not redefine the main method and does not perform test-set model
> selection.

---

## 1. Methodological fix (why this protocol exists)

Robustness showed `w/o Role-Pair Gate` slightly better on some strong
conditions. **This does NOT make it the new "main method"** — Full EA-RG is the
pre-registered main method (validated → held-out → robustness); `w/o RPG` is an
ablation. Efficiency evidence decides how the Role-Pair Gate module is
**discussed**, never which checkpoint is the main model (no test-set model
selection).

Therefore the efficiency experiment includes **both Full and w/o RPG** and
reports them symmetrically.

## 2. Methods (5)

```
full_ea_rg            (main, frozen)
w_o_role_pair_gate    (ablation, kept for efficiency verdict)
mappo                 (strong baseline)
happo                 (strong baseline)
param_matched_single  (budget-matched strong baseline)
```

Locked checkpoints (seed 0 for primary profiling; seeds 0/1/2 for repeat
variability; from `formal-robustness-results-lock-v1.5.0` manifest):

| method | checkpoint | update | file |
| --- | --- | --- | --- |
| full_ea_rg | V14/ea_rg_mappo_s_gate_prior/ppo_seed0_1m | 700 | actor_critic_update_0700.pt |
| w_o_role_pair_gate | V15/w_o_role_pair_gate/ppo_seed0_1m | 100 | actor_critic_update_0100.pt |
| mappo | Mappo/ppo_seed0 | 600 | actor_critic_update_0600.pt |
| happo | V14/happo/ppo_seed0_1m | 300 | happo_update_0300.pt |
| param_matched_single | V14/param_matched_single/ppo_seed0_1m | 500 | actor_critic_update_0500.pt |

Checkpoint facts (measured 2026-08-07, seed0, FP32):

| method | file KB | tensors | total params | structure |
| --- | --- | --- | --- | --- |
| full_ea_rg | 489.8 | 74 | 117,302 | actor.multi_relation_graph 86,016; actor heads; critic.net 7,617 |
| w_o_role_pair_gate | 489.8 | 74 | 117,302 | identical weights (ablation = forward semantics only) |
| mappo | 66.2 | 12 | 15,708 | actor.net 8,411 + critic.net 7,297 |
| happo | 450.1 | 84 | 107,313 | policies.0/1/2 each 35,771 |
| param_matched_single | 343.7 | 34 | 84,694 | single-graph GAT + critic.net 14,497 |

## 3. Hardware freeze (must be recorded once)

```
GPU, CUDA, PyTorch, driver, CPU, RAM, Windows version
precision = FP32 (no AMP / TF32 switch mid-run)
torch.backends.* frozen (defaults; no torch.compile — eager inference only)
```

No switching of AMP/TF32/compile mode between methods.

## 4. Measurement blocks

### 4.0 Timing unit (frozen): ONE JOINT TEAM DECISION

All latency / throughput numbers are expressed per **one joint team decision**
(3 blue agents acting from one environment state), NEVER per single-agent
forward. This is required for fair comparison across architectures:

```
batch=1 : 1 env state -> full joint action of 3 blue agents
batch=8 : 8 env states -> 24 agent actions (3 agents x 8 envs)
```

- HAPPO: all three policies are forwarded (policies.0/1/2) and summed for the
  joint action.
- MAPPO: shared actor produces the full 3-agent action batch (obs concat
  role-onehot, 3 rows).
- Full / w/o RPG / param_matched: forward produces all 3 agent actions.

`latency` and `decisions/s` are defined on this joint-decision unit.

### 4.1 Parameters / model complexity (static; no env)

Per method: actor / critic / graph-encoder / total trainable params;
state_dict tensor count; checkpoint size.

MACs/FLOPs is a SECONDARY, optional indicator (not a hard acceptance gate):
auto-FLOPs tools are unreliable for graph attention + dynamic masks + HAPPO's
three policies. It is reported ONLY if all 5 methods can be counted under the
SAME rule; if reported, fix:

```
3 agents, fixed graph node count, fixed candidate edge count,
explicit self-loop inclusion, per joint decision (not per single agent)
```

Never compare one method's per-agent MACs against another's 3-agent total.
Primary acceptance metrics: params, checkpoint size, measured latency,
throughput, memory.

### 4.2 Inference latency — TWO input protocols (must not be conflated)

**A. Architecture-only latency** (network cost in isolation): fixed input
tensors / fixed graph mask, THE SAME inputs replayed for every method; no
env; measures pure network computation.

**B. End-to-end rollout throughput** (system cost in a real env): fixed env
seeds, real `obs -> model -> action -> env.step` loop; measures total system
speed. (Measuring each method only on its own generated trajectories mixes in
policy-behavior differences; the two protocols answer different questions.)

Common timing discipline (both protocols):

```
warm-up   = 200 joint decisions
measure   = 1000 joint decisions
repeats   = 10
torch.no_grad(); model.eval(); CUDA sync before/after
batch = 1 (online decision) and batch = 8 (rollout-like)
```

Report: mean / median / P95 / P99 / SD latency, joint decisions/s.

### 4.3 End-to-end env throughput

```
fixed 3D env, 8 envs, 128-step rollout, deterministic action, no backprop
```

Report: env steps/s, decision steps/s, wall-clock per 10k env steps
(disambiguates model inference vs environment cost).

### 4.4 GPU memory

```
inference peak allocated / reserved memory (both latency protocols)
training peak memory (performance profiling, NOT a training experiment)
```

Training-memory profiling is frozen as a **performance characterization run**:

```
use each method's formal frozen training config
8 envs x 128 rollout
exactly 1 PPO update
no model saving
not used for any performance (task) evaluation
no hyper-parameter adjustment
```

Record: peak allocated, peak reserved, wall-clock/update, samples/update.
For HAPPO, one update must run the full three-policy update chain (not a
single policy).

### 4.5 Communication overhead (Full and w/o RPG; most important for the paper)

Report — graph-computation edges vs physical-transmission edges SEPARATED:

```
graph candidate edges:      all directed edges the model attends over,
                            MAY include self-loops (model computes them)
physical communication edges: i != j AND comm_adj[i,j] > 0  (no self-loop:
                            env skips i==j in the comm loop, comm_adj diag = eye)
available transmitted messages: agent-to-agent messages only (exclude self-loop)
actually-used edges / messages
messages / decision step
message scalars / decision step
```

**Message-payload fact (verified in source, 2026-08-07):**
`edge_feat_dim = 17` is the GAT **edge-feature dimension** (model computation),
NOT the communication payload. The real transmitted message
(`pending_target_messages` payload) is:

```
pos (3) + vel (3) + confidence (1) = 7 continuous scalars
+ 4 integer metadata (source, generation_step, delivery_step, hop_count)
+ variable-length path
```

Therefore the protocol reports **two separate numbers**:
```
edge feature dimension            = 17   (graph attention computation)
actual transmitted payload dim    = 7 continuous scalars (+ int metadata)
```

**Semantic fact (frozen, verified in source):** the Role-Pair Gate is a
**learned static multiplicative role-pair modulation**
(`out = sum(weights * h_j * sigmoid(role_pair_gate))`). It does NOT prune
edges: all messages are still computed/transmitted; `adj` (env `comm_adj`
mask) is the only hard gate (softmax `masked_fill(-1e9)`). Therefore the
protocol **explicitly separates**:
- environment availability mask (`adj`) — real communication saving,
- attention weighting (continuous),
- role-pair modulation (multiplicative, NOT a bandwidth saver).

Communication savings may be claimed ONLY for edges truly not transmitted.

## 5. Measurement discipline

- Same hardware, process, batch, and timing code for all 5 methods.
- Fixed input distribution: fixed random seeds for input tensors (or the
  same fixed episodes); no data-dependent branch differences introduced.
- Repeats interleaved across methods (avoid time-of-day drift favoring one
  method).
- Raw timing records retained (no post-hoc trimming).
- Report 3-seed repeat variability for latency (seeds 0/1/2 short profiling)
  and 3-seed state-dict structural identity for parameter counts.

## 6. Verdict template (Full vs w/o RPG) — pre-registered expectation

Measured facts already established (2026-08-07, seed0): both have
**identical params (117,302) and identical 74 tensors** (the ablation keeps
weight-count parity; it differs only in forward semantics). Therefore the
efficiency experiment must NOT expect "removing RPG makes the model much
smaller". The realistic possibilities are:

- forward marginally faster / nearly identical;
- memory nearly identical;
- communication bandwidth theoretically unchanged (RPG is multiplicative
  modulation, not hard pruning);
- storage unchanged (parameter-matched ablation).

**Pre-registered verdict** (covers the likely outcome):

> If Full and w/o RPG have basically the same resource overhead, AND w/o RPG
> is not worse on held-out/robustness, then RPG lacks sufficient independent
> empirical value and should be downgraded to an auxiliary design; no
> communication-compression claim may be made for it.

| observed | conclusion |
| --- | --- |
| same overhead + w/o RPG not worse | downgrade to auxiliary; no comm-compression claim |
| RPG measurably cheaper (params/latency/mem/comm) | cost not justified; future simplification in Discussion |
| RPG nearly zero overhead | keep as auxiliary design; NOT a core empirical contribution |
| RPG actually lowers real comm volume (only with true transmission evidence) | discuss engineering value |

## 7. No-reselection / failure policy

- Locked checkpoints only; no reselection, no replacement, no new "selected".
- Any failure (SHA mismatch, NaN/Inf, traceback, process anomaly) stops the
  measurement group; re-run the whole affected group, never patch results.

## 8. Deliverables

```
results/paper_config_runs/formal_efficiency_v1.5_20260807/
  _operator_notes/final_efficiency_audit_v1_5/
    efficiency_audit_report.md
    efficiency_params.csv
    efficiency_latency.csv
    efficiency_throughput.csv
    efficiency_memory.csv
    efficiency_communication.csv
    efficiency_outputs_sha256.txt
    efficiency_evidence_manifest.json
```

## 9. Freeze markers

```
efficiency-protocol-freeze-v1.5.0   (this document + method/checkpoint facts)
efficiency-eval-ops-v1.5.0          (after real smoke on 1 method)
formal-efficiency-results-lock-v1.5.0 (after run + audit)
```
