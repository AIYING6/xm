# v1.5 Validation 24-Checkpoint Immutable Lock

**Tag:** `formal-ablation-validation-lock-v1.5.0`
**Created:** 2026-08-06
**Status:** IMMUTABLE (MAPPO later adds a separate 3-checkpoint lock; this tag is never rewritten)

## 1. What is locked

```text
8 methods x 3 seeds = 24 method-seed selections (one checkpoint each)
240 candidate checkpoints (SHA-audited)
validation split = base_seed 641939, 4 relay_failure-family scenarios x 50 episodes
selection policy  = v1_5_wilson (Wilson95 LCB -> success -> rec-time -> succ-time -> update)
collision gate    = 0.0
evaluation tag    = formal-ablation-eval-ops-v1.5.0 @ 9e48fe7
```

## 2. Locked selections (update per method/seed)

| method | seed0 | seed1 | seed2 |
|---|---|---|---|
| full_ea_rg | 700 | 900 | 977 |
| w_o_gate_prior | 400 | 200 | 977 |
| w_o_task_support | 900 | 300 | 600 |
| w_o_role_pair_gate | 100 | 800 | 500 |
| no_graph | 900 | 800 | 100 |
| single_graph | 700 | 500 | 900 |
| param_matched_single | 500 | 200 | 900 |
| happo | 300 | 977 | 800 |

## 3. Audit evidence (results directory, read-only from now on)

Located under
`results/paper_config_runs/formal_ablation_v1.5_validation_selector_v1.5.1_20260805/_operator_notes/final_validation_audit_v1_5/`:

- `validation_audit_report.md` — full audit, FINAL: PASS
- `selected_checkpoints_24.csv` / `selected_checkpoints_24_manifest.json`
- `candidate_sha_audit_240.csv` — 240/240 SHA matched (0 FAIL)
- `selector_recompute_audit.csv` — 24/24 recomputed selection matches (0 FAIL)
- `validation_output_sha256.txt` — raw output SHAs (frozen evidence)
- `validation_results_descriptive.csv`
- `evidence_manifest.json`

Audit header states:
`VALIDATION DATA - USED FOR CHECKPOINT SELECTION, NOT HELD-OUT TEST RESULTS`.

## 4. Results wording discipline

- Gate Prior: "消融在 validation 上出现样本充足且重复可见的弱 seed，构成较强的训练稳定性证据，仍需 held-out 复现"（非"实锤"）。
- Role-Pair Gate: "当前标准 validation 未检测到可学习 Role-Pair Gate 的额外收益"（非"无贡献"）。
- single_graph seed2 同样出现弱 seed：训练稳定性比较关注整体 seed 分布，不把单个弱 seed 全部归因于某个模块。

## 5. Post-lock

- MAPPO joins as a 9th method with its own 3-checkpoint lock
  (`mappo-baseline-v1.5` worktree), then a joint 27-checkpoint held-out
  manifest is built for a single one-shot test on a brand-new split.
