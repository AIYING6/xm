# C2-M3 500k-to-1M diagnostic extension contract

**Status:** `M3_1M_EXTENSION_AUTHORIZED`.

## Scope

Resume the existing 20 completed C2-M3 trajectories in place from their exact
500k runtime states to the fixed 1M endpoint. This is a horizon diagnostic,
not a new algorithm experiment or a performance-driven rerun.

## Frozen population and methods

- Cohort A: 5101--5105; Cohort B: 5106--5110.
- Arms: `utr_sg` and `group_weighted_utr_sg` only.
- No seed, PPO, network, reward, sampler, group-weight strength, group-weight
  bounds, telemetry definition, or score change is permitted.
- Each trajectory resumes from its own
  `actor_critic_runtime_state_milestone_500k.pt`; it does not reinitialize.

## Exact budget and artifacts

The source runtime update is 1953. The continuation performs 1954 local
updates, ending at global update 3907 (1,000,192 training environment steps
per trajectory). The exact additional interaction count is 500,224 per
trajectory and 10,004,480 over all 20 trajectories. It appends the existing
training and training-only telemetry logs and writes fixed runtime milestones
at 625k, 750k, 875k, and 1M.

No evaluation starts in this contract. There is no checkpoint promotion,
automatic continuation beyond 1M, parameter adjustment, or algorithm change.

## Hard stop and later interpretation

At 1M, a separately authorized post-hoc analysis must return either a
prospective mechanism-validation authorization or
`FAILURE_MODE_DISCOVERY_NO_GO`. Continued reversals, no repeated leading
precursor, or incompatible cohort directions require the latter. No 3M or
10M extension is authorized.
