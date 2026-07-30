# Current Project State

Last updated: 2026-07-30

## Frozen Baseline (post-sixth-freeze-v1)

The formal 1M PPO study now runs against a frozen source baseline:

- **current tag**: `formal-post-sixth-freeze-v1.3` (current authority; SHA `bdcb600`)
- **historical tags** (retained, NOT moved):
  - `formal-post-sixth-freeze-v1` (SHA `8b13e26`): first frozen baseline; no formal artifacts produced; retained for source audit.
  - `formal-post-sixth-freeze-v1.1` (SHA `e30359b`): added freeze gates, coverage block, bc_manifest, BC verification, BC_INVALID classification, seed-passing fix; no formal artifacts produced; retained for source audit.
  - `formal-post-sixth-freeze-v1.2` (SHA `446aad7`): added BOM encoding fix for bc_manifest.json writer/reader; retained for source audit.
- **branch**: `main`
- **python**: 3.8.20; **torch**: 2.4.1+cu124; **cuda**: 12.4; **host**: AIYING
- **P0 actor/info-boundary fix** (in `envs/uav_intercept_3d_env.py`):
  - target prior in shared graph is zero-masked (no public prior leak);
  - under strict target sensing + agent-target-info-bottleneck, actor obs `rel`/`red_vel` are zeroed when target not visible;
  - union-graph hidden `attack` edge removed (no fourth channel).
- **Resume authority**: training-state checkpoint `update` is authoritative; `train_log.csv` is audit-only. Gate: `FRESH / READY / COMPLETE / BLOCKED` with two-stage check.
- **Enforced launch gates** (`scripts/formal_freeze_gate.ps1`, used by both launchers): abort with exit `2` unless:
  - `HEAD` == tag commit,
  - `git diff --quiet` and `git diff --cached --quiet` (no tracked/staged changes),
  - **all untracked files** are inside `results/paper_config_runs/formal_budget_post_sixth_freeze_v1/**` (no stray `.py`, `.ps1`, `.txt` outside the formal root).
- **BC integrity** (`scripts/verify_bc_checkpoint.py`): BC init must be loadable on CPU, carry a non-empty state dict, match the method architecture exactly, and pass full manifest validation (method, seed, freeze_tag, freeze_commit, checkpoint name, graph_encoder, hidden_dim, role_gate_prior_strength, checkpoint_sha256). Existence alone no longer qualifies as `FRESH`; an unusable BC reports `BC_INVALID`.
- **Batch safety**: the BC launcher supports `-ResumeValid` for safe interruption recovery; `--skip-bc-architecture` in the progress checker forces `BC_UNVERIFIED` and non-zero exit (diagnostic only).
- **Evidence separation**:
  - `results/paper_config_runs/formal_budget_pre_sixth_freeze_development/` = pre-freeze 20-29 update runs (DEVELOPMENT EVIDENCE ONLY).
  - `results/paper_config_runs/formal_budget_post_sixth_freeze/` = retired pre-P0-fix root (DEVELOPMENT/PRE-FREEZE EVIDENCE ONLY; its BC `15/15` and PPO update-20 records are void).
  - `results/paper_config_runs/formal_budget_post_sixth_freeze_v1_preflight/` = pre-tag BC + 0→2 runs (PREFLIGHT EVIDENCE ONLY).
  - `results/paper_config_runs/formal_budget_post_sixth_freeze_v1/` = the only formal root; currently `BC = 0/15`, `PPO = 0/15`, formal training not started.

## Current Milestone

