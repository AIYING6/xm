# Formal Protocol Freeze

Last updated: 2026-07-30

## Purpose

This document freezes the experiment protocol before formal budget studies and
five-seed training. Its purpose is to prevent result-driven changes to the
scenario, reward, safety rule, BC initialization, or checkpoint-selection rule.

## Main Candidate

The current main method candidate is:

- Name: EA-RG-MAPPO-S with role-gate prior.
- `graph_encoder=multi_relation`
- `role_gate_prior_strength=0.4`
- `graph_relation_ablation=none`
- `graph_message_ablation=none`
- `graph_input_ablation=none`
- `chain_aux_coef=0.0`

No further gate-parameter optimization is allowed before the formal held-out
test. The seed2 delayed-recovery caveat must be carried into the final analysis
instead of tuned away.

## Baselines

The formal baseline set is:

- MAPPO/no-graph.
- Single-Graph MAPPO.
- Parameter-Matched Single-Graph MAPPO.
- HAPPO.
- EA-RG-MAPPO-S with role-gate prior.

Optional paper-facing comparison:

- Original EA-RG-MAPPO without role-gate prior can be reported as an internal
  method-development ablation, not as a required external baseline.

## Frozen Scenario Suite

Formal validation and test use the four fixed strict-sensing relay-failure
timing scenarios:

- `dropout030_delay2_relay_failure_early`
- `dropout030_delay2_relay_failure`
- `dropout030_delay2_relay_failure_delayed`
- `dropout030_delay2_relay_failure_late`

Frozen environment settings:

- Target policy: `straight`.
- Strict target sensing: enabled.
- Agent target-info bottleneck: enabled.
- Communication dropout probability: `0.30`.
- Message delay: `2`.
- Failed blue agent: relay, index `1`.
- Training failure start: random `[25, 70]`.
- Training failure duration: `80`.
- Evaluation scenarios use their predefined fixed failure timing.
- Minimum success step: `80`.

No new scenario difficulty, target policy, dropout, delay, or failure timing may
be introduced to choose the final method. Additional scenarios can only be added
later as secondary robustness tests after the main protocol is frozen.

## Frozen Actor Information Boundary

Formal training and evaluation must use the hardened actor information boundary:

- Actor observations and actor graph features use `local_attack_window`, not the
  evaluation-only true `attack_window`.
- `local_attack_window` is computed from direct sensing or a valid local target
  cache. Under strict target sensing and the target-information bottleneck, it is
  forced to `0` when the attacker has no actor-visible target information.
- True `attack_window` may be used by reward, centralized critic, termination,
  chain-closure metrics, and evaluation logs, but must not enter decentralized
  actor observations, actor graph node features, graph edges, or
  attacker-originated task-support edges.
- Under strict target sensing and the target-information bottleneck, shared graph
  target nodes are zero-masked and agents without legal target information
  receive zeroed target relative-position/range/velocity observation fields.
- Task-support relation edges must satisfy role compatibility, delivered
  communication, and actor-visible support evidence. Static role compatibility
  alone cannot open an actor graph edge.
- Relay-originated task-support evidence must use the relay's own updated local
  target information only. It must not read another teammate's current private
  `F_m` state through a communication adjacency shortcut.
- Post-failure recovery metrics use the same consecutive closure condition as
  success. The reported recovery delay is the start of the first stable
  `attack_hold_steps`-length closure window after failure, not a one-step
  instantaneous chain-closure event.

Any checkpoint trained before this boundary was implemented is development
evidence only unless rerun or explicitly separated in the analysis.

## Frozen BC Rule

All learning methods that support BC use the same BC family:

- Teacher: geometric offset policy.
- Demonstration episodes: `120`.
- BC epochs: `20`.
- Batch size: `256`.
- Balanced action loss: enabled.
- Attacker action weight: `2.0`.
- Same strict-sensing, dropout, delay, relay-failure, and `min_success_step`
  settings as training.

HAPPO uses its HAPPO-specific BC script but the same demonstrations and weighting
logic.

No method may receive extra demonstrations, different teacher policies, or
additional BC epochs in the formal comparison.

## Frozen PPO Rule

PPO training settings:

- Number of envs: `8`.
- Rollout steps: `128`.
- Hidden dim: `64` for MAPPO/no-graph, Single-Graph, HAPPO, and
  EA-RG-MAPPO-S; `96` for Parameter-Matched Single-Graph MAPPO.
