# UTR Existing Behavior Data Audit

**Status:** completed — read-only existing-assets audit
**Protocol:** UTR Good-vs-Weak Seed Mechanism Discovery
**Scope:** Phase-D 2M UTR development assets for seeds 2002, 2101, 2102, 2103, and 2104

## 1. Scope compliance

This audit performed no environment reset/step, policy loading for rollout, evaluator execution, tape generation, checkpoint continuation, training, or algorithm modification. It inspected only existing repository source/provenance documents and the two already-present Phase-D cloud source packages:

- `EA-RG-MAPPO_PHASE_D_CONTINUATION_2M_STOPLOSS_8c1fd30.zip`
- `EA-RG-MAPPO_PHASE_D_CONTINUATION_d6b2c13.zip`

The prior Phase-D forensic provenance identifies the historical result artifact as `phase_d_2m_stoploss_results.tar.gz`, SHA-256 `BAB53589E457A10BFF638F62790C70B1F80FAC9E4F0DDB7E30164BCFF8B5CF41`. That result archive is not mounted at its prior local download location during this audit. More importantly, the previously verified result design itself stores episode aggregates rather than time-indexed behavioral trajectories, as documented below.

## 2. Per-seed provenance inventory

For each UTR seed, the historical Phase-D manifest/forensic record establishes a completed strict-continuous 1M→2M trajectory with final and milestone checkpoint/runtime-state hashes. The historical evaluation contains 100 base episode identifiers under nominal, F0, timing, duration, and compound conditions.

| Asset / variable class | Historical availability | Granularity | Provenance / limitation |
|---|---|---|---|
| Final UTR checkpoints, seeds 2002/2101–2104 | AVAILABLE | one final model per seed | Existing Phase-D asset; loading it to execute a policy is forbidden by this protocol. |
| Runtime states | AVAILABLE | continuation state at saved milestones/final | Model/optimizer/RNG/environment runtime persistence for training continuation; not an already-recorded evaluation trajectory. |
| Training log | AVAILABLE | PPO update | Update-level scalar diagnostics, not episode-aligned actions/states. |
| Actor-gradient telemetry | AVAILABLE | PPO update | Gradient bookkeeping; not actor behavior in an evaluated episode. |
| Evaluation records | AVAILABLE historically | one row per method × seed × condition × episode | 18,000 final rows across all three methods; 6,000 UTR rows. No time-index field. |
| Evaluation condition / scheduled onset / duration | AVAILABLE | episode level | `topology_condition`, `onset`, `duration`. |
| Failure exposure / terminal step / terminal flags | AVAILABLE | episode level | `failure_exposed`, `terminal_step`, collision/timeout/constraint/success. |
| Path/support information | PARTIAL | episode aggregate | During-failure direct/relay path fractions, support/info fractions, mean cache age, and total path-switch count. No per-step route sequence is retained. |
| Distance / control effort | PARTIAL | episode aggregate | Total traveled distance and total control effort only; no per-agent series or window. |
| Agent positions / velocity / heading | ABSENT | — | No UTR Phase-D state trajectory file exists in the accessible source packages or workspace. |
| Per-agent actions / action direction | ABSENT | — | No UTR Phase-D action log or behavior trace exists. |
| Role/task state / task-progress stage | ABSENT | — | No phase-aligned recorded role-state progression is available. |
| Step-level adjacency / relation adjacency / support source | ABSENT | — | No time-indexed graph/path telemetry file exists. |
| Terminal windows, last 20/40/80 steps | ABSENT | — | Cannot be derived from an aggregate row without replay, which is prohibited. |

## 3. File-level search result

Both existing Phase-D source packages contain **zero** entries under `results/development/phase_d/`. They contain source, protocol documents, and two pre-existing image assets with “trajectory” in their filenames, but no UTR Phase-D trajectory/action/position/step trace. A recursive search of the accessible workspace found:

```text
locally extracted Phase-D result files: 0
UTR-named action/position/step/trajectory behavior artifacts: 0
```

The image assets and plotting script are not UTR seed2002/2101–2104 episode records and cannot be treated as behavior data.

## 4. Why aggregate telemetry is insufficient

The Phase-D evaluation path calls `evaluate_episode`. At runtime it accumulates a transient list containing only relay-failure-active flag, attacker cache path, task support, legal-information status, and cache age. It then reduces that list to fractions/means and writes a single final episode row. It also reduces movement and control to total traveled distance and total control effort.

Consequently, the stored row can support statements such as:

- the scheduled failure condition and whether exposure occurred;
- terminal time and terminal collision/timeout/constraint/success flags;
- total path-switch count and mean/fractional during-failure telemetry.

It cannot support statements such as:

- which agent first changed action after failure;
- whether Scout, Relay, or Attacker stalled, oscillated, or moved incompatibly;
- whether a support/path switch preceded, followed, or coincided with behavior change;
- whether a terminal-window behavior precursor occurred 20/40/80 steps before timeout;
- whether a proposed coordination failure is present in most weak episodes but absent from good episodes.

Reconstructing any of those quantities would require exactly the prohibited operation: running a policy/environment to create a new trajectory.

## 5. Mandatory behavior-data sufficiency gate

The protocol requires all of the following in existing time-aligned data:

1. failure onset or topology transition;
2. episode termination;
3. at least one agent-level behavior signal;
4. at least one task/support/path progression signal; and
5. termination type.

| Required link | Result |
|---|---|
| Failure onset/topology condition | Available only as scheduled episode metadata/aggregate failure telemetry |
| Episode termination/type | Available at episode level |
| Agent-level behavior signal | **Absent** |
| Time-indexed task/support/path progression | **Absent** |
| Failure-aligned or terminal-window alignment | **Absent** |

```text
BEHAVIOR_DATA_SUFFICIENT = NO
```

The missing third and fourth links make it impossible to test the requested chain:

```text
topology transition → agent behavior → task/support consequence → timeout/degradation.
```

## 6. Stop disposition

The protocol prohibits compensating for this insufficiency by re-running the evaluator, replaying a checkpoint, creating a trace-only tape, or collecting new trajectories. No good-vs-weak temporal analysis, representative episode selection, visualization, or mechanism claim is therefore admissible.

The only permitted next disposition is recorded in [UTR_MECHANISM_DISCOVERY_DECISION.md](UTR_MECHANISM_DISCOVERY_DECISION.md).