Execute the final single-paper Q1 plan recorded in `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

The user target is one paper, Q1 attempt with Q2 fallback. The 3DOF 3v1 strict-sensing relay-failure evidence remains the statistical foundation, but the final version now also requires controlled Q1-supporting supplements: HAPPO as a priority external baseline attempt, a small 4v2/5v2 rule-red extension, and a small LAG/JSBSim replay or feasibility validation.

Immediate execution is P0 scientific-validity hardening:

- replace magic-number observation slices with a documented schema;
- verify/correct `no_role_identity`;
- remove global attack-chain progress from actor graph inputs while keeping it available to critic/evaluation;
- add actor information-boundary tests;
- mark any violating pre-hardening results as development evidence only.

Current algorithm-development status:

- Chain auxiliary learning has been implemented and tested in 100-update
  development runs, but both the direct auxiliary version and the warmup version
  hurt short-run policy learning. It is not promoted to formal 1M training.
- Role-graph diagnostics show that the original multi-relation structure is
  active, but role-pair gates remain nearly neutral.
- A `role_gate_prior_strength = 0.4` candidate was implemented and verified by
  smoke tests, but its 100-update development run under strict sensing,
  dropout 0.30, delay 2, and relay failure was worse than original EA-RG-MAPPO
  in online 5-episode evaluation (`0.0000` mean final success vs `0.3333` for
  original EA). A follow-up fixed validation sweep with 30 matched episodes per
  checkpoint found both variants weak (`0.0778` selected success for original
  EA vs `0.0889` for gate-prior EA), so the candidate is recorded as
  non-promotable rather than as a robust improvement.
- The current main method remains the original EA-RG-MAPPO. The next work should
  focus on fixed validation checkpoint sweeps, PPO stability, reward/scale
  inspection, and fair retraining rather than adding another unvalidated module.
- Early relay-failure validation under
  `dropout030_delay2_relay_failure_early` is in progress and documented in
  `docs/dropout030_delay2_early_validation_progress.md` and
  `docs/dropout030_delay2_early_validation_summary.md`. The regular
  MAPPO-family sweep is complete: EA-RG-MAPPO beats no-graph (`0.4733` vs
  `0.3667`) but does not beat Single-Graph (`0.5267`). Therefore the early
  scenario must not be promoted to final held-out testing as the main result.
  The next priority is diagnosing EA seed instability versus Single-Graph, not
  searching for another hand-picked scenario.
- A first mechanism diagnostic for the completed early validation is recorded in
  `docs/early_validation_mechanism_diagnostics.md`. EA improves over no-graph
  on recovery, tracking, connectivity, and message age, but Single-Graph still
  has better tracking during failure and shorter recovery time. The current
  bottleneck is EA seed stability and relation-routing effectiveness.
- A selected-checkpoint mechanism ablation on the early stress scenario is
  recorded in `docs/relation_bottleneck_dev_update.md`. Removing task-support
  at evaluation time barely changes EA (`0.4733` to `0.4667` success), and
  disabling role-pair gates slightly improves it (`0.4867` success). Therefore
  task-support and role-pair gate cannot currently be claimed as strong causal
  mechanisms.
- Added a guarded relation-bottleneck candidate:
  `multi_relation_global_residual_weight`. Default remains `1.0` for backward
  compatibility; `configs/paper/ea_rg_mappo_relation_bottleneck.yaml` sets it
  to `0.0` to prevent the union graph path from bypassing relation-specific
  channels. A BC+20-update smoke and a stronger seed-0 BC+100-update
  development run both completed, but online success stayed `0.0` throughout
  the 100-update PPO run. Latest diagnostics confirmed the global channel was
  disabled, but task-support/perception attention remained weak and role-pair
  gates were still near neutral. Do not scale this candidate to 1M/2M in its
  current form.
- BC diagnostics under the same early stress setting found that geometric
  oracle policies remain highly reachable (`direct` and `offset` success
  `1.000`), but balanced BC produces weak learned policies. Switching direct BC
  to `--no-balanced-loss` improved imitation accuracy from `0.2970` to `0.7253`
  and BC-only success from `0.0000` to `0.3000`. This is a protocol improvement
  candidate, not a method contribution. If used formally, it must be applied
  identically to EA, Single-Graph, MAPPO, and HAPPO-compatible BC baselines.
- A fair seed-0 no-balanced BC development run is documented in
  `docs/no_balanced_bc_seed0_dev_summary.md`. Under the same strict early-stress
  protocol, BC-only success was `0.3000` for EA, `0.3000` for Single-Graph, and
  `0.4000` for MAPPO. After 100-update PPO with checkpoint-subset validation,
  the best observed checkpoints were EA update 40 (`0.4400` success),
  Single-Graph update 80 (`0.4000`), and MAPPO update 70 (`0.3400`). This is a
  useful training-protocol improvement, but only seed 0 and a subset of
  checkpoints were evaluated. EA mechanism ablation at update 40 still showed
  no degradation when task-support or role-pair gate was disabled, so those
  mechanisms remain unproven.
- The no-balanced BC check has been extended to full seed 0/1/2 100-update PPO
  validation for EA-RG-MAPPO, Single-Graph, and MAPPO/no-graph. The fixed
  50-episode validation summary is documented in
  `docs/no_balanced_bc_seed0_2_validation_summary.md`. Selected-checkpoint mean
  success/recovery is EA-RG-MAPPO `0.3733`, Single-Graph `0.3533`, and
  MAPPO/no-graph `0.3400`. This confirms no-balanced BC is a useful short-run
  initialization protocol, but the EA margin is too small for a paper-level
  graph-mechanism claim. Do not scale this branch directly to 1M/2M until the
  role-conditioned communication mechanism or task dependence is strengthened.
- A small strict delayed-recovery checkpoint diagnostic is documented in
  `docs/delayed_recovery_candidate_sweep_small_summary.md`. The checkpoint
  sweep tool now supports `--checkpoint-updates` and records the update filter
  plus `selection_success_weight` in its report. Under fresh-message stress
  (`max_target_message_age_steps=20`, dropout `0.30`, delay `2`, relay failure
  at step `40`), `delayed_recovery_min_step=80` produced only one non-zero EA
  candidate (`seed1/update3800`, delayed recovery `0.200`) and zero delayed
  recovery for Single-Graph and MAPPO/no-graph in the sampled checkpoints.
  Lower thresholds reintroduced fast geometric-intercept confounds, so this
  branch remains development evidence. The next experiment-design step is to
  freeze a small early/standard/delayed/late relay-failure scenario suite and
  retrain all methods under one fair protocol, not to keep searching for a
  single favorable stress condition.

P0 first pass completed on 2026-07-24 and is documented in `docs/p0_scientific_validity_hardening_update.md`:

- exported `OBS3D_ROLE_IDENTITY_SLICE = slice(24, 28)` and `NODE3D_ROLE_IDENTITY_SLICE = slice(11, 16)`;
- `no_role_identity` now uses the exported 3DOF schema instead of `slice(22, 26)`;
- global normalized `attack_hold` was removed from actor graph edge features;
- `EDGE3D_FEAT_DIM` changed from 18 to 17;
- Gate 1 communication/information-boundary tests passed: `24 passed`;
- 3DOF environment smoke and one-update multi-relation training smoke passed.

The follow-up P0 pass added full `OBS3D_FIELD_NAMES` coverage and direct actor-logit invariance tests for global `attack_hold` and unreachable target-cache changes.

Because the 3DOF actor graph feature dimension changed, pre-hardening 3DOF checkpoints and old no-role-identity results are development evidence only.

P1 training-protocol standardization has started and is documented in `docs/p1_training_protocol_standardization.md`:

- created JSON-compatible YAML configs under `configs/paper/`;
- defined `configs/paper/main_gate1.yaml` with environment-step budget, validation/test split, metrics, and relay-failure scenario;
- added method configs for MAPPO, Single-Graph, EA-RG-MAPPO, Parameter-Matched Single, HAPPO, IPPO, and key ablations;
- HAPPO is now recorded as a priority external strong baseline attempt for Q1 credibility;
- added `scripts/audit_paper_configs.py`;
- config audit passed for 10 configs, with the 1M-step approximation equal to 1,000,192 environment steps.
- added `scripts/generate_paper_commands.py`;
- generated the first smoke command manifest in `results/paper_command_manifest.csv` and `docs/paper_command_manifest.md`;
- config-driven one-update smoke training passed for `mappo`, `single_graph`, and `ea_rg_mappo` under `results/paper_config_runs/smoke/`;
- `happo` initially entered the command manifest as `pending_implementation`, then advanced after HAPPO training and checkpoint-sweep smoke passed;
- `scripts/generate_paper_commands.py --mode dev_1m --methods mappo single_graph ea_rg_mappo happo --seeds 0 1 2 --include-sweeps` generated 20 commands: 12 training commands, 4 validation sweeps, and 4 test sweeps;
- generated test-sweep commands explicitly depend on validation `selected_checkpoints.csv`;
- added `scripts/train_happo_baseline.py`;
- HAPPO no-graph external-baseline training smoke passed with separate per-agent actor/critic modules and sequential PPO updates;
- HAPPO command generation now emits training, validation-sweep, and test-sweep commands;
- HAPPO validation/test checkpoint-sweep smoke passed and both outputs passed the checkpoint-selection schema audit;
- HAPPO smoke details are documented in `docs/happo_baseline_smoke.md`;
- added `scripts/write_paper_run_provenance.py`;
- added `configs/paper/checkpoint_selection_schema.yaml` and `scripts/audit_checkpoint_selection_schema.py`;
- checkpoint-selection schema audit passed with 27 summary columns, 22 selection columns, and 58 episode columns;
- generated `results/paper_run_provenance.csv` and `docs/paper_run_provenance.md` with hashes for 26 critical config/code files.
- added `scripts/run_paper_manifest.py`, `scripts/audit_paper_manifest.py`, and `docs/paper_manifest_runner.md` so long paper experiments can be checked and launched from the audited command manifest while preserving per-row logs and run status.
- manifest runner smoke execution passed for MAPPO seed 0 and wrote `results/paper_manifest_run_status.csv` plus stdout/stderr logs.
- dev_1m command manifest audit passed: 20 rows total, including 12 training rows and validation/test checkpoint sweeps for MAPPO, Single-Graph, EA-RG-MAPPO, and HAPPO over seeds 0, 1, and 2.
- added `probe_20` command-generation mode for launch-readiness and runtime estimation; probe outputs are engineering diagnostics only, not paper evidence.
- `probe_20` launch-readiness training passed for MAPPO/no-graph, Single-Graph, EA-RG-MAPPO, and HAPPO seed 0. The HAPPO parser was fixed to accept shared fairness/protocol arguments before it passed.
- wrote `docs/dev1m_launch_plan.md`: first real development-budget stage starts with seed 0 for EA-RG-MAPPO, Single-Graph, MAPPO/no-graph, and HAPPO, followed by validation-only checkpoint sweeps before any test sweep.
- added `scripts/audit_training_outputs.py` to verify train logs and checkpoints before validation sweeps.
- `scripts/audit_training_outputs.py --mode probe_20 --methods mappo single_graph ea_rg_mappo happo --seeds 0` passed, verifying the output-audit path against real probe outputs.
- added background job helpers `scripts/start_paper_manifest_job.py` and `scripts/check_paper_manifest_jobs.py` for hour-level dev_1m training runs.
- added `scripts/check_training_progress.py` to monitor long training by `train_log.csv` progress when Windows PID checks are unreliable.
- added `scripts/summarize_training_logs.py` to summarize train/eval columns and flag non-finite values before validation sweeps.
- added `scripts/gate_validation_readiness.py` so validation sweeps are gated by completed training outputs and log sanity checks.
- added `scripts/run_manifest_training_chunk.py` for foreground, resumable training chunks when detached background jobs are not reliable in the Codex sandbox.
- added full training-state checkpoint support for chunked MAPPO/Single-Graph/EA-RG-MAPPO and HAPPO training. Weight-only `actor_critic_latest.pt` and `happo_latest.pt` remain available for existing evaluation scripts, while `actor_critic_training_state_latest.pt` and `happo_training_state_latest.pt` preserve optimizer state for subsequent resume chunks. Resume-smoke verification passed for both RI-GMAPPO and HAPPO after the 1700-update chunks.
- The next fair validation/test protocol now uses a frozen four-scenario relay-failure suite from `configs/paper/main_gate1.yaml`: `dropout030_delay2_relay_failure_early`, `dropout030_delay2_relay_failure`, `dropout030_delay2_relay_failure_delayed`, and `dropout030_delay2_relay_failure_late`. `scripts/generate_paper_commands.py` now reads validation/test scenario lists from config instead of hard-coding `relay_failure`. `scripts/evaluate_3d_checkpoint_sweep.py` and `scripts/evaluate_happo_checkpoint_sweep.py` now support `--selection-group suite`, so multi-scenario validation selects one checkpoint per method/seed by suite-average score instead of selecting a different checkpoint per scenario. `scripts/audit_paper_manifest.py` verifies both the configured scenario lists and suite-selection flag. Config audit, command generation, Python compile, manifest audit, and a multi-scenario suite-selection smoke passed after the change.
- HAPPO evaluation compatibility was tightened for the frozen suite protocol: `scripts/evaluate_happo_3d.py` now uses the same matching-tensor checkpoint loader as RI-GMAPPO so older HAPPO checkpoints remain evaluable after auxiliary-head code changes; `scripts/evaluate_happo_checkpoint_sweep.py` now supports `--checkpoint-updates`, `--selection-group`, and `--selection-success-weight`. A HAPPO four-scenario suite-selection smoke over updates `3800` and `3907` passed and produced a single `scenario_suite` selected checkpoint row.
- A low-cost frozen-suite candidate sweep is documented in `docs/frozen_suite_candidate_sweep_summary.md`. It used the four-scenario suite, `--selection-group suite`, 3 train seeds, candidate checkpoints around online-monitoring peaks, and 5 validation episodes per scenario/checkpoint. Safety-gated broad recovery selection gives EA-RG-MAPPO-S recovery/delayed/success `0.333/0.083/0.433`, Single-Graph `0.350/0.083/0.500`, MAPPO/no-graph `0.133/0.000/0.167`, and HAPPO `0.000/0.000/0.000`. Safety-gated strict delayed-recovery selection gives EA `0.217` delayed recovery, Single-Graph `0.100`, MAPPO/no-graph `0.000`, and HAPPO `0.000`. This means EA has the clearest delayed-recovery mechanism signal, while Single-Graph remains slightly better on broad success. This is development evidence only. Do not run held-out test yet; next priority is improving EA training stability and deciding whether formal checkpoint selection should prioritize delayed recovery.
- The first training-stability implementation pass is documented in `docs/training_stability_implementation_update.md`. RI-GMAPPO training now supports fixed online monitor seeds (`eval_base_seed`), PPO diagnostics (`approx_kl`, `clip_fraction`, `grad_norm`, `explained_variance`, `ppo_epochs_ran`, `critic_warmup_active`), critic-only warm-up, actor/critic learning-rate parameter groups, `clip_coef`, `ppo_epochs`, `target_kl`, and `max_grad_norm` CLI controls. A one-update 3D EA-RG-MAPPO-S smoke with critic warm-up and conservative PPO settings passed. The next recommended run is EA-only 300 updates over seeds 0/1/2 with fixed monitor episodes before applying the same stable protocol fairly to Single-Graph, MAPPO/no-graph, and HAPPO.
- An EA-only stability development run through 120 updates is documented in `docs/training_stability_dev120_summary.md`. A first seed-0 attempt was invalid because it used `hidden_dim=128` with `hidden_dim=64` BC checkpoints; the valid runs use `--hidden-dim 64` and load all 74 tensors exactly. Under critic warm-up and conservative PPO, fixed-monitor success is stable for seed 0 (`0.3`-`0.4`) and seed 1 (`0.3`), while seed 2 remains unsolved on the fixed monitor. Four-scenario suite evaluation over updates 60/80/100/120 gives mean recovery/success/collision `0.333/0.667/0.000`, but strict delayed recovery remains `0.000`. This means the stability controls improve broad success and seed consistency, but do not yet solve the delayed/late recovery mechanism. `scripts/evaluate_3d_checkpoint_sweep.py` now supports `--run-dir-template` for evaluating nonstandard experiment directory layouts.
- The EA-only stability development run was extended to 180 updates and recorded in `docs/training_stability_dev180_and_random_failure_summary.md`. Fixed step-40 failure training peaks around update `160` on the four-scenario validation suite: success/recovery/delayed-recovery/collision `0.600/0.300/0.000/0.000`; update `180` degrades to `0.400/0.200/0.000/0.000`. A seed-0 random failure-start pilot over `[25,100]` reaches only success/recovery/delayed-recovery/collision `0.400/0.200/0.000/0.000`, so randomizing failure timing alone is not sufficient. The next development step is a targeted post-loss chain re-closure training objective or staged failure-time curriculum, not simply longer runs under the same objective.
- Post-loss reclosure training controls and recovery-oriented BC support are implemented and documented in `docs/post_loss_reclosure_recovery_bc_seed0_summary.md`. The key route is balanced `offset` geometric recovery BC followed by conservative PPO with `min_success_step=80` and a post-loss reclosure reward. In seed 0, the selected update-40 checkpoint reaches four-scenario suite success/recovery/after-loss/delayed-recovery/collision `0.625/0.675/0.675/0.450/0.000`; delayed and late scenarios both reach `0.700` delayed recovery with zero collision. This is the first strong delayed/late recovery development signal. It is not formal paper evidence yet; the next step is matched expansion to EA seeds 1/2 and then Single-Graph under the identical recovery-oriented protocol.
- The recovery-oriented route has been upgraded into a uniform three-seed EA-RG-MAPPO-S development protocol and recorded in `docs/post_loss_reclosure_strong_protocol_3seed_summary.md`. The protocol uses strong balanced offset BC (`120` episodes, `20` epochs), `min_success_step=80`, post-loss reclosure reward `0.5`, and safety PPO with proximity distance `2500` and penalty `0.5`. Selected validation checkpoints over the four-scenario suite give mean success/recovery/after-loss/delayed-recovery/collision `0.625/0.717/0.717/0.342/0.000`. Delayed and late scenarios average delayed recovery `0.633` and `0.667`, both with zero collision. This clears the development gate for matched baseline expansion; the next implementation step is to run Single-Graph MAPPO under the identical protocol before any formal test evaluation.
- Single-Graph MAPPO has now been run under the same strong recovery protocol and summarized in `docs/single_graph_strong_protocol_comparison_summary.md`. Under unconstrained delayed-recovery selection, Single-Graph reaches mean success/recovery/delayed/collision `0.675/0.783/0.358/0.008`, but seed 0 has nonzero collision. A zero-collision diagnostic gives EA `0.625/0.717/0.342/0.000` versus Single `0.600/0.783/0.333/0.000`. This means Single-Graph is a strong baseline; current evidence supports a nuanced safety/delayed-recovery tradeoff rather than a broad EA dominance claim. The next step is MAPPO/no-graph under the same protocol to establish the value of graph structure itself.
- MAPPO/no-graph has now been run under the same strong recovery protocol and summarized in `docs/no_graph_strong_protocol_comparison_summary.md`. Under zero-collision selection, EA/Single/no-graph reach success `0.625/0.600/0.367`, recovery `0.717/0.783/0.492`, delayed recovery `0.342/0.333/0.308`, and timeout `0.375/0.400/0.633`. This supports a graph-structure claim over no-graph MAPPO, while preserving the earlier conclusion that EA versus Single is a close safety/recovery tradeoff rather than a one-sided dominance result. The next baseline to run is HAPPO under the same recovery protocol if schedule allows.
- launched dev_1m seed-0 training jobs for EA-RG-MAPPO, Single-Graph MAPPO, MAPPO/no-graph, and HAPPO through `scripts/start_paper_manifest_job.py`. Progress should be monitored with `scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0`.
- current dev_1m seed-0 progress snapshot is recorded in `docs/dev1m_seed0_progress.md`; all four seed-0 jobs are active and should finish on an hours-level timescale if current throughput holds.
- detached background jobs stopped updating before completion in the Codex sandbox, so seed-0 dev_1m training has moved to foreground resumable chunks via `scripts/run_manifest_training_chunk.py`.
- current chunked seed-0 progress: EA-RG-MAPPO 3907 updates, Single-Graph 3907, MAPPO/no-graph 3907, corrected HAPPO 3907 updates. The older pre-correction HAPPO-style run reached 2300 updates but is no longer eligible for formal paper comparison; all four seed-0 methods completed the dev-1M training budget.
- first seed-0 1000-update audit passed and is recorded in `docs/dev1m_seed0_1000update_audit.md`; this is a development-training checkpoint, not formal paper evidence.
- seed-0 1200-update output audit passed and wrote `results/dev1m_seed0_1200update_summary.csv`.
- seed-0 1300-update output audit passed and wrote `results/dev1m_seed0_1300update_summary.csv`.
- seed-0 1400-update output audit passed and wrote `results/dev1m_seed0_1400update_summary.csv`.
- seed-0 1500-update output audit passed and wrote `results/dev1m_seed0_1500update_summary.csv`; the 5-episode online monitor at this checkpoint showed EA-RG-MAPPO success 0.4 and Single-Graph/MAPPO/HAPPO success 0.0.
- seed-0 1600-update output audit passed and wrote `results/dev1m_seed0_1600update_summary.csv`; the 5-episode online monitor at this checkpoint showed EA-RG-MAPPO and HAPPO success 0.4, while Single-Graph and MAPPO/no-graph remained 0.0.
- seed-0 1700-update output audit passed and wrote `results/dev1m_seed0_1700update_summary.csv`; the 5-episode online monitor at this checkpoint showed EA-RG-MAPPO success 0.6 and Single-Graph/MAPPO/HAPPO success 0.0.
- seed-0 1800-update output audit passed and wrote `results/dev1m_seed0_1800update_summary.csv`; the 5-episode online monitor at this checkpoint showed Single-Graph success 0.4 and EA-RG-MAPPO/MAPPO/HAPPO success 0.0, reinforcing that online 5-episode checks are only noisy monitors and validation-set checkpoint selection is mandatory.
- seed-0 1900-update output audit passed and wrote `results/dev1m_seed0_1900update_summary.csv`; the 5-episode online monitor at this checkpoint showed all four methods success 0.0, so training continues toward full 3907-update completion before validation selection.
- seed-0 2000-update output audit passed and wrote `results/dev1m_seed0_2000update_summary.csv`; all four methods are now past the halfway point of dev_1m seed-0 training and remain in development-monitoring mode until full 3907-update completion.
- seed-0 2100-update output audit passed and wrote `results/dev1m_seed0_2100update_summary.csv`; all four methods remain synchronized and continue toward the 3907-update validation gate.
- seed-0 2200-update output audit passed and wrote `results/dev1m_seed0_2200update_summary.csv`; all four methods remain synchronized at 56.31% of the dev_1m budget.
- seed-0 2300-update output audit passed and wrote `results/dev1m_seed0_2300update_summary.csv`; all four methods remain synchronized at 58.87% of the dev_1m budget.
- The project-summary review on 2026-07-26 identified four paper-risk items and the first fixes are now implemented: README rewritten as paper-facing documentation, dependencies pinned in `requirements.txt`, HAPPO renamed to HAPPO-style unless a standard implementation is integrated, and target-prior sensitivity exposed through `--target-prior-position`.
- HAPPO hardening on 2026-07-26 replaced the earlier HAPPO-style sequential PPO loss with a HAPPO sequential joint-ratio-corrected surrogate. Formal HAPPO evidence must be generated from post-correction checkpoints; older HAPPO-style outputs remain historical diagnostics only.
- Corrected HAPPO manifest commands now write to `results/paper_config_runs/<mode>/runs/happo_standard/` so they cannot accidentally resume from the older `runs/happo/` HAPPO-style checkpoint directory.
- Added `docs/target_prior_ablation_protocol.md`; target-prior perturbation diagnostics are now a required post-validation robustness check, not a main contribution.
- A dev-1M seed 0/1/2 target-prior sensitivity diagnostic is complete in
  `docs/dev1m_seed0_2_target_prior_sensitivity_diag.md`. Perturbing the target
  prior from `(10000, 0, 5000)` to `(10000, 8000, 5000)` and `(0, -20000,
  5000)` does not reveal a simple target-prior leakage explanation. Mean
  success/recovery changes versus the default prior are: EA-RG-MAPPO `-0.0889`
  under lateral offset and `+0.1111` under far prior; Single-Graph `-0.1778`
  under both perturbations; MAPPO/no-graph `0.0000` and `-0.0111`. This is a
  useful credibility audit, but MAPPO/no-graph remains too competitive in some
  seeds, so the next scientific step is still stronger communication-dependence
  or causal mechanism evidence.
- A fresh-message stress diagnostic is complete in
  `docs/dev1m_fresh20_dropout030_delay2_stress_diag.md`. Using frozen dev-1M
  validation-selected checkpoints with `max_target_message_age_steps=20`,
  dropout `0.30`, and delay `2`, mean success/recovery is EA-RG-MAPPO `0.2222`,
  Single-Graph `0.0778`, and MAPPO/no-graph `0.3222`. This condition suppresses
  Single-Graph but does not solve the no-graph issue because MAPPO seed 1 remains
  very strong (`0.9667`). Do not promote this stress condition as a final main
  scenario. The next step should diagnose MAPPO/no-graph seed 1 behavior and
  identify whether its success comes from geometric interception, target-cache
  use, or an environment shortcut.
- MAPPO/no-graph seed-1 anomaly analysis is complete in
  `docs/dev1m_no_graph_seed1_anomaly_diagnostic.md`. Under the fresh20 stress,
  successful no-graph seed-1 episodes end around `60` steps on average and form
  the first attack window around step `57`, shortly after relay failure starts
  at step `40`, while failure-window connectivity is only `0.1455`. This points
  to fast geometric interception rather than communication-recovery behavior.
  The next quality step is evaluation/task hardening: distinguish early
  geometric closure from true post-failure chain recovery, for example by
  requiring post-failure loss-and-recovery, sustained chain closure, or target
  initial-condition randomization.
- Strict recovery metric hardening is implemented as a post-processing script in
  `scripts/analyze_strict_recovery_hardening.py` and documented in
  `docs/dev1m_strict_recovery_metric_hardening.md`. On the fresh20 stress
  diagnostic, raw legacy recovery is EA-RG-MAPPO `0.2222`, MAPPO/no-graph
  `0.3222`, and Single-Graph `0.0778`. Requiring delayed recovery at step
  `>=80` changes the result to EA-RG-MAPPO `0.0333`, MAPPO/no-graph `0.0000`,
  and Single-Graph `0.0000`, filtering the no-graph seed-1 early-geometry
  anomaly. Candidate final primary metric: `delayed_recovery_ge_80`. This
  metric is scientifically cleaner but currently too sparse, so the next
  protocol should retrain/evaluate with this metric in mind rather than using
  raw success alone.
- Checkpoint-sweep support for delayed-recovery selection is implemented and
  documented in `docs/checkpoint_sweep_delayed_recovery_selection_update.md`.
  `scripts/evaluate_3d_checkpoint_sweep.py` now supports
  `--selection-metric delayed_recovery --delayed-recovery-min-step 80
  --selection-success-weight 0`, while default legacy selection remains
  unchanged. `configs/paper/checkpoint_selection_schema.yaml` was updated to v2
  with delayed-recovery columns, schema audit passed, and a MAPPO/no-graph
  seed-1 smoke showed legacy recovery `1.0` but delayed recovery `0.0`,
  correctly penalizing early geometric closure. A focused MAPPO/no-graph seed-1
  candidate sweep is recorded in
  `docs/delayed_recovery_mappo_seed1_candidate_sweep.md`: update `2300` has
  legacy recovery `0.8000` but delayed recovery `0.0000`. Future strict
  relay-failure validation sweeps should use delayed-recovery selection with
  success weight `0`; if all candidate checkpoints have zero delayed recovery,
  treat that seed as a failed delayed-recovery run rather than as a meaningful
  selected checkpoint.

## Stable Research Direction

`EA-RG-MAPPO` is the main paper method:

- edge-aware role graph policy;
- perception, communication, and dynamic task-support multi-relation graph reasoning;
- role-pair-conditioned message passing;
- limited-communication graph attention under strict intermittent target sensing.

Topology curriculum, reward shaping, rules, ELO, self-play, and JSBSim replay are auxiliary protocols or future extensions. They must not be written as primary contributions unless later evidence specifically supports that claim.

Current safe paper claim:

> Under strict intermittent sensing, target-information bottleneck, communication dropout, and relay-node failure, EA-RG-MAPPO-S improves 3DOF heterogeneous UAV kill-chain recovery reliability over no-graph, single-graph, and parameter-matched single-graph baselines.

Target next-stage claim:

> The same graph/message mechanism remains useful under selected scenario-depth extensions such as harder failure timing and maneuvering targets, without changing the core contribution boundary.

## Completed

- 2D heterogeneous UAV pursuit environment and MAPPO/GAT-MAPPO/EA-RG-MAPPO-S training/evaluation chain.
- Final 2D main evaluation with 3 seeds and 300 evaluation episodes per seed.
- Communication dropout, radius interpolation, speed robustness, and edge-feature diagnostic evaluations.
- Chinese/English manuscript drafts, LaTeX projects, figures, tables, and evidence audits.
- Reproducibility checksum manifest and checksum verification.
- LAG-like role graph adapter/wrapper tests for future 6DOF migration.
- First 3DOF 3v1 heterogeneous interception environment smoke test.
- Maintained 3DOF EA-RG-MAPPO-S checkpoint evaluation script and diagnostic CSV schema.
- First non-smoke 3DOF learnability diagnostic under a straight-target curriculum.
- Low-level altitude and horizontal-boundary flight-envelope protection in the 3DOF environment.
- Geometric-demonstration behavior-cloning warm start and BC-to-PPO fine-tuning path.
- Matched three-replicate 3DOF straight-target baseline protocol with 360 independently evaluated episodes.
- Perception, communication, and dynamic task-support relation adjacencies in the 3DOF graph observation.
- Role-pair-conditioned multi-relation graph encoder with a union-graph residual path.
- Matched three-seed single-graph vs multi-relation BC-to-PPO straight-target comparison.
- Stage-configurable 3DOF communication range scaling, dropout, delay, radar dropout, and temporary communication-node failure.
- Zero-shot topology robustness screening script for existing 3DOF checkpoints.
- Episode-level 3DOF topology domain randomization hooks for range scale, communication dropout, message delay, and radar dropout during PPO training.
- Matched topology-curriculum protocol script for continuing nominal checkpoints under randomized communication topology and evaluating the same robustness suite.
- Random temporary blue-node communication failure curriculum hooks for PPO training.
- Paper-facing 3DOF robustness main table for the current evidence triage.
- Relay-failure matched episode candidate list for later trajectory/timeline case visualization.
- Relay-failure per-step replay CSV, qualitative summary, and timeline/trajectory figure for the top matched case.
- `no_task_support` graph-relation ablation switch across 3DOF environment, BC pretraining, PPO training, robustness evaluation, and replay.
- Seed-0 diagnostic task-support ablation pilot comparing full multi-relation against no-task-support under relay/scout failure.
- Formal three-seed `no_task_support` task-support ablation under relay/scout node-failure evaluation.
- Formal three-seed scale-matched `no_role_pair_gate` message ablation under relay/scout node-failure evaluation.
- `graph_input_ablation=no_edge_features` switch across 3DOF training, BC pretraining, policy evaluation, topology robustness evaluation, and baseline/topology protocols; compile, 3DOF smoke, one-update training smoke, evaluation smoke, and the full lightweight build gate passed.
- Seed-0 `no_edge_features` diagnostic through BC-to-PPO baseline, node-failure topology curriculum, relay/scout robustness evaluation, and paired diagnostic analysis.
- `graph_input_ablation=no_role_identity` switch across 3DOF training/evaluation paths, with smoke validation, seed-0 diagnostic, and formal three-seed relay/scout node-failure evaluation.
- `target_policy=break_turn` and `target_policy=weaving` maneuvering target policies in the 3DOF environment, including red-side altitude and boundary protection.
- Zero-shot break-turn node-failure scenario-depth pilot using existing straight-target topology-curriculum checkpoints.
- `target_policy=weaving_mild` reduced-amplitude maneuvering target policy and maneuvering-target pilot summary.
- Oracle geometric node-failure diagnostic and compact straight-target node-failure baseline table comparing oracle geometric pursuit, single-graph MAPPO, and EA-RG-MAPPO-S.
- Opt-in strict intermittent-sensing switch for the 3DOF environment, plus a strict-sensing smoke test and a small relay/scout node-failure screening evaluation.
- Manuscript-ready 3DOF figure asset generator for the task scene, multi-relation role graph, main recovery evidence, and strict-sensing scenario-depth result.
- Separate English 3DOF LaTeX manuscript path under `paper_latex_3d_en/`, preserving the older 2D LaTeX drafts.
- Formal strict-sensing protocol entry point with checkpoint snapshots, fixed validation/test splits, validation-based checkpoint selection, and a smoke-validated end-to-end run.
- Three-seed strict-sensing relay-failure development run with 120-update checkpoint snapshots, fixed validation checkpoint selection, and disjoint 100-episode-per-seed test evaluation.
- Seed-aware strict-sensing relay-failure statistics with hierarchical bootstrap over training seeds and matched test episodes.
- `no_graph` MAPPO-style actor baseline and fair strict-sensing baseline protocol entry point covering `no_graph`, `single`, and `multi_relation`.
- Smoke-scale fair baseline run under `results/intercept_3d_strict_sensing_fair_baselines_smoke/`, validating BC pretraining, PPO topology curriculum, validation checkpoint selection, and disjoint test evaluation for all three baseline classes.
- Two-seed fair-baseline development run under `results/intercept_3d_strict_sensing_fair_baselines_dev2/` with 12 BC episodes, 2 BC epochs, and 5 PPO updates. The protocol completed for `no_graph`, `single`, and `multi_relation`, but validation recovery stayed at zero for all methods, so the run is an integration/budget diagnostic rather than a performance result.
- Fair-baseline development summary generated at `docs/intercept_3d_strict_sensing_fair_baseline_dev_summary.md`.
- Current requirements and scope boundaries are recorded in `docs/CURRENT_REQUIREMENTS.md`.
- Seed-0 BC-strength diagnostic under `results/intercept_3d_strict_sensing_bc_strength_diag_seed0/` increased BC to 40 episodes and 10 epochs for `single` and `multi_relation`, but validation/test recovery still stayed at zero. This suggests that direct BC-to-strict-relay training is not the right fair-baseline path; the fair protocol should prepare comparable nominal/node-failure source checkpoints before strict-sensing fine-tuning.
- Fair staged source protocol script added at `scripts/run_3d_fair_staged_source_protocol.py`. It prepares `stage1_bc`, `stage2_nominal`, `stage3_curriculum`, and optional `stage4_strict_smoke` outputs for `no_graph`, `single`, and `multi_relation`.
- Minimal fair staged source smoke completed under `results/intercept_3d_fair_staged_source_smoke/`. All three graph encoders produced BC, nominal, curriculum, and strict-sensing snapshot checkpoints, and the strict checkpoint sweep consumed the staged source outputs successfully.
- Seed-0 fair staged source development run under `results/intercept_3d_fair_staged_source_dev_seed0/` completed for `single` and `multi_relation` with 40 BC episodes, 10 BC epochs, 5 nominal updates, 5 curriculum updates, and 3 strict updates. Source-quality audit showed zero nominal success, zero curriculum success, and zero strict validation recovery.
- Seed-0 nominal source budget diagnostic under `results/intercept_3d_nominal_source_budget_diag_seed0/` increased nominal PPO to 20 updates from the same BC source, but both `single` and `multi_relation` still had zero nominal success. Summary is recorded in `docs/intercept_3d_nominal_source_budget_diag_seed0.md`.
- Fair source checkpoint inventory in `docs/intercept_3d_fair_source_checkpoint_inventory.md` confirms existing `single` and `multi_relation` source checkpoints are available for seeds `0, 1, 2`; `no_graph` sources were missing.
- `no_graph` seed-0 source training completed under `results/intercept_3d_no_graph_source/` and `results/intercept_3d_no_graph_source_curriculum/`: strong BC (`200` episodes, `80` epochs), nominal PPO (`60` updates), and topology/node-failure curriculum (`20` updates). Nominal success reached `0.9` at update 30 and curriculum success reached `0.5`.
- Mixed-source strict-sensing seed-0 diagnostic completed under `results/intercept_3d_strict_sensing_mixed_source_seed0_diag/`, using the new `no_graph` source and existing `single` / `multi_relation` sources. Validation/test recovery became nonzero: validation `no_graph=48%`, `single=74%`, `multi_relation=100%`; test `no_graph=30%`, `single=100%`, `multi_relation=100%`. This is a development diagnostic, not a formal result.
- Strongest current three-method 3DOF diagnostic completed under `results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_formal_diag/`: `dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck` gives test recovery `no_graph=25.0%`, `single=78.3%`, and `multi_relation=95.0%`; seed-aware `multi_relation - single` recovery delta is `+16.7 pp` with 95% CI `[+6.7, +28.3] pp`.
- The frozen five-seed expansion contract is now recorded in `docs/bottleneck_dropout030_relay_frozen_protocol.md`.
- New bottleneck-protocol evaluation outputs now include explicit `strict_target_sensing` and `agent_target_info_bottleneck` CSV fields; schema smoke evidence is recorded in `docs/intercept_3d_bottleneck_metadata_smoke.md`.
- Q1 execution plan added at `docs/Q1_EXECUTION_PLAN.md`, with Gate 1 focused on information realism before any 5v2 or five-seed formal expansion.
- Gate 1 first pass completed: task-support edges now follow `A[receiver, sender]`, require delivered communication, and 3DOF actor construction disables global intent-context broadcasting. Audit notes are recorded in `docs/gate1_communication_feasibility_audit.md`.
- Actor-vs-critic CTDE observation boundaries are documented in `docs/actor_critic_observation_boundary.md`.
- Role-conditioned centralized critic hardening is implemented in `algorithms/ri_gmappo/simple_ri_gmappo.py` and audited in `docs/critic_role_conditioning_audit.md`. The actor information boundary is unchanged; the critic now receives each blue agent's role one-hot to align value estimation with heterogeneous role-specific returns.
- True `no_role_identity` hardening is implemented and audited in `docs/true_no_role_identity_ablation_audit.md`. The ablation now removes explicit actor role indicators from role embeddings, role-pair message inputs, local observation role fields, and graph-node role fields while preserving physical capability heterogeneity. Older `no_role_identity` results are pre-hardening evidence and require rerun before paper use.
- A small post-hardening `no_role_identity` diagnostic is recorded in `docs/true_no_role_identity_post_hardening_diag10_summary.md`. Using hardened no-role inference on pre-hardening no-role checkpoints, recovery dropped to `50.0%` on both `dropout030_relay_failure` and `scout_failure`, versus `76.7%` and `86.7%` for full fixed-update-60 reference checkpoints on the same small matched evaluation budget. This is go/no-go evidence only; formal paper use still requires retraining no-role checkpoints under the hardened semantics.
- A 5-episode post-Gate-1 compatibility evaluation for one existing `multi_relation` checkpoint ran successfully under the frozen dropout-relay bottleneck settings; this is smoke evidence only, not paper evidence.
- A 5-episode seed-0 three-method post-change diagnostic also ran successfully: `no_graph=0%`, `single=60%`, `multi_relation=100%` recovery. This preserves the expected ordering but is only smoke evidence.
- A three-seed checkpoint-reuse post-Gate-1 diagnostic is recorded in `docs/intercept_3d_gate1_post_change_3seed_diag_summary.md`: aggregate recovery was `no_graph=30.0%`, `single=26.7%`, `multi_relation=86.7%`; seed-aware `multi_relation - single` recovery delta was `+60.0 pp` with 95% CI `[+20.0, +93.3] pp`.
- A tiny seed-0 post-Gate-1 retraining smoke is recorded in `docs/intercept_3d_gate1_post_change_retrain_smoke_summary.md`: after 3 continuation PPO updates, `single` recovered `90.0%` and `multi_relation` recovered `100.0%` over 10 episodes.
- A three-seed post-Gate-1 retraining diagnostic is recorded in `docs/intercept_3d_gate1_post_change_retrain_3seed_diag_summary.md`: after 3 continuation PPO updates, `single` recovered `35.0%` and `multi_relation` recovered `95.0%` over 60 matched episodes; seed-aware recovery delta was `+60.0 pp` with 95% CI `[+16.7, +90.0] pp`.
- A 20-update post-Gate-1 retraining diagnostic with validation checkpoint selection is recorded in `docs/intercept_3d_gate1_post_change_retrain_20update_diag_summary.md`: over 60 matched disjoint test episodes, `single` recovered `33.3%` and `multi_relation` recovered `93.3%`; seed-aware recovery delta was `+60.0 pp` with 95% CI `[+16.7, +91.7] pp`, and restricted mean recovery-step delta was `-125.13` with 95% CI `[-189.58, -35.85]`.
- A 60-update post-Gate-1 retraining diagnostic with validation checkpoint selection is recorded in `docs/intercept_3d_gate1_post_change_retrain_60update_diag_summary.md`: over 60 matched disjoint test episodes, `single` recovered `43.3%` and `multi_relation` recovered `93.3%`; seed-aware recovery delta was `+50.0 pp` with 95% CI `[+15.0, +80.0] pp`, and restricted mean recovery-step delta was `-110.57` with 95% CI `[-171.70, -42.23]`.
- `scripts/evaluate_3d_checkpoint_sweep.py` now supports `--max-selection-collision-rate`; formal validation can reject checkpoints with collisions before final testing. The frozen bottleneck protocol now recommends `--max-selection-collision-rate 0.0`.
- `scripts/run_3d_strict_sensing_formal_protocol.py` now forwards `--max-selection-collision-rate` to validation checkpoint sweeps. A one-update formal-protocol smoke passed under `results/intercept_3d_formal_protocol_collision_option_smoke3/`.
- A three-method post-Gate-1 60-update safety-selected diagnostic is recorded in `docs/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag_summary.md`: validation-selected test recovery was `no_graph=31.7%`, `single=38.3%`, and `multi_relation=98.3%`; seed-aware `multi_relation - single` recovery delta was `+60.0 pp` with 95% CI `[+26.7, +86.7] pp`, and `multi_relation - no_graph` was `+66.7 pp` with 95% CI `[+1.7, +100.0] pp`.
- Five-seed launch plan is recorded in `docs/post_gate1_five_seed_launch_plan.md`. Current blocker: source checkpoints for seeds `3` and `4` are missing for all three formal methods.
- Seed `3` and `4` source generation is complete for `no_graph`, `single`, and `multi_relation`. The summary is recorded in `docs/post_gate1_seed34_source_generation_summary.md`; every method now has seeds `0, 1, 2, 3, 4` with six post-Gate-1 checkpoint snapshots.
- A five-seed checkpoint-sweep integration diagnostic is recorded in `docs/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag_summary.md`: with small validation/test budgets, recovery was `no_graph=26.0%`, `single=46.0%`, and `multi_relation=94.0%`; seed-aware `multi_relation - single` recovery delta was `+48.0 pp` with 95% CI `[+18.0, +82.0] pp`.
- The five-seed formal `dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck` run is complete and recorded in `docs/intercept_3d_gate1_dropout030_bottleneck_5seed_formal_summary.md`. Validation evaluated 90 candidate checkpoints and selected 15 zero-validation-collision checkpoints. Disjoint testing used 100 episodes per selected method/seed checkpoint, for 1500 test episodes total. Test recovery was `no_graph=34.2%`, `single=51.8%`, and `multi_relation=96.2%`. Seed-aware `multi_relation - single` recovery delta was `+44.4 pp` with 95% CI `[+16.2, +74.4] pp`; `multi_relation - no_graph` was `+62.0 pp` with 95% CI `[+27.8, +95.2] pp`.
- `scripts/analyze_3d_failure_aligned_mechanism.py` now generates failure-aligned mechanism curves and a median-difference representative case from the completed five-seed formal test CSV and validation-selected checkpoints. Syntax validation and a 2-episode-per-method smoke run passed under `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_smoke_cached/`. Full 1500-episode per-step replay is not complete yet because the current tool call has a 300-second hard limit; the script has been extended with method, train-seed, and episode-range chunk filters for the next resumable implementation pass.
- Failure-aligned mechanism evidence is now complete under `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/` and documented at `docs/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/failure_aligned_mechanism_summary.md`. The corrected curve schema separates `n_available` instantaneous metric support from `n_episode` recovery-CDF support. At `relative_step=220`, recovery CDF matches the formal test rates: `no_graph=0.342`, `single=0.518`, and `multi_relation=0.962`. The representative median-difference case is seed `0`, episode `11`: `single` fails to recover while `multi_relation` closes the chain 6 steps after relay failure.
- Gate 1 P0-1 actor-localization first pass is complete. The 3DOF actor observation no longer includes team-level communication connectivity, team mean message age, global last-detection age, or global attack-hold progress. Those four slots are now local inbound connectivity, local inbound message age, local target-cache age, and local target-cache confidence. `tests.test_gate1_communication_feasibility` now includes a regression test that changes only team-level aggregate shortcuts and verifies the disconnected attacker's actor observation is unchanged.
- Gate 1 P0 target-message freshness first pass is complete. `max_target_message_age_steps` and `min_target_confidence` now flow through the 3DOF environment, training, BC pretraining, checkpoint sweep, formal protocol, evaluator, topology robustness, geometric baseline, replay, and mechanism-analysis scripts. `_has_target_information()`, attacker chain checks, actor target-cache confidence, and exported info metrics now reject stale or low-confidence target cache entries. Gate 1 tests cover stale cache rejection, low-confidence rejection, and fresh-cache validity.
- Gate 1 P0 timing semantics first pass is complete. `env.step()` now returns post-step state consistently, delayed message delivery and node-failure activation use the same returned timestamp, and post-failure metrics now distinguish maintained, recovered-after-loss, and unrecovered outcomes. Audit notes are recorded in `docs/gate1_timing_semantics_audit.md`.
- Gate 1 P0 graph-information first pass is complete. Under strict target sensing plus the target-information bottleneck, `_get_graph_obs()` no longer exposes stale global last-detected target state through the shared target node; no-current-detection graph target state is now the fixed prior, while current direct detection still exposes the current target. Gate 1 tests, 3DOF smoke, evaluator smoke, and a one-update PPO training smoke passed. Audit notes are recorded in `docs/gate1_graph_information_audit.md`.

## In Progress

- Freeze and polish the fixed-update-60 Gate 1 evidence package: main comparison, capacity-control baseline, mechanism ablations, timing generalization, model-cost report, and failure-aligned explanation.
- Keep the paper contribution boundary centered on strict-sensing relay-failure recovery and role-graph/message mechanisms.
- Treat no-curriculum, scout-failure stressors, and weaving-target experiments as boundary/supporting diagnostics unless later formal evidence justifies promotion.
- Continue only reviewer-critical consistency, reproducibility, and manuscript-readiness work before any new compute-heavy experiment.
- Stage 1 automated closure checks pass. Stage 2 three-seed frozen-protocol diagnostic is complete but below the paper-facing acceptance gate. Do not expand to five seeds or tune on the `609000` test split. Next work should either return to Gate 1 manuscript packaging or design a revised Stage 2 protocol using validation-only diagnostics.
- Final single-paper scope is now fixed: do not start full 4v2/5v2, self-play, online missile/radar, or full JSBSim baseline training for this paper. Optional realism work must be small and directly support the same Gate 1 paper.

## Known Issues

- The current main result is a hardened 3v1 strict-sensing dropout-relay mechanism study, not a complete 4v2 red-blue air-combat system.
- The evidence is strongest for recovery reliability and tracking under relay failure. Claims about recovered-only recovery speed, arbitrary failure timing, and all communication stressors should be softened.
- The no-curriculum diagnostic does not prove an independent topology-curriculum advantage, so curriculum remains a training protocol rather than a contribution.
- Scout-failure and delayed scout-failure stressors are useful supplemental screens but are not yet formal main-table evidence against the single-graph baseline.
- Maneuvering-target work is promising only after oracle-assisted training; it remains scenario-depth development evidence until hardened validation/test splits and formal seed-aware statistics are complete.
- Under nominal straight-target training, the multi-relation and single-graph success intervals overlap; no nominal-condition superiority claim is supported.
- LAG/JSBSim is currently interface-level only; no real JSBSim reset/step evaluation has passed.
- Intent prediction diagnostics are weak and must not be used as a main contribution.
- Full 4v2 red-blue self-play, ELO, missile online simulation, and human-UAV teaming are out of scope for the immediate paper.
- PDF visual rendering has not passed in this environment because a LaTeX toolchain is unavailable; static manuscript checks are the current local gate.

## Current Maintained Gate

Latest full lightweight build passed with:

```text
required files checked: 144
required scripts checked: 50
checksum rows: 184
schema audit rows: 32
provenance audit rows: 56
```

## Repository State

- Local Git repository initialized on branch `main`.
- GitHub remote configured as `origin = https://github.com/AIYING6/xm.git`.
- Initial local commit: `7a037f3 chore: initialize UAV research project`.
- Latest manuscript skeleton commit before proxy-push workflow update: `4aab7a8 docs: draft 3d manuscript skeleton`.
- Heavy model checkpoints (`*.pt`, `*.pth`, `*.ckpt`, `*.onnx`) are ignored by `.gitignore`; the local Git object store is about 3.15 MiB after the initial commit.
- Push from this Codex environment should use the local proxy: `HTTPS_PROXY=http://127.0.0.1:7897 git push -u origin main`.

