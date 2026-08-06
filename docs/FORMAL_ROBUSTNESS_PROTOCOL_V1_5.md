# FORMAL_ROBUSTNESS_PROTOCOL_V1_5

> Status: FROZEN — defines the one-shot strong-perturbation robustness test for
> the v1.5 study. Uses ONLY the 21 locked checkpoints selected for robustness;
> no reselection, no retraining, no checkpoint replacement. Runs after
> `formal-held-out-results-lock-v1.5.1` and is the deciding evidence for the
> Role-Pair Gate verdict and the green/yellow/red positioning.

---

## 1. Scope

Robustness evaluation of **7 methods x 3 train seeds = 21 locked checkpoints**
under 10 communication/topology conditions (single-factor degradation +
one joint stress), all on the SAME matched episode seeds (new deterministic
robustness base seed).

```
7 methods x 3 seeds x 10 conditions x 50 episodes = 10,500 episodes
```

## 2. Frozen evidence chain

| Asset | Lock / Tag |
| --- | --- |
| Held-out results | `formal-held-out-results-lock-v1.5.1 @ ca3bf74` |
| Held-out eval ops (selector-skip) | `held-out-eval-ops-v1.5.1` |
| MAPPO PPO/training/validation | `mappo-ppo-training-lock-v1.5.0 @ 989e338` / `mappo-validation-lock-v1.5.0 @ ec08b50` |
| 27-checkpoint joint manifest | `joint_held_out_manifest_27.csv` (SHA `0C4CA4F2…`) |
| Robustness ops | `robustness-eval-ops-v1.5.0` (this stage) |

## 3. Methods (7, subset of the 27-checkpoint manifest)

```
full_ea_rg            (Full EA-RG)
w_o_role_pair_gate    (ablation: Role-Pair Gate removed)
w_o_gate_prior        (ablation: Gate Prior removed)
w_o_task_support      (ablation: Task-Support removed)
mappo                 (strong baseline)
happo                 (strong baseline)
param_matched_single  (budget-matched strong baseline)
```

`w_o_role_pair_gate` is mandatory: the central question is whether the static
Role-Pair Gate yields value only under stronger communication/topology stress.

## 4. Perturbation matrix (frozen 10-row parameter table)

The baseline family (held-out) is `dropout=0.30, delay=2, relay failure
(agent 1, start=40, duration=80)`. The complete, unambiguous condition set is
the following 10 rows; conditions are native env parameter combinations only
(`failed_blue_agent: int` single-node failure; `node_failure_start_step`,
`node_failure_duration_steps`, `communication_dropout_prob`,
`message_delay_steps`), with NO task-semantic change.

| ID | condition key | dropout | delay | failed agent | start | duration | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R00 | `dropout030_delay2_relay_failure` | 0.30 | 2 | 1 (relay) | 40 | 80 | baseline |
| R01 | `dropout050_delay2_relay_failure` | 0.50 | 2 | 1 (relay) | 40 | 80 | mid dropout |
| R02 | `dropout070_delay2_relay_failure` | 0.70 | 2 | 1 (relay) | 40 | 80 | high dropout |
| R03 | `dropout030_delay4_relay_failure` | 0.30 | 4 | 1 (relay) | 40 | 80 | mid delay |
| R04 | `dropout030_delay8_relay_failure` | 0.30 | 8 | 1 (relay) | 40 | 80 | high delay |
| R05 | `dropout030_delay2_relay_failure_early` | 0.30 | 2 | 1 (relay) | 25 | 80 | early failure |
| R06 | `dropout030_delay2_relay_failure_delayed` | 0.30 | 2 | 1 (relay) | 55 | 80 | delayed failure |
| R07 | `dropout030_delay2_scout_failure` | 0.30 | 2 | 0 (scout) | 40 | 80 | node-type change |
| R08 | `dropout030_delay2_relay_failure_late` | 0.30 | 2 | 1 (relay) | 70 | 80 | late failure |
| R09 | `dropout070_delay8_relay_failure_early` | 0.70 | 8 | 1 (relay) | 25 | 80 | joint stress |

Single-factor structure: R00 vs R01/R02 (dropout escalation at delay=2);
R00 vs R03/R04 (delay escalation at dropout=0.30); R00 vs R05-R08 (topology
timing / node type at dropout=0.30, delay=2); R09 is the one pre-registered
joint stress.

New keys added ONLY to the robustness scenario dictionary (evaluation-config
extension; frozen env/training untouched): `dropout050_delay2_relay_failure`,
`dropout070_delay2_relay_failure`, `dropout030_delay4_relay_failure`,
`dropout030_delay8_relay_failure`, `dropout070_delay8_relay_failure_early`.

## 5. Split (deterministic, no cherry-picking)