- Role dim: `8`.
- Intent dim: `8`.
- Actor learning rate: `5e-5` for MAPPO-style methods.
- Critic learning rate: `1e-4` for MAPPO-style methods.
- HAPPO learning rate: `5e-5`.
- Clip coefficient: `0.1`.
- PPO epochs: `2`.
- Target KL: `0.01` for MAPPO-style methods.
- Entropy coefficient: `0.003`.
- Max grad norm: `0.5`.
- Critic warm-up: `20` updates for MAPPO-style methods.

If a method cannot use a field structurally, it must be documented. The field
must not be replaced by a stronger method-specific alternative.

## Frozen Reward and Safety Rule

Reward/safety settings:

- Post-loss chain reclosure reward weight: `0.5`.
- Post-loss chain reclosure min step: `80`.
- Safety proximity distance: `2500`.
- Safety proximity penalty weight: `0.5`.
- Attack geometry reward weight: `0.0`.
- Chain auxiliary loss: `0.0`.

No reward shaping changes are allowed after this freeze unless a code bug is
found. If a bug is found, all methods affected by the bug must be rerun.

## Checkpoint Selection Rule

Budget study checkpoint candidates:

- Save snapshots every fixed interval.
- Evaluate candidate checkpoints on the validation split only.
- Select one checkpoint per training seed using suite-level mean over the four
  frozen scenarios.
- Primary selection metric: generation-based after-loss post-failure
  fresh-information recovery
  (`selection_metric=fresh_info_recovery`).
- Fresh-information recovery requires a continuous `attack_hold_steps` window
  in which the attacking platform's current effective target cache was generated
  no earlier than the relay-failure start, the attacker is in the true attack
  window, and the target is currently directly tracked by at least one blue
  platform. A message generated before failure but delivered after failure is
  reported separately and is not FreshRec.
- Recovery requires pre-failure chain establishment. Episodes where the chain
  is first established only after failure are reported as post-failure first
  establishment and are not counted as recovered-after-loss.
- `delayed_recovery_min_step=80` remains an auxiliary reporting threshold, not
  the primary selection metric.
- Success weight: `0`.
- Collision must be reported. If formal selection uses a collision constraint,
  that constraint must be applied to all methods before any final test.
- Tie-break order for checkpoints with equal primary score:
  1. lower suite-level collision rate;
  2. lower restricted mean fresh-information recovery time;
  3. higher suite-level success rate;
  4. earlier checkpoint update.

Recommended final rule before held-out test:

- Use suite-level post-failure fresh-information recovery as the primary score.
- The primary paper comparison is EA-RG-MAPPO-S versus Parameter-Matched
  Single-Graph MAPPO on suite-level post-failure fresh-information recovery.
  Collision rate is a safety constraint and must be reported for every selected
  checkpoint.
- Add a hard selected-checkpoint collision constraint of `0` if every method has
  at least one feasible zero-collision checkpoint under the final budget.
- If any method has no zero-collision checkpoint, do not silently drop it; report
  this and either use unconstrained selection for all methods or define a common
  penalty rule before looking at test results.

## Data Splits

Development results so far used `base_seed=291000` and are not held-out test
evidence.

Formal study must use:

- Training seeds: five seeds, recommended `0 1 2 3 4`.
- Validation split: new base seed not used for development, recommended
  `391000`.
- Final held-out test split: new base seed used exactly once, recommended
  `491000`.

After final held-out test is run, no method, checkpoint, budget, scenario,
reward, BC, or safety parameter may be changed based on test results.

## Budget Study

Before five-seed formal training, run a common-budget study to determine `B*`.

Candidate budgets:

- `1M` environment transitions: approximately `977` updates with
  `8 * 128 = 1024` transitions per update.
- `2M` environment transitions: approximately `1954` updates.

Decision rule for `B*`:

- Define `y_last` as the mean validation primary metric over the last 10% of
  candidate checkpoints and `y_prev` as the mean over the previous 10%.
- Define `delta_late = y_last - y_prev`.
- If at least three main methods have `delta_late > 0.03`, expand all methods to
  2M.
- A seed failure is defined as post-failure fresh-information recovery `< 0.10`
  and success `< 0.20` on the validation suite. If at least two methods have
  seed failures at 1M, expand all methods to 2M.
- Otherwise choose 1M.
- The same `B*` must be used for all five main methods.

## Next Step

Start the budget study with reduced seeds before five-seed formal training:

- First budget-study seeds: `0 1 2`.
- Methods: five main methods.
- Budgets: 1M and, if needed, 2M.

Only after `B*` is chosen should five-seed formal training begin.

## Frozen Source Baseline

The formal 1M budget study runs against a frozen source baseline (not just a
frozen protocol). Any training artifact is valid only if produced by this commit.