## Latest Integration Check

- `train_ri_gmappo.py` now supports `--env-name 2d_pursuit` (default) and `--env-name 3d_intercept`.
- The role embedding size is inferred from the selected environment graph, so the 3DOF target role is supported.
- The 3DOF graph supplies a neutral placeholder for the legacy intent context but marks it unsupervised; no intent auxiliary loss is applied.
- One-update smoke runs completed for both 2D and 3DOF and wrote logs plus latest/best checkpoints under `results/ri_gmappo_2d_smoke/` and `results/ri_gmappo_3d_smoke/`.
- `scripts/evaluate_ri_gmappo_3d.py` evaluates saved 3DOF checkpoints and writes task-chain metrics to `results/intercept_3d_policy_eval.csv`.
- A from-scratch 30-update PPO diagnostic failed through low-altitude constraint termination. Flight-envelope protection removes this invalid failure mode: the same policy then times out rather than violating constraints.
- The geometric 3DOF controller solves 0.8 of five smoke episodes, so the environment is task-solvable. Under the straight-target curriculum, an 80-epoch unweighted behavior-cloning warm start reaches 0.70 success over 20 independent evaluation episodes; a 60-update PPO fine-tune reaches 0.967 success over 30 independent episodes, with zero collisions and zero constraint violations.
- A 20-episode light-stress check (0.15 communication dropout, two-step delay, 0.1 radar dropout) did not fail, but the sample is too small and the policy was not trained with topology randomization. Treat this only as an integration check.
- The supported training entry for the next stage is `scripts/pretrain_ri_gmappo_3d_bc.py` followed by `scripts/train_ri_gmappo.py --resume <bc_checkpoint>`.
- The matched baseline protocol in `scripts/run_3d_baseline_protocol.py` completed with three training/evaluation replicates and 30 independent evaluation episodes per replicate. In the 3DOF straight-target task, geometric control reached `1.000 +/- 0.000` success, RI-GMAPPO from scratch reached `0.000 +/- 0.000`, BC-only reached `0.844 +/- 0.077`, and BC-to-PPO reached `0.967 +/- 0.033`. BC-to-PPO had zero collisions and zero constraint violations; this establishes a learnable curriculum baseline, not a main-method comparison.
- `relation_adj` now carries separate perception, communication, and dynamic task-support adjacencies while the old `adj` remains the union graph for a strict single-graph ablation. `graph_encoder=multi_relation` applies role-pair-conditioned messages over each relation plus a union-graph residual path. A one-seed diagnostic with 200 BC episodes, 80 BC epochs, and conservative PPO fine-tuning (60 updates, learning rate `5e-5`, entropy coefficient `0.001`) reached `1.000` success over 30 independent straight-target episodes with zero collisions, timeouts, and constraint violations. This is an integration/learnability result only.
- The matched three-seed comparison is complete with 30 independent episodes per seed. Single-graph BC-only/BC-to-PPO reached `0.844 +/- 0.051` and `0.900 +/- 0.033` success, respectively; multi-relation BC-only/BC-to-PPO reached `0.933 +/- 0.115` and `0.922 +/- 0.107`. All variants had zero collision and constraint-violation rates. The mean multi-relation result is slightly higher but its interval overlaps the single-graph result, so nominal-condition performance is a feasibility baseline rather than the main method claim.
- `UAVIntercept3DConfig` now exposes `communication_range_scale`, `failed_blue_agent`, `node_failure_start_step`, and `node_failure_duration_steps`. `train_ri_gmappo.py` also supports fixed or randomized 3DOF communication range scaling for staged topology curriculum training.
- `scripts/evaluate_3d_topology_robustness.py` reuses existing single-graph and multi-relation checkpoints and evaluates matched disruption scenarios. A screening run with 3 training seeds, 11 scenarios, and 5 episodes per checkpoint-scenario produced 330 episodes under `results/intercept_3d_topology_robustness_screen/`.
- The screening result shows that nominally trained multi-relation checkpoints do not yet outperform the single-graph checkpoints under the tested disruptions. Treat this as evidence that topology-curriculum retraining is necessary, not as a negative final result.
- A one-update multi-relation topology-curriculum training smoke passed from an existing seed-0 checkpoint using randomized range scale, dropout, delay, and radar dropout. This validates the training interface only; it is not a result.
- `scripts/run_3d_topology_curriculum_protocol.py` completed an initial three-seed 20-update pilot with single-graph and multi-relation checkpoints, followed by 330 robustness evaluation episodes under `results/intercept_3d_topology_curriculum_protocol_seed0_pilot/`. The directory name is historical from the first seed-0 run; it now contains seeds 0, 1, and 2.
- In the 20-update pilot, multi-relation and single-graph are mostly tied on nominal, dropout, delay, and range-0.75 scenarios. Multi-relation has a positive signal on `radar_025`, `relay_failure`, and `scout_failure`, while `range_050` remains too severe and favors single-graph. Treat this as scenario-selection evidence, not a final robustness claim.
- Random node-failure curriculum parameters are now available (`--node-failure-random-prob`, start-step range, and duration range). A one-update smoke run passed under `results/intercept_3d_node_failure_curriculum_smoke/`.
- A focused three-seed node-failure curriculum pilot also completed under `results/intercept_3d_node_failure_curriculum_pilot_seed0/` with 20 fine-tuning updates and 330 evaluation episodes. It used a milder range curriculum (`0.65--1.0`) plus random temporary blue-node failures. Multi-relation outperformed single-graph on most non-extreme scenarios in this pilot, including nominal, range-0.75, dropout, delay-2, radar perturbations, relay failure, and scout failure. `range_050` remains an extreme out-of-training stress case where single-graph performs better.
- A formal-budget node-failure evaluation completed under `results/intercept_3d_node_failure_curriculum_formal_node_failure_eval/` with 3 seeds, 30 episodes per checkpoint-scenario, and 360 total episodes. Under relay failure, multi-relation reached `1.000 +/- 0.000` success versus single-graph `0.922 +/- 0.016`; under scout failure, multi-relation reached `0.967 +/- 0.047` versus single-graph `0.944 +/- 0.016`. Multi-relation also used fewer steps on both scenarios. This is the first usable 3DOF robustness evidence, though more selected scenarios are still needed.
- A second formal-budget selected robustness evaluation completed under `results/intercept_3d_node_failure_curriculum_formal_selected_eval/` with 720 total episodes. Multi-relation is ahead on `delay_2` (`0.967 +/- 0.047` vs `0.944 +/- 0.016`), `dropout_030` (`0.967 +/- 0.027` vs `0.933 +/- 0.027`), and `radar_025` (`0.944 +/- 0.079` vs `0.922 +/- 0.031`), with fewer average steps. Single-graph is ahead on `range_075` (`0.967 +/- 0.027` vs `0.944 +/- 0.079`), so range compression should be treated as a mixed stress case rather than the main positive claim.
- `scripts/analyze_3d_topology_curriculum_statistics.py` now consolidates the formal node-failure and selected robustness evaluations into `results/intercept_3d_topology_curriculum_formal_summary.csv` and `docs/intercept_3d_topology_curriculum_formal_summary.md`. The current delta table favors multi-relation in 5 of 6 formal scenarios: `delay_2`, `dropout_030`, `radar_025`, `relay_failure`, and `scout_failure`; `range_075` favors single-graph.
- The formal summary now includes paired episode bootstrap confidence intervals. Only `relay_failure` currently has a success-rate CI fully above zero (`+0.078`, 95% CI `[+0.022, +0.133]`) and a steps CI fully below zero (`-16.2`, 95% CI `[-28.0, -6.7]`). Other positive scenarios should be described as trends until more seeds or stronger evaluation settings are added.
- 3DOF evaluation rows now include kill-chain timing and node-failure recovery metrics: first attack-window step, first chain-close step, post-failure recovery indicator, post-failure recovery steps, chain-closed rate during failure, tracking during failure, and connectivity during failure.
- `scripts/analyze_3d_node_failure_recovery.py` produces `results/intercept_3d_node_failure_recovery_summary.csv` and `docs/intercept_3d_node_failure_recovery_summary.md`. In `relay_failure`, multi-relation improves post-failure chain recovery probability by `+0.078` with 95% CI `[+0.022, +0.133]`, and reduces recovery steps by `-16.2` with 95% CI `[-28.0, -4.5]`. This directly supports the “kill-chain recovery after relay failure” paper claim. `scout_failure` remains a positive but non-separated trend.

