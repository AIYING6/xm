# T0 — Telemetry-Native Evidence-Chain Freeze

## Purpose

T0 starts a new evidence line after the old Phase-D archive could not support
a complete step-level replay.  T0 does **not** reinterpret, repair, or replace
any historical result.  It introduces no network, loss, reward, environment
semantic, PPO, or failure-schedule change.

The purpose is only to make every future rollout self-contained and
re-aggregable from its own raw step telemetry.

## Single-source contract

For every future technical, development, held-out, or canonical evaluation:

```text
raw_step_telemetry.jsonl
        -> episode_aggregates.jsonl
        -> seed / condition summaries
        -> paper tables and mechanism analysis
```

`episode_aggregates.jsonl` must be derived from the raw JSONL in the same
execution.  No later CSV, manually accumulated quantity, or historical
aggregate is a competing evidence source.

All scalar reductions use Python/NumPy float64 from the logged step values.
No cross-implementation comparison to a legacy float32 aggregate is required
or permitted as a validity gate.

## Information boundary

Each step record separates:

- `actor_legal`: the exact `obs`, `share_obs`, graph tensors, and sampled
  action available to the decentralized actor;
- `diagnostic_only`: simulator positions, target state, and audit telemetry.

The policy callback receives only `(obs, share_obs, graph)`.  It cannot
receive the diagnostic record, simulator object, global path oracle, future
link, failure label, or ground-truth route.

## Frozen task semantics

T0 retains the S2 3DOF task contract: straight target, strict target sensing,
actor information bottleneck, business-grounded geometry, 260-step horizon,
and Relay 1 failure.  T0's technical F0 descriptor is onset 44, duration 80.
The IDs `910000–910001` are technical smoke IDs only, not development,
held-out, or canonical evidence.

## Mandatory gates before any new training

1. raw-to-aggregate source closure passes exactly;
2. same seed / same deterministic policy replay is byte-equivalent at the
   canonical JSONL level;
3. logger versus independent no-raw-logger rollout preserves the derived
   episode aggregate exactly;
4. actor/dynamic diagnostic field separation is schema-audited;
5. output manifest hashes raw and aggregate files and states the complete
   scenario descriptor;
6. output roots are append-protected; no historical result directory is
   overwritten.

## T0 boundary

Passing T0 authorizes only a separately approved telemetry-native reference
run.  It does not authorize a new method, long training, held-out seeds,
canonical seeds, or a paper superiority claim.