```
anchor = SHA256_hex(held_out_split_manifest.csv) + "formal-robustness-v1.5"
h = SHA256(anchor)                                   # hex, uppercase
candidate = (int(h[0:8], 16) % 900000) + 100000
while candidate in {888000, 120000, 641939, 745669}:
    candidate = ((candidate + 1) % 900000) + 100000
ROBUSTNESS BASE SEED = 946804
```

Computed values:

```
held_out_split_manifest.csv SHA256 = 17433806FE9FE76136415B5F8CA70AF461A7C5EB1D8B40C5722A2862F6E56FEB
derivation hash                     = 35F67EF4BD3ED802EA442A8ED5A8651605874604BBC3F926256FF085993DE308
ROBUSTNESS BASE SEED                = 946804
```

`946804` has never been used for training, BC, smoke, `888000`, `120000`,
`641939`, `745669`, or any prior validation/test. Episode seeds:
`episode_seed = base_seed + episode_index` (matched across all 21 checkpoints
and all 10 conditions).

## 6. Inputs: 21 locked checkpoints

```
results/paper_config_runs/formal_held_out_v1_5_10800_20260807/
  _operator_notes/final_held_out_audit_v1_5/
    robustness_checkpoint_manifest.csv   (21 rows: method, seed, update,
                                          checkpoint_abs, sha256)
```

- Every checkpoint SHA must match the 27-checkpoint joint manifest entry
  (input SHA audit before running).
- No reselection, no replacement, no new "selected checkpoint".

## 7. Evaluation settings (frozen)

| Setting | Value |
| --- | --- |
| split | `test` |
| base_seed | `946804` |
| conditions | the 10 above |
| episodes per condition | `50` |
| eval batch size | `1` |
| deterministic action | argmax |
| strict target sensing / agent target info bottleneck | enabled |
| device | `cuda` |
| execution | serial, single Scheduled Task |
| selection | NONE (robustness evaluates locked checkpoints only) |

Execution: one call per (method, seed, condition) via the frozen
`evaluate_3d_checkpoint_sweep.py` entrypoint with `--split test` and
`--checkpoint-updates <locked update>` (split=test skips the selector,
per `held-out-eval-ops-v1.5.1`). Output per group:
`<root>/robustness_v1.5/<method>/seed<seed>/<condition>/`.

## 8. Statistics (identical aggregation rules as the held-out audit)

Per method-seed-condition report: success count/rate, collision count/rate,
exposed count (raw), recovered/exposed, Wilson 95% lower bound, pooled
time_to_success, pooled time_to_recovery (pooled over all valid episodes,
NOT means of scenario means; SD = sample SD ddof=1 over 3 seeds; retain all 3
seed values + worst seed).

### 8.1 Sample-stability rule (pre-registered)

Each method-seed-condition cell has exactly 50 episodes. Frozen rules:

- Report the raw `exposed` count and the raw `recovered` count; never a rate
  without its denominator.
- `recovery_given_exposure = recovered / exposed`, `Wilson95 = wilson_lower_95(exposed, recovered)`.
- If `exposed < 10`, mark the cell `estimate_unstable=True`.
- Cells marked `estimate_unstable` are reported descriptively but are NOT used
  for any Role-Pair Gate deterministic conclusion (section 9).
- No condition is expanded after seeing results; sample size per cell is
  fixed at 50 episodes for all cells.

### 8.2 Degradation (primary reporting object)

```
Delta_success   = stress_success - baseline_success
Delta_recovery  = stress_recovery - baseline_recovery
Delta_t_success = stress_t_success - baseline_t_success
Delta_t_recovery= stress_t_recovery - baseline_t_recovery
```

Also report per-method degradation slope across dropout/delay escalation and
the joint-stress gap (R09 minus R00).

## 9. Role-Pair Gate pre-registered verdict

### 9.1 Retain as a core structure

Only if Full vs `w_o_role_pair_gate` shows, across MULTIPLE strong
communication/topology conditions, a consistent pattern of:
- higher recovery,
- lower worst-seed degradation,
- shorter recovery time,
- advantage widening as perturbation strengthens.

### 9.2 Downgrade to auxiliary structure

If the two remain basically equal, or the gate-free version is slightly better:
> Role-Pair Gate shows no stable independent benefit under standard or strong
> perturbation metrics; it is a light role-prior modulation, not a core
> empirical contribution.

### 9.3 Remove / simplify

If `w_o_role_pair_gate` is stably better and more efficient on most
conditions, adopt the simplified model. No selective reporting of conditions
to keep the module.

## 10. No-reselection / failure policy

- No reselection on robustness data; inputs fixed (21 checkpoints).
- A failed task (non-zero exit, incomplete rows, SHA mismatch, duplicate
  instance, missing condition, NaN/Inf, traceback) stops the process; do not
  hand-pick results; re-run the affected whole attempt from frozen inputs.
- Robustness results never feed back into checkpoint selection.

## 11. Freeze marker

This document + the robustness checkpoint manifest + the robustness split
manifest are committed and tagged before any robustness evaluation runs.

Tag: `robustness-eval-ops-v1.5.0`