- `scripts/build_3d_paper_tables.py` now produces `results/intercept_3d_paper_main_table.csv`, `docs/intercept_3d_paper_main_table.md`, and `docs/intercept_3d_paper_main_table.tex`. The table separates the current evidence into a defensible main claim (`relay_failure`), supporting trends (`scout_failure`, dropout, delay, radar), and a mixed stress case (`range_075`).
- `scripts/find_3d_relay_failure_case_candidates.py` now produces `results/intercept_3d_relay_failure_case_candidates.csv` and `docs/intercept_3d_relay_failure_case_candidates.md`. The top candidate is train seed `0`, episode `0`, where the single-graph checkpoint does not recover after relay failure while the multi-relation checkpoint recovers in `8` steps.
- `scripts/replay_3d_relay_failure_case.py` now replays the top relay-failure candidate and produces `results/intercept_3d_relay_failure_case_replay.csv`, `docs/intercept_3d_relay_failure_case_replay.md`, and `results/figures/intercept_3d_relay_failure_case_replay.png`. In the replay, the single-graph policy times out at `260` steps without chain closure while the multi-relation policy closes the chain at step `48`.
- The full lightweight paper asset gate passed after adding the 3DOF paper table, relay-failure case-candidate, and relay-failure replay scripts.
- `graph_relation_ablation=no_task_support` removes the dynamic task-support relation from the 3DOF graph and is now exposed through `scripts/train_ri_gmappo.py`, `scripts/pretrain_ri_gmappo_3d_bc.py`, `scripts/evaluate_ri_gmappo_3d.py`, `scripts/evaluate_3d_topology_robustness.py`, `scripts/run_3d_baseline_protocol.py`, `scripts/run_3d_topology_curriculum_protocol.py`, and `scripts/replay_3d_relay_failure_case.py`.
- A seed-0 diagnostic pilot completed under `results/intercept_3d_no_task_support_baseline_seed0_pilot/` and `results/intercept_3d_no_task_support_topology_seed0_pilot/`. Compared with the full multi-relation seed-0 checkpoint on the same relay/scout evaluation seeds, full multi-relation reached `1.000` success while no-task-support reached `0.300`, with average steps `45.9` versus `195.5`. This is strong diagnostic support for a formal task-support ablation, but it is not yet paper-level statistical evidence.
- `scripts/analyze_3d_task_support_ablation_pilot.py` produces `results/intercept_3d_task_support_ablation_seed0_pilot_summary.csv` and `docs/intercept_3d_task_support_ablation_seed0_pilot_summary.md`.
- `scripts/run_3d_task_support_ablation_protocol.py` now defines the formal no-task-support ablation protocol. The formal run completed for seeds `0, 1, 2` under `results/intercept_3d_no_task_support_baseline_formal/` and `results/intercept_3d_no_task_support_topology_formal/`, with 30 evaluation episodes per checkpoint-scenario for `relay_failure` and `scout_failure`.
- `scripts/analyze_3d_task_support_ablation_formal.py` produces `results/intercept_3d_task_support_ablation_formal_summary.csv` and `docs/intercept_3d_task_support_ablation_formal_summary.md`. On matched evaluation episodes, full multi-relation outperforms no-task-support on `relay_failure` success by `+0.111` with 95% CI `[+0.056, +0.178]` and reduces recovery steps by `-23.5` with 95% CI `[-37.7, -11.6]`. On `scout_failure`, success improves by `+0.089` with 95% CI `[+0.033, +0.156]` and recovery steps improve by `-18.8` with 95% CI `[-32.9, -7.0]`. This is now manuscript-level evidence for the dynamic task-support relation.
- `graph_message_ablation=no_role_pair_gate` disables learned role-pair-conditioned message gates while preserving the perception, communication, and task-support relation channels. The disabled gate uses a scale-matched constant value of `0.5`, matching the full model's zero-initialized sigmoid gate scale.
- `scripts/run_3d_role_pair_gate_ablation_protocol.py` completed the formal scale-matched no-role-pair-gate ablation for seeds `0, 1, 2` under `results/intercept_3d_no_role_pair_gate_baseline_formal_scale_matched/` and `results/intercept_3d_no_role_pair_gate_topology_formal_scale_matched/`, with 30 evaluation episodes per checkpoint-scenario for `relay_failure` and `scout_failure`.
- `scripts/analyze_3d_role_pair_gate_ablation_formal.py` produces `results/intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.csv` and `docs/intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.md`. On `relay_failure`, the full model improves success/recovery over no-role-pair-gate by `+0.044` with 95% CI `[+0.011, +0.089]` and reduces recovery steps by `-9.8` with 95% CI `[-19.2, -2.7]`. On `scout_failure`, the effect is positive but non-separated, so it should be used as supporting trend evidence only.
- `scripts/build_3d_paper_tables.py` now appends both formal task-support and formal role-pair-gate ablation sections to `docs/intercept_3d_paper_main_table.md`.
- `graph_input_ablation=no_edge_features` zeros edge features inside the actor while preserving graph dimensions and relation channels. It is now wired through 3DOF BC pretraining, PPO training, policy evaluation, topology robustness evaluation, baseline protocol, and topology protocol. The current validation is only smoke-scale: compile checks, 3DOF environment smoke, one-update no-edge training smoke, no-edge checkpoint evaluation smoke, and the full lightweight build gate all pass. No paper claim should use this ablation until a matched diagnostic or formal run is complete.
- The seed-0 no-edge diagnostic completed under `results/intercept_3d_no_edge_features_baseline_seed0_diagnostic/` and `results/intercept_3d_no_edge_features_topology_seed0_diagnostic/`. The paired diagnostic summary in `docs/intercept_3d_no_edge_features_ablation_seed0_diagnostic_summary.md` shows only a weak relay-failure degradation (`+0.033` full-minus-no-edge success delta, CI `[+0.000, +0.100]`) and no scout-failure success difference. Do not promote this to a formal three-seed ablation unless a later manuscript review specifically needs an edge-feature diagnostic.
- The original `graph_input_ablation=no_role_identity` implementation mapped every role ID to the same neutral role inside the actor but still left explicit role indicators in 3DOF local observations and graph node features. Its seed-0 diagnostic and formal three-seed run are now pre-hardening historical evidence.
- The pre-hardening formal no-role-identity ablation completed under `results/intercept_3d_no_role_identity_baseline_formal/` and `results/intercept_3d_no_role_identity_topology_formal/`. The summary in `docs/intercept_3d_no_role_identity_ablation_formal_summary.md` is retained only as diagnostic context and should not be used in the paper main table until rerun under the 2026-07-19 true no-role semantics.
- `target_policy=break_turn` adds defensive maneuvering when a blue UAV enters the target's threat zone: the target performs lateral break turns relative to the nearest pursuer and altitude changes while preserving world-boundary and altitude safety. `target_policy=weaving` adds lower-intensity sinusoidal lateral/altitude maneuvering.
- The zero-shot break-turn pilot completed under `results/intercept_3d_break_turn_node_failure_pilot/`, with paired summary in `docs/intercept_3d_break_turn_node_failure_pilot_summary.md`. Existing straight-target checkpoints were evaluated under break-turn plus relay/scout node failure. Single-graph timed out in every tested episode, while multi-relation retained nonzero success: relay failure `0.244` vs `0.000` and scout failure `0.144` vs `0.000`. Paired success deltas were `+0.244` with CI `[+0.156, +0.333]` for relay failure and `+0.144` with CI `[+0.078, +0.222]` for scout failure. This is strong scenario-depth evidence that the harder target policy has discriminative value, but the absolute success rate is too low for a main result without break-turn curriculum fine-tuning.
- A 20-update seed-0 break-turn fine-tuning pilot completed under `results/intercept_3d_break_turn_curriculum_seed0_pilot/`, but did not raise absolute success enough: multi-relation reached `0.267` on relay failure and `0.000` on scout failure; single-graph stayed at `0.000` on both.
- The zero-shot weaving pilot completed under `results/intercept_3d_weaving_node_failure_pilot/`, with paired summary in `docs/intercept_3d_weaving_node_failure_pilot_summary.md`. It behaved similarly to break-turn: multi-relation reached `0.267` relay and `0.144` scout success, while single-graph stayed at `0.000`.
- A seed-0 `weaving_mild` pilot completed under `results/intercept_3d_weaving_mild_node_failure_seed0_pilot/`. It still did not produce paper-ready absolute success: multi-relation reached `0.267` relay and `0.000` scout success; single-graph stayed at `0.000`.
- `docs/intercept_3d_maneuvering_target_pilot_summary.md` consolidates the maneuvering-target pilots. Current decision: keep maneuvering target results as scenario-depth diagnostics only. Do not promote them to the main table until a staged target-policy curriculum raises absolute success.
- `scripts/evaluate_3d_geometric_node_failure.py` evaluates the deterministic geometric pursuit demonstrator under the same relay/scout node-failure protocol. The formal run under `results/intercept_3d_geometric_node_failure_eval/` produced 180 episodes. It reached 100% success and 100% post-failure recovery in both relay and scout failure, with about `5.2` recovery steps. Because this controller uses simulator target state, it is an oracle-style demonstrator/reference rather than a fair decentralized baseline.
- `scripts/analyze_3d_compact_node_failure_baselines.py` produces `results/intercept_3d_compact_node_failure_baselines.csv` and `docs/intercept_3d_compact_node_failure_baselines.md`. The compact table places oracle geometric pursuit, single-graph MAPPO, and EA-RG-MAPPO-S under the same straight-target node-failure table. It documents baseline coverage and task difficulty, while explicitly preserving the paired single-vs-multi recovery analysis and formal ablations as the real method evidence.
- The new compact-baseline scripts compile successfully, and the full lightweight paper asset gate passed after the compact-baseline additions.
- `UAVIntercept3DConfig(strict_target_sensing=True)` now prevents local observations, shared observations, and graph target nodes/edges from falling back to true target state before a valid detection. Before first detection it uses a fixed search prior; after detection it uses the last detected target position/velocity. The default remains `False`, so all existing straight-target evidence is reproducible.
- `scripts/smoke_test_strict_target_sensing.py` verifies that forced radar dropout keeps legacy observations on true target state but strict-sensing observations and graph target nodes on the fixed prior.
- `scripts/evaluate_3d_topology_robustness.py`, `scripts/evaluate_ri_gmappo_3d.py`, `scripts/train_ri_gmappo.py`, `scripts/pretrain_ri_gmappo_3d_bc.py`, `scripts/run_3d_baseline_protocol.py`, and `scripts/run_3d_topology_curriculum_protocol.py` now expose `--strict-target-sensing`.
- A small strict-sensing node-failure screen completed under `results/intercept_3d_strict_sensing_node_failure_screen/` with 3 seeds, relay/scout failure, and 5 episodes per checkpoint-scenario. Existing topology-curriculum checkpoints remain task-capable, but single-graph reached `1.000` success on both relay/scout while multi-relation reached `0.867`. Treat this as a diagnostic showing that strict sensing needs matched retraining, not as a paper claim.
- A strict-sensing topology-curriculum pilot completed under `results/intercept_3d_strict_sensing_curriculum_seed0_pilot/`. It reused the existing node-failure curriculum checkpoints, enabled `--strict-target-sensing`, and fine-tuned single/multi checkpoints for 10 PPO updates across seeds `0, 1, 2`. The 30-episode-per-checkpoint-scenario evaluation produced 360 episodes under `formal_eval/`.
- `docs/intercept_3d_strict_sensing_curriculum_seed0_pilot_formal_eval_summary.md` summarizes the strict-sensing pilot checkpoint evaluation. Under `relay_failure`, multi-relation recovered in `0.967` of episodes versus single-graph `0.711`, giving a paired recovery delta of `+0.256` with 95% CI `[+0.156, +0.367]`, and reduced recovery steps by `-53.9` with 95% CI `[-75.3, -32.6]`. Under `scout_failure`, the result is positive but non-separated (`+0.067`, CI `[-0.056, +0.189]`). This is now a strong candidate scenario-depth result for Q2-level quality, especially because strict sensing removes target-state leakage from observations.
- `scripts/build_3d_paper_tables.py` now appends a strict-sensing scenario-depth section to `docs/intercept_3d_paper_main_table.md`. The section labels the result as a 10-update strict-sensing fine-tuning pilot, promotes only the separated relay-failure row, and keeps scout failure as a supporting trend.
- `docs/english_3d_experiments_draft.md` now converts the current 3DOF evidence stack into manuscript-ready experimental narrative. It covers the 3DOF scenario, training protocol, relay-failure recovery result, communication/sensing robustness trends, formal mechanism ablations, strict-sensing scenario-depth experiment, qualitative replay case, and claim boundaries.
- `docs/english_3d_manuscript_draft.md` now provides a full next-stage English manuscript skeleton around the 3DOF claim, including title, abstract, contributions, claim boundary, introduction, related work placeholders, problem formulation, method, experiments, discussion, conclusion, and revision checklist.
- `scripts/replay_3d_relay_failure_case.py` was updated with a default `strict_target_sensing=False` compatibility field after `evaluate_ri_gmappo_3d.build_config()` gained the new option. The relay-failure replay and the full lightweight paper asset gate both pass after the strict-sensing changes.
- `no_graph` fair source checkpoints were trained for seeds `0, 1, 2`, then a mixed-source strict-sensing fair diagnostic was completed under `results/intercept_3d_strict_sensing_fair_3seed_diag/`. Validation-selected test recovery was `100.0%` for `multi_relation`, `93.3%` for `single`, and `40.0%` for `no_graph` over three training seeds and 10 test episodes per seed. This is still a development-budget diagnostic, but it confirms that the fair baseline path is now producing a meaningful method ordering instead of all-zero recovery.
- Seed-aware hierarchical bootstrap reports were generated for the three-seed fair diagnostic. `multi_relation` vs `no_graph` showed a `+60.0 pp` recovery delta with 95% CI `[+13.3, +100.0] pp`; `multi_relation` vs `single` showed a smaller `+6.7 pp` recovery delta with CI `[+0.0, +23.3] pp`. The safe interpretation is strong evidence that graph/message structure is necessary under strict sensing, plus weaker development evidence that multi-relation roles improve recovery robustness over a single union graph.
- `docs/no_graph_source_audit_summary.md` records a 50-episode audit of the three `no_graph` source checkpoints. Seed 2 is confirmed as a genuinely weak source (`22.0%` nominal success and `0.0%` strict relay-failure success), so formal reporting should either keep all seeds as variance or retrain all `no_graph` sources with a stronger predefined budget, not selectively replace seed 2.
- `docs/fair_baseline_source_policy.md` fixes the next-step policy: keep all current `no_graph` seeds for the 30-update development diagnostic, then decide whether all `no_graph` sources need a standardized stronger retrain before the five-seed formal run.
- A 30-update strict-sensing fair checkpoint-budget diagnostic completed under `results/intercept_3d_strict_sensing_fair_30update_diag/`. Validation-selected test recovery was `95.0%` for `multi_relation`, `90.0%` for `single`, and `36.7%` for `no_graph` across three training seeds and 20 test episodes per seed. Seed-aware bootstrap gives `multi_relation - no_graph = +58.3 pp` recovery with 95% CI `[+11.6, +95.0] pp`, but `multi_relation - single = +5.0 pp` with CI `[-3.3, +13.3] pp`. This confirms the necessity of graph/message structure, but the current straight relay-failure task is too easy to strongly separate multi-relation from a single union graph.
- Three checkpoint-only harder-scenario probes were completed using the 30-update validation-selected checkpoints. `weaving_mild + relay_failure` is too hard (`multi_relation` recovery `6.7%`, `single/no_graph` `0.0%`). `range0.75 + relay_failure` remains saturated for graph methods (`multi_relation` `98.3%`, `single` `96.7%`). `radar_dropout0.10 + relay_failure` does not favor multi-relation over single (`multi_relation` `93.3%`, `single` `95.0%`). These probes show that the next quality improvement should target a better task-support dependency or a staged scenario curriculum, not arbitrary harder settings.
- A fourth checkpoint-only probe, `communication_dropout0.30 + relay_failure`, produced the best scenario-depth candidate so far: recovery was `98.3%` for `multi_relation`, `76.7%` for `single`, and `28.3%` for `no_graph`. Seed-aware bootstrap gives `multi_relation - single = +21.7 pp` with 95% CI `[+3.3, +41.7] pp`. This should become the next formal strict-sensing validation/test scenario, but it is not final paper evidence yet because checkpoint selection was still performed on the easier straight relay-failure validation split.
- `dropout030_relay_failure` was added to the shared 3DOF robustness scenario table and smoke-tested through `scripts/evaluate_3d_checkpoint_sweep.py`. `docs/dropout030_relay_strict_sensing_protocol.md` now defines the next validation/test protocol.
- The first dropout-relay formal development diagnostic completed under `results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag/`, using dropout-relay validation selection and disjoint dropout-relay test episodes. Test recovery was `93.3%` for `multi_relation`, `86.7%` for `single`, and `31.7%` for `no_graph`. Seed-aware `multi_relation - single` recovery delta was `+6.7 pp` with 95% CI `[-15.0, +33.3] pp`; `multi_relation - no_graph` was `+61.7 pp` with CI `[+0.0, +100.0] pp`. This keeps the graph-vs-no-graph claim alive, but it does not yet justify a strong multi-relation-over-single claim at the current 30-update budget.
- A 60-update dropout-relay strict-sensing diagnostic was completed for `single` and `multi_relation` under `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/`. Validation-selected test recovery was `96.7%` for `multi_relation` and `88.3%` for `single`. Seed-aware `multi_relation - single` recovery delta improved to `+8.3 pp`, but the 95% CI remained non-separated at `[-1.7, +21.7] pp`. Longer training helps slightly, but the current scenario still allows one single-graph seed to saturate, so five-seed formal expansion is premature.
- An opt-in `agent_target_info_bottleneck` switch was added and smoke-tested. In a checkpoint-only probe using the 60-update dropout-relay checkpoints, the bottleneck reduced single-graph saturation and produced the strongest current `multi_relation` vs `single` separation: recovery `95.0%` vs `78.3%`, delta `+16.7 pp` with 95% CI `[+3.3, +33.3] pp`. `docs/agent_target_info_bottleneck_protocol.md` records the protocol and next steps.
- Bottleneck-enabled validation selection and disjoint testing were completed under `results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_formal_diag/`. Test recovery was `95.0%` for `multi_relation` and `78.3%` for `single`; seed-aware `multi_relation - single` recovery delta was `+16.7 pp` with 95% CI `[+6.7, +28.3] pp`. All three training seeds show positive deltas. This is now the strongest candidate for the formal scenario-depth result.
- `no_graph` was added to the same bottleneck-enabled dropout-relay protocol after training 60-update checkpoints with the same source policy. The three-method recovery ordering is now `no_graph 25.0% < single 78.3% < multi_relation 95.0%`. Seed-aware `multi_relation - no_graph` recovery delta is `+70.0 pp` with 95% CI `[+20.0, +100.0] pp`.
- Gate 1 P0 hardening is complete for actor observation localization, target-message TTL/confidence freshness, post-step timing semantics, maintained/recovered/unrecovered recovery accounting, and strict-bottleneck graph target hiding. The old five-seed bottleneck result is retained only as pre-hardening development evidence.
- A hardened 20-update three-method, three-seed development rerun completed under `results/intercept_3d_gate1_hardened_20update_3seed_dev/`. Strict zero-collision validation selection failed because `single` seed `1` had no zero-collision eligible checkpoint. A relaxed diagnostic preserved the expected method ordering on disjoint test episodes: `no_graph` recovery `0.253 +/- 0.422`, `single` `0.467 +/- 0.397`, and `multi_relation` `0.793 +/- 0.194`. This is encouraging development evidence, not formal paper evidence. Details are recorded in `docs/intercept_3d_gate1_hardened_20update_3seed_dev_summary.md`.
- A hardened 60-update three-method, three-seed development rerun completed under `results/intercept_3d_gate1_hardened_60update_3seed_dev/`. Strict zero-collision validation checkpoint selection passed. On the disjoint test split, recovery was `no_graph 0.267 +/- 0.411`, `single 0.613 +/- 0.473`, and `multi_relation 0.853 +/- 0.070`. The result strongly favors `multi_relation` on mean recovery and seed stability, but disjoint test collision is not fully zero (`multi_relation` mean `0.007`, `single` mean `0.013`), so safety inspection is required before promoting this to formal evidence. Details are recorded in `docs/intercept_3d_gate1_hardened_60update_3seed_dev_summary.md`.
- Seed-aware hierarchical bootstrap for the hardened 60-update run separates `multi_relation` from `no_graph` on recovery (`+58.7 pp`, 95% CI `[+14.7, +90.7] pp`) but does not yet separate `multi_relation` from `single` (`+24.0 pp`, 95% CI `[-18.0, +76.7] pp`). Collision audit found three disjoint-test collision episodes, recorded in `docs/intercept_3d_gate1_hardened_60update_collision_audit.md`.
- `scripts/evaluate_ri_gmappo_3d.py` now adds explicit recovery-time semantics fields, `post_failure_chain_recovery_steps_censored` and `post_failure_chain_recovered_only_steps`, while preserving the legacy `post_failure_chain_recovery_steps` column. A one-episode evaluator smoke confirmed the new columns under `results/intercept_3d_gate1_hardened_60update_3seed_dev/field_semantics_smoke/`.
- `scripts/replay_3d_collision_cases.py` now replays disjoint-test collision episodes and writes per-step distance/action traces. The hardened 60-update collision replay found one `multi_relation` blue-blue collision (`blue0-blue2`, step `45`, `114.2 m`) and two `single` blue-target collisions (`blue0-red0`, step `55`, `31.3 m` and `103.0 m`). All occur during relay failure and show sustained unsafe approach. The replay report is `docs/intercept_3d_gate1_hardened_60update_collision_replay.md`.
- A light proximity safety auxiliary has been implemented and smoke-tested across the 3DOF environment, PPO config, training CLI, and strict-sensing formal protocol. It is disabled by default and should be treated as training support, not a claimed innovation.
- A three-method, three-seed hardened 60-update safety diagnostic is recorded in `docs/intercept_3d_gate1_hardened_60update_safety_diag_summary.md`. With `safety_proximity_distance=1000` and `safety_proximity_penalty_weight=0.3`, test recovery was `no_graph=28.0%`, `single=53.3%`, and `multi_relation=86.7%`; `multi_relation` had zero test collisions across all three seeds. Seed-aware `multi_relation - no_graph` recovery delta was `+58.7 pp` with 95% CI `[+7.3, +97.4] pp`; `multi_relation - single` recovery delta was `+33.3 pp` with 95% CI `[-0.7, +68.7] pp`.
- 3DOF evaluation outputs now include episode and final minimum blue-red / blue-blue distances, and checkpoint sweeps summarize episode-minimum distances. The safety diagnostic was re-evaluated without retraining under `results/intercept_3d_gate1_hardened_60update_safety_diag_min_distance_eval/`; `multi_relation` kept zero collisions with mean episode-min distances of `3290.2 m` blue-red and `2334.4 m` blue-blue.
- A five-seed safety-enabled hardened formal candidate completed all `15/15` training runs under `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/`. It uses seeds `0--4`, methods `no_graph`, `single`, and `multi_relation`, `60` safety-continuation PPO updates, strict target sensing, the agent target-information bottleneck, and `safety_proximity_distance=1000`, `safety_proximity_penalty_weight=0.3`. Source checkpoints come from `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/.../actor_critic_latest.pt`.
- Validation checkpoint selection for the five-seed safety candidate remains expensive and repeatedly stalled. The practical fixed-final-checkpoint diagnostic under `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/` is complete.
- The fixed-update-60 five-seed safety diagnostic is recorded in `docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md`. On 1500 matched test episodes, recovery was `no_graph=21.8%`, `single=53.2%`, and `multi_relation=88.6%`; `multi_relation` had zero collisions. Seed-aware recovery delta was `+35.4 pp` versus `single` with 95% CI `[+1.2, +73.0] pp`, and `+66.8 pp` versus `no_graph` with 95% CI `[+28.6, +93.8] pp`.
- Fixed-update-60 failure-aligned mechanism evidence is complete under `results/gate1_safety_fx60_mechanism/` and documented in `docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md`. It includes weighted full-test mechanism curves from all five training seeds and a predefined median-positive-difference representative case.
- The first fixed-update-60 hardened safety ablation, `no_task_support`, is complete and recorded in `docs/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_summary.md`. Matched recovery was `64.8%` versus full `multi_relation` `88.6%`; the seed-aware recovery delta was `+23.8 pp` but the 95% CI `[-9.2, +63.6] pp` crosses zero, so this should be treated as supportive but not decisive mechanism evidence.
- The second fixed-update-60 hardened safety ablation, `no_role_pair_gate`, is complete and recorded in `docs/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_summary.md`. Matched recovery was `64.8%` versus full `multi_relation` `88.6%`; the seed-aware recovery delta was `+23.8 pp` with 95% CI `[+2.8, +59.2] pp`, so this is the stronger current mechanism ablation.
- Paper-facing fixed-update-60 result tables are generated in `docs/gate1_safety_fx60_paper_tables.md` and `results/gate1_safety_fx60_paper_tables/`. The package includes main comparison, mechanism ablations, seed-aware deltas, and LaTeX table fragments.
- `no_curriculum` was reopened as a high-standard contribution-risk check. A seed-0 fixed full-difficulty no-curriculum diagnostic is recorded in `docs/gate1_safety_fx60_no_curriculum_seed0_dev60_summary.md`. On the matched 30-episode validation diagnostic, no-curriculum reached `70.0%` recovery at fixed update 60 versus `63.3%` for the original topology-curriculum seed-0 checkpoint, both with zero collision. This means topology curriculum should not be claimed as an independently proven main contribution yet; it remains a training protocol unless a three-seed/five-seed ablation proves otherwise.
- The no-curriculum check has been upgraded to a three-seed development diagnostic, recorded in `docs/gate1_safety_fx60_no_curriculum_3seed_dev60_summary.md`. Validation-selected recovery is effectively tied (`88.9%` no-curriculum versus `87.8%` topology curriculum), and fixed-update-60 slightly favors curriculum (`85.6%` versus `87.8%`) but only by `2.2 pp`. Both have zero diagnostic collisions. Decision: do not spend a five-seed formal budget on no-curriculum now, and do not list topology curriculum as a primary contribution.
- Seed-level mechanism figures are generated by `scripts/plot_gate1_safety_fx60_seed_mechanism.py` and documented in `docs/gate1_safety_fx60_seed_mechanism_summary.md`. The package includes main method seed scatter, paired mechanism-ablation seed deltas, and a seed-aware bootstrap forest plot. It reinforces the current claim boundary: full multi-relation improves seed-level reliability; role-pair gating is the cleanest mechanism ablation; task-support relation is supportive but not decisive.
- A small graph-relation stressor, `dropout030_scout_failure`, has been added to the 3DOF robustness scenario registry and evaluated with frozen fixed-update-60 checkpoints. The 5-seed, 20-episode diagnostic is recorded in `docs/gate1_safety_fx60_dropout030_scout_failure_diag20_summary.md`: recovery is `no_graph=24.0%`, `single=51.0%`, and `multi_relation=76.0%`; full multi-relation has zero diagnostic collisions. Seed-aware full-vs-single recovery delta is `+25.0 pp` but the interval crosses zero, so this is a useful stressor screen rather than formal evidence.
- The sharper accelerated stressor `dropout030_delay2_scout_failure` is complete and recorded in `docs/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20_summary.md`. It adds two-step message delay to dropout scout failure. Recovery is `no_graph=37.0%`, `single=56.0%`, and `multi_relation=85.0%`; full multi-relation has the lowest variance and zero collisions. Full-vs-single recovery delta is `+29.0 pp` but the 95% CI `[-5.0, +70.0] pp` still crosses zero; tracking separates in favor of full. Decision: stop adding more small stressors and move to finish mode.
- A paper-facing English experiment-section draft for the fixed-update-60 3v1 strict-sensing relay-failure package is available at `docs/gate1_safety_fx60_experiment_section_draft.md`.
- The fixed-update-60 experiment section has been integrated into `paper_latex_3d_en/sections/05_experiments.tex`; `paper_latex_3d_en/main.tex` abstract now matches the five-seed fixed-budget evidence. Mechanism figures were copied into `results/figures/` for the LaTeX graphic path.
- Active 3D manuscript consistency audit is recorded in `docs/gate1_safety_fx60_manuscript_consistency_audit.md`. Introduction and method wording were revised so curriculum is treated as a training protocol rather than a standalone proved contribution; strict sensing now matches the five-seed fixed-budget result rather than a pilot.
- Contribution-to-evidence alignment is recorded in `docs/gate1_safety_fx60_contribution_evidence_alignment.md`. The introduction contribution list now uses the same three-contribution wording.
- Method-component audit is recorded in `docs/gate1_safety_fx60_method_component_audit.md`. The problem section now defines post-failure recovery, recovery steps, tracking during failure, and chain-closed rate during failure; the method section now includes multi-relation role-pair message-passing equations and the MAPPO clipped objective.
- `scripts/merge_checkpoint_sweep_shards.py` has been added and compile-validated. It merges per-seed checkpoint-sweep shards, deduplicates rows, preserves episode-level metric columns, and regenerates selected checkpoint CSVs using the standard checkpoint-selection logic.
- `scripts/run_3d_strict_sensing_formal_protocol.py` and `scripts/evaluate_3d_checkpoint_sweep.py` now propagate graph relation/message/input ablation switches so fixed-protocol ablations can be evaluated consistently.
- `scripts/evaluate_ri_gmappo_3d.py` and `scripts/evaluate_3d_checkpoint_sweep.py` now support `--eval-batch-size` for batched episode evaluation. A smoke comparison confirmed identical key episode metrics for `eval_batch_size=1` and `5`.
- The active English manuscript related-work section has been strengthened with recent communication-limited MADRL, robust graph communication, air-combat DRL review, graph-convolutional air-combat decision learning, and GNN-based air-combat references. Citation audit found no missing or unused BibTeX keys.
- `scripts/report_3d_model_costs.py` now generates the baseline-credibility cost package under `results/gate1_safety_fx60_model_costs/` and `docs/gate1_safety_fx60_model_cost_report.md`. Current CPU report: full EA-RG-MAPPO-S has `389745` total parameters and `4.1432 ms` batch-1 actor latency, versus single-graph `124017` parameters and `1.2322 ms`.
- `scripts/report_3d_model_costs.py` now includes a parameter-matched single-graph baseline specification. `hidden_dim=240` gives `394913` total parameters for `Single-graph MAPPO (param-matched)`, close to full EA-RG-MAPPO-S at `390385` total parameters after role-conditioned critic hardening. The plan is recorded in `docs/parameter_matched_single_graph_baseline_plan.md`.
- A seed-0 parameter-matched single-graph development diagnostic is complete and recorded in `docs/parameter_matched_single_graph_seed0_dev_summary.md`. The hidden-240 single-graph baseline trained through BC, nominal PPO, topology curriculum, and strict bottleneck fine-tuning. On a 10-episode matched `dropout030_relay_failure` test split, parameter-matched single recovered `10.0%` versus full fixed-update-60 reference `90.0%`. This is development evidence only, but it supports expanding the capacity-control baseline to three seeds.
- The model-cost LaTeX table is integrated into `paper_latex_3d_en/sections/05_experiments.tex`, and the recursive static manuscript check passes with no missing citations, unused BibTeX keys, missing references, missing inputs, missing graphics, or duplicate labels.
- PDF-readiness static audit is recorded in `docs/gate1_safety_fx60_pdf_readiness_audit.md`. The main result, ablation, bootstrap, and model-cost LaTeX tables now use page-width resize protection.
- Failure-timing generalization scenarios are registered in `scripts/evaluate_3d_topology_robustness.py`: early/nominal/late relay failure with and without 0.30 communication dropout. A one-episode smoke evaluation passed for `dropout030_relay_failure_early`; the formal protocol is recorded in `docs/gate1_safety_fx60_failure_timing_generalization_protocol.md`.
- A 5-episode-per-seed timing diagnostic is recorded in `docs/gate1_safety_fx60_failure_timing_generalization_combined_diag5_summary.md`. Early relay failure preserves the method ordering (`no_graph 28.0%`, `single 48.0%`, `multi_relation 76.0%` recovery), while delayed/late failure has invalid failure-window coverage for the full method because many episodes terminate before the failure window. Current decision: formal timing generalization should focus on early versus nominal relay failure only.
- The fixed-checkpoint early-vs-nominal failure-timing generalization formal evaluation is complete and deduplicated under `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/`: 3 methods, 5 seeds, 2 scenarios, 100 matched episodes per seed, 3000 total episodes. Formal evidence is recorded in `docs/gate1_safety_fx60_failure_timing_generalization_formal_evidence.md`. Early relay failure recovery is `no_graph=23.2%`, `single=46.6%`, `multi_relation=88.2%`; seed-aware full-vs-single recovery delta is `+41.6 pp` with 95% CI `[+4.4, +78.6] pp`.
- The timing-generalization result is integrated into `paper_latex_3d_en/sections/05_experiments.tex` via `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_generalization_latex.tex`. Recursive LaTeX static check passes with five resized paper-facing tables and no missing citations/references/labels.
- `scripts/build_gate1_safety_fx60_paper_tables.py` now regenerates the failure-timing generalization section and artifact links in `docs/gate1_safety_fx60_paper_tables.md`, so rerunning the paper-table packager no longer drops the timing table.
- `scripts/write_submission_readiness_report.py` has been migrated from the old 2D readiness scope to the current 3DOF Gate 1 manuscript package. `docs/submission_readiness_report.md` now reports the hardened 3DOF relay-failure recovery claim, the fixed-update-60 main evidence, and the current unresolved runtime limitation: no LaTeX toolchain is available for visual PDF rendering in this environment.
- `scripts/audit_english_manuscript_readiness.py` and `scripts/write_submission_package_manifest.py` now target the current `paper_latex_3d_en/` Gate 1 manuscript package instead of the older `paper_latex_en/` route. The regenerated readiness audit reports zero hard errors; the package manifest now lists the current 3D Gate 1 tables and figures.
- The Q1 three-stage execution plan is recorded in `docs/Q1_THREE_STAGE_EXECUTION_PLAN.md`: Gate 1 package closure, formal `nominal weaving_mild`, then one small realism supplement.
- The formal `nominal weaving_mild` scenario-depth protocol is frozen in `docs/nominal_weaving_mild_frozen_protocol.md`. It requires equal oracle-assisted training for `no_graph`, `single`, and `multi_relation`, validation/test separation, seed-aware statistics, and a new formal test split rather than further tuning on the existing `409000` development split.
- `scripts/run_3d_nominal_weaving_mild_formal_protocol.py` implements the frozen Stage 2 protocol. A one-method, one-seed smoke passed and is recorded in `docs/nominal_weaving_mild_formal_protocol_smoke_summary.md`.
- The Stage 2 three-seed frozen-protocol run is complete and recorded in `docs/nominal_weaving_mild_formal_protocol_3seed_summary.md`. The hierarchy remains `no_graph < single < multi_relation`, but `multi_relation` reaches only `42.7%` success and seed 1 remains almost unsolved, so the run does not pass the predefined acceptance gate and should not be expanded to seeds `3` and `4` yet.
- The final single-paper scope is recorded in `docs/FINAL_SINGLE_PAPER_SCOPE.md`. The paper target is a Q2-level minimum with Q1 stretch, centered on Gate 1 strict-sensing relay-failure recovery rather than broad system expansion.
- Parameter-matched single-graph capacity-control development is extended to three seeds in `docs/parameter_matched_single_graph_3seed_dev_summary.md`. On the small matched strict bottleneck split, full multi-relation recovers `93.3%` versus parameter-matched single-graph `3.3%`, with seed-level recovery deltas of `+80.0`, `+90.0`, and `+100.0` percentage points. This supports the structural baseline argument but remains development evidence until the training budget and test episodes are formalized.
- A fairer parameter-matched single-graph update-60 development extension is complete in `docs/parameter_matched_single_graph_update60_dev_summary.md`. With three seeds and 20 test episodes per seed, parameter-matched single recovers `18.3%` versus full multi-relation `88.3%` on the same test split. The longer budget improves seed 0 but does not close the structural gap.
- The parameter-matched single-graph capacity-control baseline has been extended to a five-seed test50 formal candidate in `docs/parameter_matched_single_graph_5seed_test50_candidate_summary.md`. On 50 independent test episodes per seed, full multi-relation recovers `89.2%` versus parameter-matched single-graph `33.2%`, both with zero collisions. Seed-level results show high single-graph variance: seeds `0` and `4` are competitive, while seeds `1`, `2`, and `3` nearly fail.
- Seed-aware hierarchical bootstrap for the five-seed parameter-matched capacity-control candidate is complete. Recovery delta is `+56.0 pp` with 95% CI `[+11.2, +98.8] pp`; tracking, connectivity, chain closure, timeout, and restricted recovery-time intervals also separate in favor of full multi-relation.
- The parameter-matched capacity-control result is integrated into the paper table package in `docs/gate1_safety_fx60_paper_tables.md` and `results/gate1_safety_fx60_paper_tables/`, including standalone CSV and LaTeX tables.
- `run_3d_fair_staged_source_protocol.py` now passes `--graph-input-ablation` through BC, nominal PPO, topology curriculum, and strict smoke, enabling fair staged-source training for input ablations.
- Hardened true `no_role_identity` three-seed dev20 rerun is complete in `docs/true_no_role_identity_hardened_3seed_dev20_summary.md`. Recovery is `20.0%` versus full same-split reference `93.3%`; this is strong development evidence that explicit role identity matters, but not yet a formal manuscript table.
- Evaluation metrics now handle episodes that terminate before the configured failure start: failure-window rates are `0.0` rather than `-1.0` when no active failure samples exist. Gate 1 regression coverage was added.
- Hardened true `no_role_identity` five-seed formal test50 candidate is complete in `docs/true_no_role_identity_hardened_5seed_formal_test50_summary.md`. Recovery is `56.8%` versus full matched reference `87.2%`; seed-aware recovery delta is `+30.4 pp` with 95% CI `[+7.2, +64.4] pp`. This is now usable paper-facing mechanism evidence for explicit role identity, with the caveat that no-role can still solve some seeds.
- The hardened role-identity formal result is integrated into `docs/gate1_safety_fx60_paper_tables.md` and `results/gate1_safety_fx60_paper_tables/` as standalone role-identity CSV and LaTeX tables.
- First scenario-depth diagnostic is complete in `docs/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20_summary.md`. Zero-shot fixed straight-target checkpoints transfer poorly to `weaving_mild`: full multi-relation recovers `11.0%`, single `0.0%`, and no_graph `2.0%`. This is too hard for a main table without weaving-specific training.
- Weaving-specific strict relay-failure fine-tuning is complete in `docs/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20_summary.md`. Direct 20-update adaptation from straight-target checkpoints gives `0.0%` recovery for both `single` and `multi_relation`, so the strict weaving-failure setting is not ready for formal reporting.
- Nominal `weaving_mild` feasibility evaluation is complete in `docs/gate1_safety_fx60_weaving_mild_nominal_feasibility_diag20_summary.md`. Without strict sensing or node failure, straight-target checkpoints achieve `21.7%` success for `multi_relation` and `0.0%` for `single`; this shows weak feasibility but also confirms that staged target-policy adaptation is required before adding relay failure.
- Stage 1 nominal `weaving_mild` fine-tuning from mature straight-target checkpoints is complete in `docs/gate1_safety_fx60_weaving_mild_stage1_nominal_finetune_dev20_summary.md`. Correct `hidden_dim=64` checkpoint-compatible fine-tuning gives `multi_relation=26.7%` success and `single=0.0%` on the disjoint nominal weaving test split. This supports the staged scenario-depth route but is not strong enough to enter strict-sensing Stage 2.
- Stage 1 nominal `weaving_mild` 60-update extension is complete in `docs/gate1_safety_fx60_weaving_mild_stage1_nominal_finetune_dev60_summary.md`. Longer fine-tuning does not solve the adaptation problem: validation-selected test success is `24.7%`, with seed 1 still at `0.0%`.
- `weaving_tiny` has been added as an opt-in lower-amplitude target-policy curriculum entry. Zero-shot evaluation is recorded in `docs/gate1_safety_fx60_weaving_tiny_zero_shot_diag30_summary.md`: `multi_relation` reaches `28.9%` and `single` remains `0.0%`, but seed 1 still fails across source snapshots `10` through `60`.
- Target-policy curriculum execution is implemented in `scripts/run_3d_target_policy_curriculum.py` and smoke-tested in `docs/gate1_target_policy_curriculum_smoke_summary.md`. The smoke validates `straight source -> weaving_tiny -> weaving_mild` checkpoint chaining and final evaluator compatibility.
- A real three-seed target-policy curriculum diagnostic is complete in `docs/gate1_target_policy_curriculum_multi_3seed_dev30x2_summary.md`. The `weaving_tiny -> weaving_mild` curriculum reaches `27.3%` test success with zero collisions, but seed 1 remains `0.0%`, so maneuvering-target scenario depth is still not ready for strict sensing or relay failure.
- Opt-in attack-geometry reward shaping is implemented and tested. The seed-1 diagnostic in `docs/gate1_target_policy_curriculum_seed1_geometry_shaping_diag.md` used `attack_geometry_reward_weight=0.15` but still produced `0.0%` seed-1 success, so the next step should be trajectory/reachability analysis rather than more reward weight scaling.
- Maneuvering-target reachability analysis is complete in `docs/gate1_maneuver_reachability_curriculum_3seed_eval30_summary.md`. Seed 1 reduces range by about `11.9 km`, similar to the successful/partly successful seeds, but never forms attack windows and never reaches attack-geometry score `> 0.25`. The current blocker is therefore attack-geometry conversion, not basic approach or collision. The next step is a deterministic geometric-oracle reachability check before spending more PPO training budget.
- Deterministic geometric-oracle reachability is implemented in `scripts/analyze_3d_geometric_oracle_reachability.py` and documented in `docs/gate1_geometric_oracle_reachability_eval30_summary.md`. On matched 30-episode nominal evaluations, the lead/offset oracle achieves `100%` success and `0%` collision on `weaving_mild`; direct pursuit reaches only `66.7%` success with `36.7%` collision. This proves the scenario is feasible and shifts the next learning task toward oracle-assisted maneuvering-target Stage 1 training.
- Oracle-BC support is added to `scripts/pretrain_ri_gmappo_3d_bc.py` via `--geometric-policy-mode` and optional `--attacker-action-weight`. Seed-1 diagnostics are documented in `docs/gate1_oracle_bc_weaving_mild_seed1_dev_summary.md`: ordinary BC still fails, while attacker-weighted offset BC creates the first nonzero seed-1 attack-window/success signal (`3.3%`) with zero collision. The next step is a small oracle-BC + PPO development run, not a formal multi-seed budget.
- A seed-1 oracle-BC + PPO dev10 diagnostic is complete in `docs/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10_summary.md`. Short PPO fine-tuning improves nominal `weaving_mild` seed-1 success from the curriculum-only `0.0%` and pure oracle-BC `3.3%` to `13.3%`, with zero collision. The route is promising but still below the maneuvering-target acceptance gate; next step is a cautious 20-40 update continuation or checkpoint sweep, not a three-seed formal run.
- Seed-1 oracle-BC + PPO continuation is complete in `docs/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30_summary.md`. The best/update30 checkpoint reaches `40.0%` nominal `weaving_mild` success and `40.0%` attack-window formation on 30 matched test episodes, with zero collision. This clears the seed-1 development threshold and justifies expanding the oracle-assisted route to seeds 0 and 2.
- Three-seed oracle-assisted nominal `weaving_mild` development is complete in `docs/gate1_oracle_bc_ppo_weaving_mild_3seed_dev30_summary.md`. The route reaches `62.2%` aggregate success and `64.4%` attack-window formation with zero collisions across seeds 0/1/2, improving over the previous curriculum-only `27.3%`. This passes the Stage 1 maneuvering-target development gate, but formal use requires fair oracle-assisted baselines.
- A fair oracle-assisted `single` graph seed-1 control is complete in `docs/gate1_oracle_bc_ppo_weaving_mild_single_seed1_control_summary.md`. Under the same offset-BC, attacker weighting, PPO budget, and matched test split, `single` remains at `0.0%` success while `multi_relation` reaches `40.0%`. This supports the claim that the maneuvering-target improvement is not only from oracle training assistance.
- The three-seed fair oracle-assisted `multi_relation` versus `single` comparison is complete in `docs/gate1_oracle_bc_ppo_weaving_mild_multirelation_vs_single_3seed_dev30_summary.md`. Under equal oracle-BC and PPO budgets, `multi_relation` reaches `62.2%` success versus `single` `11.1%`, with a `+51.1 pp` success gap and zero collisions for both. This is now the strongest maneuvering-target scenario-depth development evidence, but it still needs validation/test protocol hardening before paper use.
- Nominal `weaving_mild` validation-selected protocol hardening is complete in `docs/gate1_nominal_weaving_mild_validation_selected_protocol_dev10_summary.md`. Validation uses base seed `509000` and 10 episodes per checkpoint; frozen selected checkpoints are then evaluated on the existing `409000` test split with 30 episodes. Test success is `63.3%` for `multi_relation` versus `11.1%` for `single`, with zero collisions and a `+52.2 pp` success gap. This upgrades the maneuvering-target result from raw development evidence to validation-selected development evidence.
- The `no_graph` oracle-assisted maneuvering-target control is complete in `docs/gate1_nominal_weaving_mild_no_graph_control_summary.md`. Under the same validation-selected protocol, `no_graph` reaches `0.0%` success and `0.0%` attack-window formation, while `single` reaches `11.1%` and `multi_relation` reaches `63.3%`. This establishes a clean `no_graph < single < multi_relation` method hierarchy for nominal `weaving_mild`.

