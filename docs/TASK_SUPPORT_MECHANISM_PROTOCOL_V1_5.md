# Task-Support Mechanism Protocol v1.5

- status: **FROZEN** (freeze tag: `task-support-mechanism-protocol-freeze-v1.5.0`)
- frozen at: 2026-08-07
- scope: mechanism analysis ONLY. Does NOT re-open held-out / robustness / efficiency /
  gate-prior locks. Read-only over locked checkpoints; no training, no hyper-parameter
  changes, no metric changes after results are inspected.
- All comparison objects, windows, extraction sizes, and interpretation boundaries are
  pre-registered. Any change requires a new protocol revision.

## 0. Objective and boundary

Q: does the task-support relation help information/task-dependency re-organization after a
node failure, explaining Full's shorter recovery time?

- This is NOT a re-evaluation of performance. It explains the locked held-out effect
  (Full recovery ~0.971 / t_recovery ~10.8 vs w/o Task-Support recovery ~0.892 /
  t_recovery ~16.1) — the mechanism question, not the performance question.
- Concept boundary (frozen, must be respected in the paper):
  - w/o Task-Support = model-layer task-support relation output set to zero
    (`disable_task_support=True`, `output = zeros_like`) AND env-side `relation_adj[2]=0`
    (`active_support=0.0`). It does NOT delete the environment task, nor does it remove
    all graph communication (perception/communication channels remain).
  - Claimable: "Task-Support relation contributes to task-dependent relational
    reasoning / coordination."
  - NOT claimable: "without Task-Support there is no task graph" or "Task-Support
    controls whether real messages are sent" (comm_adj is independent).

## 1. Source-of-truth fact table (verified 2026-08-07, locked)

| item | fact |
|---|---|
| tensor | `relation_adj[:, 2, :, :]` = task-support channel, shape [B, 3, N, N], N=4 (3 blue + 1 target), A[receiver, sender] |
| activation | `_active_support_edge(src,dst)`: role-compatible AND `comm_adj[dst,src]>0.5` AND (sender SCOUT/RELAY has target info OR sender ATTACKER/INTERCEPTOR has local attack window) |
| env comment | "task-support edges gate delivered communication messages; they are not an independent information channel" |
| model role | independent GAT channel per relation (layer1/layer2 x 3); `relation_adj` masks attention scores (`masked_fill(adj<=0, -1e9)`); also folded into union adj |
| normalization | attention weights = softmax over senders per receiver; no extra task-support normalization |
| w/o variant | env `active_support=0.0` AND model output `zeros_like` (attention still computed); perception/comm channels unchanged |
| extractability | `relation_adj[2]`, `comm_adj`, failure/recovery/success events directly recorded from eval rollout of locked checkpoints; no forward hooks required |

## 2. Locked comparison objects

| method | checkpoint source | seeds |
|---|---|---|
| Full | `ri_gmappo_uav/results/.../ea_rg_mappo_s_gate_prior/ppo_seed{S}_1m/actor_critic_update_0700.pt` | 0,1,2 |
| w/o Task-Support | `ri_gmappo_uav_ablation_v1.5/results/.../w_o_task_support/ppo_seed{S}_1m/actor_critic_update_0100.pt` | 0,1,2 |

- Eval entry: `scripts/evaluate_ri_gmappo_3d.build_agent` with locked config mirrors
  (same as the locked held-out / robustness entrypoints), deterministic seeds,
  `graph_relation_ablation` = "none" (Full) / "no_task_support" (w/o).
- Scenarios: `dropout030_delay2_relay_failure` and `dropout030_delay2_relay_failure_early`
  (locked held-out scenarios). Per (method, seed, scenario): 100 episodes.
  Episode initial seeds derived deterministically from the locked held-out base seed
  745669 (same derivation rule as the held-out split).

## 3. Block 1 — performance effect (cited, NOT re-run)

Reported from the LOCKED held-out audit (formal_held_out_v1_5_10800_20260807) and locked
robustness audit: for Full vs w/o Task-Support — success, recovery, t_success, t_recovery,
worst-seed, and 3-seed mean ± SD (ddof=1). No new performance experiments.

## 4. Block 2 — task-support relation dynamics around failure