- **git tag**: `formal-post-sixth-freeze-v1.3` (current authority). Historical tags retained unmoved:
  - `formal-post-sixth-freeze-v1` (SHA `8b13e26`): first freeze; no formal artifacts; source audit only.
  - `formal-post-sixth-freeze-v1.1` (SHA `e30359b`): freeze gates, coverage block, bc_manifest, BC verification, BC_INVALID, seed-passing fix; no formal artifacts.
  - `formal-post-sixth-freeze-v1.2` (SHA `446aad7`): BOM encoding fix for bc_manifest.json writer/reader; no formal artifacts.
- **branch**: `main`
- **python**: 3.8.20; **torch**: 2.4.1+cu124; **cuda**: 12.4
- **P0 actor/info-boundary fix** (committed in `envs/uav_intercept_3d_env.py`):
  - target prior in shared graph is zero-masked;
  - under strict sensing + bottleneck, actor obs `rel`/`red_vel` are zeroed when target not visible;
  - union-graph hidden `attack` edge removed.
- **Resume authority**: training-state checkpoint `update` is authoritative; `train_log.csv` is audit-only.
- **Gate**: `FRESH / READY / COMPLETE / BLOCKED` with two-stage check (pre-PPO: FRESH=15 allowed; post-launch: READY+COMPLETE=15, FRESH=0).

### Enforced launch gates (v1.3)

Each launcher dot-sources `scripts/formal_freeze_gate.ps1` and exits `2` when:

- `git rev-parse HEAD` != `git rev-list -n 1 formal-post-sixth-freeze-v1.3`;
- `git diff --quiet` fails (tracked working-tree changes);
- `git diff --cached --quiet` fails (staged but uncommitted changes);
- any untracked file exists outside `results/paper_config_runs/formal_budget_post_sixth_freeze_v1/**`.

Untracked files under `results/` are intentionally ignored, since formal
outputs are produced by the run itself. Tracked source and config changes are
never ignored. A `-AllowUnfrozen` switch exists for development smoke runs and
downgrades the failure to a warning; its outputs are not formal evidence.

The BC launcher additionally refuses to overwrite any directory that already
contains `bc_train_log.csv`, `actor_critic_latest.pt`, or `happo_bc_latest.pt`
unless `-Force` is given, and writes `bc_manifest.json` (freeze commit, tag,
architecture, teacher settings, checkpoint SHA256) into every BC directory.

### BC integrity gate (v1.3)

`FRESH` previously required only that the BC file exist, so a truncated write,
an empty file, a wrong hidden dim, or a checkpoint from another method could
seed a "formal" run. The full integrity check now covers:

- **File checks**: `bc_exists`, `bc_nonempty_file`, `bc_loadable`
- **State checks**: `bc_nonempty_state`, `bc_method_compatible` (exact architecture match)
- **Manifest checks**: `bc_manifest_valid` (all fields: method, seed, freeze_tag,
  freeze_commit, checkpoint name, graph_encoder, hidden_dim, role_gate_prior_strength
  match expectations), `bc_sha256_match` (manifest SHA256 == actual file SHA256),
  `bc_method_metadata_match` (manifest method == requested method)
- **Provenance**: `bc_sha256` (computed), `bc_freeze_commit` (from manifest)

Compatibility is an *exact* match: a reference agent is built with the method's
own encoder and hidden dim, and every key and shape must correspond. HAPPO is
checked through its own agent class.

`scripts/check_formal_post_sixth_1m_progress.py` accepts `--expected-tag` (which
auto-resolves the freeze commit via `git rev-list`), classifies an unusable BC
as `BC_INVALID`, and requires `--skip-bc-architecture` to force all BC-aware
tasks into `BC_UNVERIFIED` with non-zero exit (diagnostic only, never a
formal-gate escape). `-ResumeValid` in the BC launcher allows safe batch
interruption recovery.

Pre-PPO acceptance requires:

```text
FRESH = 15
READY = 0
COMPLETE = 0
BLOCKED = 0

BC loadable = 15/15
BC architecture exact = 15/15
BC manifest valid = 15/15
BC SHA256 match = 15/15
freeze commit match = 15/15
```
- **Evidence separation**:
  - `formal_budget_pre_sixth_freeze_development/` = DEVELOPMENT EVIDENCE ONLY (pre-freeze 20-29 updates).
  - `formal_budget_post_sixth_freeze_v1_preflight/` = PREFLIGHT EVIDENCE ONLY (pre-tag BC + 0→2).
  - Formal results live only in `formal_budget_post_sixth_freeze_v1/`, started fresh after the tag.

Training scripts must abort if `git rev-parse HEAD != freeze_commit_sha` or the
working tree has uncommitted source changes.