## Next Recommended Task

Next task: finish mode. Freeze the current evidence set and organize the manuscript package around the fixed-update-60 main result, mechanism ablations, capacity-control baseline, timing generalization, no-curriculum boundary, seed-level mechanism figures, and delayed scout-failure stressor as supplemental scenario-depth evidence. Do not add more stressors unless a specific reviewer-critical gap remains.

Current dev-1M paper-protocol track: all four seed-0 methods reached 3907
updates and completed validation checkpoint selection on the strict-sensing
relay-failure task with 50 matched episodes per checkpoint. Validation-selected
success/recovery are: EA-RG-MAPPO `0.94/0.94` at update 1600, Single-Graph
MAPPO `0.82/0.82` at update 3907, MAPPO/no-graph `0.62/0.62` at update 3800,
and HAPPO `0.14/0.14` at update 900; all selected checkpoints have zero
collisions. The consolidated summary is in
`docs/dev1m_seed0_validation_selection_summary.md` and
`results/paper_config_runs/dev_1m/checkpoint_sweeps/seed0_validation_selected_summary.csv`.
The held-out test split is also complete for seed 0 using 100 matched episodes
and base seed `220000`: EA-RG-MAPPO reaches `0.89` success/recovery,
Single-Graph MAPPO `0.80`, MAPPO/no-graph `0.60`, and HAPPO `0.08`, all with
zero collisions. This preserves the validation ordering and is the strongest
current seed-0 evidence. Detailed test results are in
`docs/dev1m_seed0_heldout_test_summary.md` and
`results/paper_config_runs/dev_1m/test_eval/seed0_heldout_test_summary.csv`.
Next, launch seeds 1/2 unchanged and repeat validation selection plus held-out
testing before making paper-level claims.