Per episode, record per-step (0..max): `relation_adj[2]` (12 blue-blue pairs),
`comm_adj` (blue-blue), failure step `f` (node failure onset), recovery step `r`
(first post-failure chain recovered, else inf), success flag, episode length.

Pre-registered windows (relative to events, frozen):
- pre-failure: steps `[f-20, f-1]`
- early post-failure: steps `[f, f+20]`
- pre-recovery: steps `[r-20, r-1]` (episodes with finite r only)
- post-recovery: steps `[r, r+20]` (episodes with finite r only)

Pre-registered statistics, per (method, seed, scenario), pooled over episodes:
- task-support relation strength: mean of `relation_adj[2]` over blue-blue pairs per
  step, averaged over window; non-zero-edge fraction (active edges / 12).
- role-pair distribution: non-zero fraction grouped by (receiver_role, sender_role)
  within each window.
- task-support/comm co-occurrence: fraction of active task-support edges whose comm edge
  is present (by construction ~1 for Full; report as sanity check).
- cross-seed consistency: per (method, scenario, window): SD across seeds of the
  mean strength; also per-seed mean strength list.

The primary between-method comparison is Full vs w/o Task-Support on the same windows,
same scenario, same seed. NOTE: w/o Task-Support has relation_adj[2]=0 by construction,
so its window strength is exactly 0; the meaningful contrasts are (a) Full relation
strength by window (does it rise after failure / before recovery), and (b) Full vs w/o
event timing (t_recovery) already covered by Block 1. Do not treat relation strength 0
in w/o as a "surprising" result — it is the ablation definition.

## 5. Block 3 — typical episode cases (frozen selection rule)

Three classes, selected by fixed rules (no cherry-picking):
- C1: Full and w/o both succeed, but Full recovery faster (minimal Full t_recovery delta
  >= 2 steps among candidates).
- C2: Full succeeds while w/o fails.
- C3: both fail.
Selection: within each class, pick the episode with the smallest episode index
(lexicographic: scenario order as listed in Section 2, then episode index). For C1, from
candidates with `Full t_recovery < w/o t_recovery`; for C2, from `Full success and
!w/o success`; for C3, from `!Full success and !w/o success`. Use Full seed0 / scenario
`dropout030_delay2_relay_failure` as primary; if no candidate exists in that cell, move in
fixed order (scenario early, then seeds 1,2). Each case figure shows: failure step,
task-support active edges (relation_adj[2]) over time, recovery step, and episode success.

## 6. Pre-registered verdict

- SUPPORT: Full shows a stable task-support re-organization after failure (window strength
  pattern: rise in early post-failure or pre-recovery vs pre-failure) AND this is in the
  same direction as shorter t_recovery and better worst-seed (Block 1).
- EMPIRICAL SUPPORT ONLY: performance ablation is clear, but the internal relation
  trajectory shows no clear interpretable pattern.
- INCONCLUSIVE: internal metrics point in inconsistent directions or are driven by a
  handful of episodes.
Report honestly; no forced interpretation.

## 7. Deliverables

- `docs/TASK_SUPPORT_MECHANISM_PROTOCOL_V1_5.md` (this file)
- `docs/task_support_v1_5_assets/`
  - `task_support_episode_manifest.csv` (per episode: method, seed, scenario, episode idx,
    failure step, recovery step, success, steps)
  - `task_support_relation_trajectory.csv` (per episode per window: mean strength,
    non-zero fraction, role-pair fractions)
  - `task_support_window_summary.csv` (per method/seed/scenario/window: pooled stats)
  - `task_support_seed_consistency.csv` (per method/scenario/window: cross-seed SD + per-seed values)
  - `task_support_case_manifest.csv` (selected cases: class, episode refs, event steps, success)
  - `task_support_mechanism_report.md`
  - figures: `fig_ts_window_strength.png` (Full window means by method/scenario),
    `fig_ts_case_examples.png` (case trajectories, up to 3 panels)
- All CSVs carry schema + provenance (method, seed, scenario, episode, event steps,
  metric, value, source lock tags).

## 8. Determinism and scope guard

- All episodes run with the locked held-out base-seed derivation; no new randomness.
- Exactly 2 scenarios x 2 methods x 3 seeds x 100 episodes = 1200 episodes total.
- If a scenario/seed checkpoint fails to load, that cell is flagged and reported;
  no silent substitution.