Seeds 1 and 2 are now fully trained for EA-RG-MAPPO, Single-Graph MAPPO,
MAPPO/no-graph, and HAPPO under the unchanged `dev_1m` protocol. All eight new
runs reached update 3907 and passed the training-output audit; the training log
summary is in `results/dev1m_seed1_seed2_3907update_summary.csv`. Next, run
validation checkpoint selection for seeds 1/2, then held-out test evaluation
before making multi-seed paper-level claims.

EA-RG-MAPPO seeds 1/2 validation checkpoint selection is complete. Seed 1
selects update 2200 with `0.34` success/recovery, `9.41176` mean recovery steps,
and zero collision. Seed 2 selects update 3800 with `0.48` success/recovery,
`25.25` mean recovery steps, and zero collision. Both seeds are substantially
weaker than seed 0, so this is a main-method stability warning. Do not interpret
it in isolation: the next step is to run the identical seeds 1/2 validation
selection for Single-Graph MAPPO, MAPPO/no-graph, and HAPPO before deciding
whether the relative advantage holds or whether a controlled training-protocol
adjustment is needed.

Single-Graph MAPPO seeds 1/2 validation checkpoint selection is complete under
the same protocol. Seed 1: the existing selection score chooses
update 40 with `0.04` success/recovery and zero collision, while the highest
observed validation success/recovery across its 50 checkpoints is `0.24`. Seed 2:
the selection score chooses update 40 with `0.44` success/recovery, `23.4545`
mean recovery steps, and zero collision, which is also its best observed
success/recovery. After all validation sweeps are complete, review whether the
current selection score is over-penalizing slow recovery relative to
success/recovery probability before freezing held-out test checkpoints.

MAPPO/no-graph and HAPPO seeds 1/2 validation checkpoint selection is complete.
The consolidated 3-seed validation summary is in
`docs/dev1m_validation_all_methods_seed0_2_summary.md`. Selected-checkpoint
mean success/recovery over seeds 0/1/2 is: EA-RG-MAPPO `0.5867`, MAPPO/no-graph
`0.5333`, Single-Graph MAPPO `0.4333`, and HAPPO `0.1200`. EA-RG-MAPPO remains
the best mean method, but the margin over MAPPO/no-graph is only `+0.0534` and
MAPPO/no-graph seed 1 reaches `0.98` success/recovery with zero collision. This
is a major scientific warning. Before held-out test claims, audit the no-graph
actor information boundary and reassess whether the current strict-sensing
relay-failure task is too easy or too seed-sensitive for the planned graph-centric
main claim.

A first no-graph boundary audit found no obvious actor-side target-information
leak in the inspected path: the no-graph actor branch zeros graph features and
intent context, and target cache propagation is tied to direct sensing plus
communication reachability. The existing Gate 1 information-boundary test also
passed (`24 passed` in `tests/test_gate1_communication_feasibility.py`). Current
interpretation: the no-graph seed-1 spike is more likely scenario solvability and
seed sensitivity than an obvious implementation leak. The next evidence step is
held-out testing of the already selected checkpoints, followed by a harder
stress condition if no-graph remains competitive.

Held-out testing for seeds 0/1/2 is complete and documented in
`docs/dev1m_heldout_all_methods_seed0_2_summary.md`. Test mean success/recovery
is: EA-RG-MAPPO `0.5233`, MAPPO/no-graph `0.5100`, Single-Graph MAPPO `0.4667`,
and HAPPO `0.0933`. EA-RG-MAPPO remains the best mean method, but the advantage
over MAPPO/no-graph is only `+0.0133`; MAPPO/no-graph seed 1 transfers to the
test split with `0.93` success/recovery and zero collision. Decision: the current
dev-1M strict-sensing relay-failure scenario is useful development evidence but
is not strong enough as the final sole main experiment. Move the main evidence
route to a harder stress condition, starting with `dropout030 + relay_failure +
strict_target_sensing + bottleneck`, then adding message delay or earlier relay
failure if needed.

The first `dropout030_relay_failure` stress test using nominal validation-selected
checkpoints is complete and documented in
`docs/dev1m_dropout030_relay_failure_stress_test_seed0_2_summary.md`. Mean
success/recovery over seeds 0/1/2 is: EA-RG-MAPPO `0.3000`, MAPPO/no-graph
`0.1533`, Single-Graph MAPPO `0.1300`, and HAPPO `0.1133`. This is a better
scenario candidate because the EA-vs-no-graph margin increases to `+0.1467` and
the no-graph seed-1 spike drops from `0.93` to `0.38`. However, EA seed 2 remains
weak (`0.04`) and has a small collision rate (`0.01`), so the next step is not
final reporting. Run validation checkpoint selection directly under
`dropout030_relay_failure`, then run held-out stress testing from those
stress-selected checkpoints.

Stress validation selection under `dropout030_relay_failure` is complete and
documented in
`docs/dev1m_dropout030_relay_failure_stress_validation_selection_summary.md`.
The result reverses the earlier stress-test optimism: selected-checkpoint mean
success/recovery is MAPPO/no-graph `0.4733`, Single-Graph MAPPO `0.4133`,
EA-RG-MAPPO `0.3400`, and HAPPO `0.1400`. Therefore `dropout030_relay_failure`
is not strong enough as the final main stress scenario. The next route should
increase direct dependence on communication-mediated information recovery,
preferably by adding `dropout030_delay2_relay_failure` and then, if needed,
`dropout030_delay2_relay_failure_early`.

`dropout030_delay2_relay_failure` scenario definitions were added to
`scripts/evaluate_3d_topology_robustness.py` on 2026-07-28. The script now
supports normal, early, late, and delayed relay-failure variants with 30%
communication dropout and 2-step message delay. A direct import check confirmed
all four scenarios are registered with the intended parameters. One-checkpoint
smoke evaluations under `dropout030_delay2_relay_failure` passed for both the
regular checkpoint-sweep path and the HAPPO checkpoint-sweep path, writing outputs
under `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_smoke/`
and `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_happo_smoke/`.
Next, run validation checkpoint selection for MAPPO/no-graph, Single-Graph
MAPPO, EA-RG-MAPPO, and HAPPO under `dropout030_delay2_relay_failure`. If
no-graph still remains competitive, repeat the same selection under
`dropout030_delay2_relay_failure_early`.

Validation checkpoint selection under `dropout030_delay2_relay_failure` is
complete and documented in
`docs/dev1m_dropout030_delay2_relay_failure_validation_selection_summary.md`.
Selected-checkpoint mean success/recovery over seeds 0/1/2 is: EA-RG-MAPPO
`0.5600`, Single-Graph MAPPO `0.5600`, MAPPO/no-graph `0.4733`, and HAPPO
`0.1867`, all with zero selected-checkpoint collision rate. This scenario is
better than nominal for suppressing no-graph, but it still does not prove the
multi-relation graph advantage over Single-Graph MAPPO. Do not promote it to the
final main held-out scenario yet. Next, run identical validation selection under
`dropout030_delay2_relay_failure_early`.

Because repeated stress-scenario screening still does not give a stable
EA-RG-MAPPO advantage over Single-Graph MAPPO, the project has shifted from
further scenario search to method strengthening. An optional actor-side
kill-chain auxiliary learning head was added and documented in
`docs/chain_auxiliary_learning_update.md`. The new `--chain-aux-coef` argument
defaults to `0.0`, so existing experiments are unchanged unless explicitly
enabled. The auxiliary head predicts actor-visible graph states
(`perception_active`, `communication_connected`, `task_support_active`,
`attack_window_active`, and `fresh_message_available`) and does not use held-out
test outcomes or global attack-hold progress. A 1-update 3DOF smoke training run
passed, and Gate 1 actor information-boundary tests still pass (`24 passed`).
Next, run a controlled development comparison between original EA-RG-MAPPO and
EA-RG-MAPPO + Chain Auxiliary before deciding whether to launch another full
1M/2M formal training batch.

The first chain-auxiliary Stage-A development comparison is complete and
documented in `docs/chain_aux_dev100_training_summary.md`. Both original
EA-RG-MAPPO and EA-RG-MAPPO + Chain Auxiliary completed 100 updates for seeds
0/1/2. The auxiliary head learned its graph labels well
(`~0.934` mean final auxiliary accuracy), but `chain_aux_coef=0.05` hurt short
policy learning: mean final online success was `0.3333` for original EA and
`0.0000` for EA + Chain Auxiliary, using only 5 online eval episodes. Decision:
do not launch 1M with `chain_aux_coef=0.05`. A safer candidate has been
implemented: `chain_aux_coef=0.02` with `chain_aux_warmup_updates=20`, plus
`chain_aux_effective_coef` logging. Help/config/smoke checks passed, and Gate 1
information-boundary tests still pass (`24 passed`). Next, run a second 100-update
comparison for this safer auxiliary candidate before any 1M launch.

The second chain-auxiliary Stage-A comparison is complete and documented in
`docs/chain_aux_dev100_warmup_training_summary.md`. The safer candidate
(`chain_aux_coef=0.02`, `chain_aux_warmup_updates=20`) completed seeds 0/1/2
without non-finite values, and the warm-up behaved correctly. However, online
success remained weaker than original EA-RG-MAPPO: mean final success was
`0.0000` for the warm-up auxiliary version versus `0.3333` for original EA in
the 100-update diagnostic. Mean best online success improved from `0.0667` for
the earlier auxiliary run to `0.1333`, but it remains below original EA's
`0.4000`. Decision: do not launch 1M with the current chain auxiliary
implementation. Keep original EA-RG-MAPPO as the main method for now. Next route
is role-pair gate and task-support relation diagnostics/optimization.

Role-graph mechanism diagnostics have been added and documented in
`docs/role_graph_gate_diagnostics_update.md`. The new
`scripts/diagnose_role_graph_usage.py` script writes relation-attention and
role-pair-gate CSV/MD outputs. Diagnostics on dev-1M EA validation-selected
checkpoints under `dropout030_delay2_relay_failure` show that the role-pair gates
are effectively neutral: average gate deviation from 0.5 is only `0.000154`, and
max deviation is about `0.002548`. This means the current model uses the
multi-relation graph structure, but role-pair-conditioned message passing is not
yet strongly learned. A default-off candidate fix was implemented:
`--role-gate-prior-strength`, with a new config
`configs/paper/ea_rg_mappo_gate_prior.yaml` using strength `0.4`. Smoke training,
diagnostics, config audit, and Gate 1 information-boundary tests passed. Next,
run a 100-update EA-RG-MAPPO + Role-Gate Prior development comparison before any
1M/2M launch.

HAPPO baseline protocol compatibility has been repaired for the current strong
post-loss recovery experiments. `scripts/train_happo_baseline.py` now exposes
the same critical knobs used by the EA/Single/MAPPO strong protocol: PPO clip,
PPO epochs, max grad norm, fixed online eval seed, random node-failure start and
duration windows, minimum success step, post-loss chain reclosure bonus, and
safety proximity terms. `scripts/evaluate_happo_3d.py` and
`scripts/evaluate_happo_checkpoint_sweep.py` now pass `min_success_step` through
the evaluation path. HAPPO's action/value interface was also updated to return a
dummy chain-auxiliary tensor so it remains compatible with the shared rollout
collector. Py-compile, 1-update HAPPO training smoke, and one-checkpoint HAPPO
sweep smoke all passed. Next, run HAPPO under the same strong recovery protocol
for seeds 0/1/2, then compare it against EA, Single-Graph, and no-graph using
the same checkpoint-selection rule.

HAPPO behavior cloning has also been added and documented in
`docs/happo_strong_protocol_bc_update.md`. The new
`scripts/pretrain_happo_3d_bc.py` reuses the existing 3DOF geometric teacher and
demonstration collection, then trains HAPPO's independent actors on the same
balanced offset demonstrations used by the other methods. A HAPPO BC smoke and a
BC-initialized 1-update PPO smoke both passed, with all 84 HAPPO tensors loaded
from the BC checkpoint. The next HAPPO comparison should therefore use BC +
PPO, not random initialization.

The HAPPO BC + PPO development comparison for seeds 0/1/2 is complete and
documented in `docs/happo_strong_protocol_comparison_summary.md`. With the same
strong recovery protocol and suite-level checkpoint selection, HAPPO selected
mean success/recovery/delayed-recovery/collision is
`0.167/0.258/0.083/0.017`. HAPPO is therefore a useful external MARL baseline,
but it remains weaker than EA, Single-Graph, and MAPPO/no-graph in this
development setting. Next, merge the four-method strong-protocol comparison
table and then decide whether to launch longer 1M/2M runs immediately or first
run the role-gate prior 100-update diagnostic.

The four-method strong-protocol comparison table is now documented in
`docs/strong_protocol_four_method_comparison.md`. Development validation means
are: EA-RG-MAPPO `0.625/0.717/0.342/0.000`
(success/recovery/delayed/collision), Single-Graph MAPPO
`0.675/0.783/0.358/0.008`, MAPPO/no-graph `0.383/0.517/0.333/0.008`, and HAPPO
`0.167/0.258/0.083/0.017`. The result supports graph-based coordination over
no-graph MARL baselines, but it does not yet support a broad EA dominance claim
over Single-Graph MAPPO. Next priority is to run the role-gate prior diagnostic
before committing expensive 1M/2M formal training.

Role-gate prior seed0 dev100 is complete and documented in
`docs/role_gate_prior_seed0_dev100_summary.md`. The selected checkpoint is
update 60 with suite success/recovery/delayed-recovery/collision
`0.925/0.950/0.525/0.000`, compared with original EA seed0
`0.575/0.725/0.275/0.000`. Role-pair gate diagnostics on the selected checkpoint
show mean/max absolute gate deviation from 0.5 of `0.025573/0.121487`, much
larger than the previous near-neutral gate result (`~0.000154`). This is a
strong one-seed signal that the role-gate prior may improve both performance and
mechanism evidence. Next, run the same dev100 protocol for seeds 1 and 2 before
promoting it to the main long-budget method.

The gate-prior dev100 three-seed decision is complete and documented in
`docs/gate_prior_dev100_three_seed_decision.md`. Original EA was fairly extended
to 100 updates for seeds 0/1/2 and compared against gate-prior using the same
20/40/60/80/100 checkpoint set and suite-level selection. Gate-prior selected
mean success/recovery/delayed-recovery/collision is
`0.783/0.850/0.417/0.000`; original EA is `0.625/0.725/0.317/0.033`. Gate-prior
improves success and recovery on all seeds, improves delayed recovery on seeds 0
and 1, and has zero selected-checkpoint collisions. Decision: promote
`role_gate_prior_strength=0.4` as the current main EA-RG-MAPPO-S candidate and
stop further gate tuning. Next, freeze the common safety, BC, reward, and
checkpoint-selection protocol before formal budget studies.

The formal protocol freeze is documented in `docs/formal_protocol_freeze.md`.
Frozen items include the main gate-prior candidate, four baseline methods,
strict-sensing relay-failure scenario suite, BC settings, PPO settings, reward
and safety settings, checkpoint selection policy, and validation/test split
rules. Development base seed `291000` must not be treated as final held-out
evidence. Formal validation should use a new base seed such as `391000`, and the
final held-out test should use a separate base seed such as `491000` exactly
once. Next, prepare the common-budget study commands for 1M/2M runs and choose a
shared `B*` before five-seed formal training.

Formal budget-study command templates are documented in
`docs/formal_budget_study_commands.md`. The frozen budget mapping is 1M =
approximately 977 updates and 2M = approximately 1954 updates with
`num_envs=8` and `rollout_steps=128`. The budget study should first run seeds
0/1/2 for the four methods under the frozen protocol, evaluate validation with
base seed `391000`, and choose one shared `B*` for all methods. The next
execution step is to launch the 1M budget-study runs; do not run final held-out
test before `B*` and five-seed formal checkpoints are frozen.

Formal budget-study execution has started and is tracked in
`docs/formal_budget_progress.md`. EA-RG-MAPPO-S with role-gate prior seed0 BC is
complete, and its 1M PPO run has been restarted with safer 40-update chunks and
`save_interval=20` after an initial non-resumable partial attempt. Current seed0
progress is `400/977` updates, with saved candidate checkpoints at updates 200
and 400. Online monitor success at updates 200/300/400 is `0.8/1.0/0.8` with
zero collision, but this is not formal checkpoint-selection evidence. Next,
continue seed0 from `actor_critic_training_state_update_0400.pt` to 977, then
run seed1/2 for the same method before the fixed validation suite.

P0 information-boundary hardening was extended after manuscript review. The
environment now separates evaluation-only `attack_window`, computed from true
target state, from actor-visible `local_attack_window`, computed only from
legal target estimates and forced to zero when an attacker lacks direct sensing
or a valid target cache under strict sensing. Actor observations, graph node
features, and attacker-originated task-support edges now use
`local_attack_window`; reward, critic, termination, and evaluation may still use
the true `attack_window`. The earlier local-attack union edge has since been
removed by the sixth-review consistency hardening. A new regression test,
`test_local_attack_window_requires_actor_visible_target_information`, was added.
`D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest
tests/test_gate1_communication_feasibility.py -q` passes with `29 passed`.
Checkpoints trained before this hardening should remain development evidence
unless rerun or explicitly audited under the new actor information boundary.

The third manuscript-review P0 items were then addressed. Relay-originated
task-support evidence now uses only the relay's own updated target information;
the previous shortcut through a teammate's current private target-information
state was removed from `_has_target_information` / `_active_support_edge`.
Post-failure recovery delay now uses the start of the first stable
`attack_hold_steps`-length closure window rather than a one-step closure event,
and evaluation scripts expose/pass `attack_hold_steps=4` on formal paths. New
regression tests cover relay-private-state leakage, stable-window recovery
metrics, and fresh-information versus stale-cache recovery. `D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest
tests/test_gate1_communication_feasibility.py -q` now passes with `33 passed`.
The manuscript and protocol docs were updated to make Parameter-Matched
Single-Graph MAPPO a required main baseline and to freeze the primary comparison
as EA-RG-MAPPO-S versus Parameter-Matched Single-Graph on suite-level delayed
recovery under collision reporting.

Formal-budget protocol audit was completed after the P0 information-boundary
hardening. `RIGMAPPOConfig`, RI-GMAPPO PPO training, RI-GMAPPO BC pretraining,
single-checkpoint evaluation, and checkpoint-sweep evaluation now explicitly
pass `attack_hold_steps` into the 3DOF environment instead of relying only on
the environment default. HAPPO BC and HAPPO PPO training now do the same, while
HAPPO evaluation already had the pass-through. The Gate 1 regression suite now
includes `test_ri_config_passes_attack_hold_steps_to_3d_env`, and
`D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest -q
tests/test_gate1_communication_feasibility.py` passes with `33 passed`. A
one-update strict-sensing RI-GMAPPO training smoke, a minimal HAPPO BC smoke,
and a minimal HAPPO training smoke with `attack_hold_steps=4` also passed under
`results/protocol_hardening_smoke/`. The completed seed0 1M run and the seed1
partial 400-update run in `results/paper_config_runs/formal_budget/` are kept as
development/continuity artifacts only; the next formal-budget execution must
restart from a clean post-audit run directory before any checkpoint is treated
as formal validation or test evidence.

Clean post-audit formal-budget execution has restarted under
`results/paper_config_runs/formal_budget_post_audit/ea_rg_mappo_s_gate_prior/`.
Seed0 BC is complete with final action accuracy about `0.496` and demonstration
success about `0.908`. Seed0 PPO has reached `40/977` updates with training
states saved at updates 20 and 40. Online 5-episode monitor success at updates
20/40 is `1.0/1.0` with zero collision, but these values are only health checks;
the next execution step is to continue seed0 PPO to the 1M checkpoint set
`200/400/600/800/977`, then evaluate the fixed validation suite.

Clean post-audit seed0 PPO has advanced to `80/977` updates. Additional
training states are saved at updates 60 and 80, and online 5-episode monitor
success remains `1.0` with zero collision at updates 60/80. These are still
health checks only; continue toward the first formal candidate checkpoint at
update 200 before suite-level validation.

Clean post-audit seed0 PPO has advanced to `120/977` updates. Training states
are saved through update 120. Online monitor success/collision/timeout at
updates 100 and 120 is `0.8/0.0/0.2` and `1.0/0.0/0.0`, respectively; this
remains training health monitoring rather than checkpoint-selection evidence.
Continue from `actor_critic_training_state_update_0120.pt` toward update 200.

Clean post-audit seed0 PPO has reached the first formal budget candidate at
`200/977` updates under
`results/paper_config_runs/formal_budget_post_audit/ea_rg_mappo_s_gate_prior/ppo_seed0_1m/`.
The run now contains `actor_critic_update_0200.pt` and a matching training state
for continuation. Online monitor success/collision/timeout at updates 140, 160,
180, and 200 is `1.0/0.0/0.0`, `1.0/0.0/0.0`, `1.0/0.0/0.0`, and
`0.8/0.0/0.2`. These remain health checks only; continue to candidate
checkpoints 400, 600, 800, and 977 before fixed validation selection.

Fourth-review P0 hardening started on 2026-07-29. The review correctly noted
that ordinary post-failure recovery can still be inflated by attack-platform
target caches created before relay failure. The code now logs attacker cache
generation/delivery times and separates `post_failure_fresh_info_recovered`
from `post_failure_stale_cache_recovered`; checkpoint sweeps can use
`selection_metric=fresh_info_recovery`. The Gate 1 communication/information
boundary regression suite passes with `33 passed`, the 3DOF smoke test passes,
and the touched environment/evaluation scripts compile. Protocol and manuscript
docs now treat fresh-information recovery as the primary checkpoint-selection
metric, while delayed recovery and stale-cache recovery are auxiliary
diagnostics. At that point, remaining fourth-review items before formal multi-seed evidence were:
freeze target-invisible zero/mask semantics, delete or mathematically define
attack-edge semantics, correct the gamma-update notation, complete the
communication queue/cache/confidence formulas, formalize role-pair gate/prior
equations, and align PPO/HAPPO losses with code.

Fourth-review hardening continued by freezing actor graph target masking:
under `strict_target_sensing + agent_target_info_bottleneck`, the shared actor
graph target node is masked and does not expose the true target state or an
`any_detected` flag. Sixth-review consistency hardening later tightened this
from public prior + zero velocity to zero position + zero velocity, and also
zeros local target relative-position/range/velocity observation fields for
agents without legal target information. Legal target information remains only
in the detecting/receiving agent's local observation and target cache. This
fourth-review state still documented a local attack-window union edge; that edge
was later removed by the sixth-review consistency hardening and is no longer
part of the actor graph. The 3DOF gamma update notation was also corrected in the methods
draft by defining \(k_\gamma=0.35\,s^{-1}\). Gate 1 tests pass with `33
passed` after this stricter mask update. Remaining fourth-review items before
formal multi-seed evidence are now narrowed to: complete communication
queue/cache/confidence formulas, formalize role-pair gate/prior equations, and
align PPO/HAPPO losses with code.

Those remaining fourth-review documentation P0 items were then completed in
`docs/formal_methods_experiments_latex_zh.md`: communication delivery queues,
target-cache replacement, confidence decay, role-pair sigmoid gates, gate-prior
initialization, MAPPO minimization loss, and the HAPPO prefix-ratio baseline
loss are now written to match the code. The fourth-review hardening stage is
therefore ready for a final lightweight validation pass and then continuation
of clean post-audit formal-budget training. Because the shared actor graph
target mask changed after the previous clean post-audit seed0 run had reached
200/977 updates, that run is now a health/development artifact rather than
formal budget evidence. Formal budget training should restart from BC in a new
post-graph-mask directory and use `selection_metric=fresh_info_recovery`. Do
not run held-out test yet.

Fifth-review FreshRec hardening started on 2026-07-30. The review correctly
identified that `max(generation_step, delivery_step) >= failure_start` can
misclassify a pre-failure observation delivered after failure as fresh
information. Evaluation now defines `post_failure_fresh_info_recovered` as
after-loss, generation-based, continuous-window recovery: for every step in the
`attack_hold_steps` recovery window, an attacking platform must be in the true
attack window and its currently effective target cache must have
`generation_step >= node_failure_start_step`, while the target is also currently
directly tracked by at least one blue platform. Post-failure delivery of
pre-failure information is logged separately as
`post_failure_post_delivered_old_info_recovered`; maintained episodes with
fresh information but no prior loss are logged as
`post_failure_fresh_info_acquired_without_prior_loss`; direct and communicated
fresh recovery are split into `post_failure_fresh_direct_recovered` and
`post_failure_fresh_comm_recovered`. Checkpoint sweep summaries and selected
checkpoint CSVs now include these fields, and selection tie-breaks follow the
frozen order: higher fresh recovery, lower collision, shorter fresh recovery
time, higher success, earlier checkpoint. Gate 1 tests pass with `33 passed`
after this metric change. Formal budget training must restart after this
hardening; pre-Fifth-review validation selections are development evidence
only.

Sixth-review consistency hardening is complete on 2026-07-30. FreshRec now
uses the same current tracking condition as environment chain closure. Recovery
classification now requires pre-failure chain establishment and splits
pre-established maintained, pre-established recovered-after-loss, post-failure
first establishment, and never-established cases. The ordinary
`post_failure_chain_recovered_after_loss` metric now detects actual loss after
failure, rather than relying only on whether the chain was closed at the failure
start step. The checkpoint sweep defaults are locked to the formal protocol:
`selection_metric=fresh_info_recovery`, `selection_group=suite`, and
`selection_success_weight=0`. The hidden local-attack-window union-graph edge
has been removed; `local_attack_window` remains a node feature and task-support
cue but no longer opens a fourth graph channel.

The remaining target-invisible public-prior P0 was also closed in this pass:
under `strict_target_sensing + agent_target_info_bottleneck`, shared graph target
nodes are zero-masked and agents without legal target information receive zeroed
target relative-position/range/velocity observation fields. This is a formal
protocol change, so all formal budget runs must start after this commit.

Post-sixth-freeze formal preflight is complete and recorded in
`docs/formal_post_sixth_freeze_preflight.md`. Minimal BC plus one-update PPO
smokes passed for all five formal method families: MAPPO/no-graph, Single-Graph
MAPPO, Parameter-Matched Single-Graph MAPPO, EA-RG-MAPPO-S, and HAPPO. The
preflight outputs live under
`results/paper_config_runs/formal_budget_post_sixth_freeze_preflight/` and are
not paper evidence. The formal budget root named here
(`results/paper_config_runs/formal_budget_post_sixth_freeze/`) has since been
retired; see the superseded notice below. The current formal root is
`results/paper_config_runs/formal_budget_post_sixth_freeze_v1/`.

**SUPERSEDED (development/pre-freeze evidence only).** The two paragraphs below
describe the *old* `results/paper_config_runs/formal_budget_post_sixth_freeze/`
root. That root was retired under Decision A after a P0 environment fix
(target-prior zero/mask + removal of the hidden union-graph attack edge)
invalidated every checkpoint produced before the fix. Its BC `15/15` and PPO
`15/15`-at-update-20 records are **not** formal evidence and must never be cited
as such. The runs were relocated to
`results/paper_config_runs/formal_budget_pre_sixth_freeze_development/`.
Retained verbatim for provenance:

> Formal post-sixth seed0/seed1/seed2 BC is complete and recorded in
> `docs/formal_budget_post_sixth_seed0_bc_progress.md`. All five formal methods
> completed 20 BC epochs for seeds `0`, `1`, and `2` under the clean
> `results/paper_config_runs/formal_budget_post_sixth_freeze/` root and produced
> the expected latest/best BC checkpoints. The formal BC stage is `15/15`
> complete.
>
> Formal post-sixth 1M PPO training has started and is tracked in
> `docs/formal_budget_post_sixth_1m_progress.md`. All `15/15` method/seed tasks
> have valid PPO logs and latest training-state checkpoints, and all reached at
> least update `20` with checkpoint status `ok` (`no_graph seed2=29`,
> `happo seed1=26`, several seed2 runs `=24`).

### Current formal status (authoritative)

The only valid formal root is
`results/paper_config_runs/formal_budget_post_sixth_freeze_v1/`:

```text
formal_budget_post_sixth_freeze_v1:
BC  = 0/15
PPO = 0/15
Formal training not started
```

Formal artifacts may only be produced from the freeze tag
`formal-post-sixth-freeze-v1.1`. Both launchers now enforce this: they abort
with exit code `2` unless `HEAD` equals the tag commit and the tracked working
tree is clean (untracked `results/` is ignored). The BC launcher additionally
refuses to overwrite existing BC outputs without `-Force`, writes a
`bc_manifest.json` recording the freeze commit and architecture into every BC
directory, and verifies each checkpoint afterwards. The progress checker
reports `bc_loadable`, `bc_method_compatible`, `bc_sha256`, and
`bc_freeze_commit`, and only classifies a run as `FRESH` when its BC init is
loadable, non-empty, and an exact architecture match; a present-but-unusable BC
is reported as `BC_INVALID`.

The maintained launchers remain the resumable
`scripts/run_formal_post_sixth_1m_chunk.ps1` and
`scripts/run_formal_post_sixth_1m_bc.ps1`; the older all-in-one
`scripts/run_formal_post_sixth_1m.ps1` predates these gates and must not be used
for formal runs.

Next execution steps, in order: regenerate one BC
(`ea_rg_mappo_s_gate_prior` seed `0`) and verify it, regenerate the remaining
`15/15` BC until the gate reports `FRESH=15 / BC loadable=15/15 / freeze commit
match=15/15`, run the `0→2→4` resume validation, then advance all runs to
update `100` and on to `200/400/600/800/977`.
