# Phase 2IA9 failure-dependency path-audit report

## Scope

Phase2IA9 was a trace-only replay of the frozen P1 schedule. It retained the
same controllers, support trigger, relay-1 next-step failure, 80-step duration,
and environment configuration; it added only read-only path telemetry. No
checkpoint, optimizer, training update, canonical seed, or canonical result
was used.

The replay used 600 new audit-only episodes (two fixed controllers × seeds
801–803 × 100 episodes).

## Integrity

- 600 raw episode records and six trace files were produced.
- All 600 trigger observations were present.
- Fault-start reconstruction matched every raw record (0 mismatches).
- The information-path telemetry passed its static noninterference and seeded
rollout invariance checks before replay.

## Frozen classification outcome

| Controller | Trigger observations | Fault-active observations | Classification |
|---|---:|---:|---|
| structural_oracle | 300 | 600 | DIRECT_BYPASS in every observation |
| legal_observation | 300 | 600 | DIRECT_BYPASS in every observation |

At every pre-failure support trigger and every recorded relay-failure timestep,
the attacker directly detected the target. No fresh attacker cache path—relay
1 dependent or otherwise—was needed to satisfy attacker target information.

## Scientific conclusion

**FAILURE-DEPENDENCY CLASSIFICATION: DIRECT-SENSING BYPASS**

Relay-1 is not a causal information dependency for the observed support state
in this nominal geometry/sensing configuration. A relay-1 communication
failure can therefore leave `chain_support_t` intact, exactly as observed in
P1. This is a task-causality finding, not a poor algorithm result and not a
reason to make the fault longer or train more.

## Decision

**CURRENT RELAY-FAILURE RECOVERY CLAIM: UNSUPPORTED**  
**Phase2IA8 P2: NO-GO**  
**Role-Gate retention: UNRESOLVED**  
**Architecture Freeze / Phase 3A: NO-GO**

The current task cannot support a claim about recovery from losing a relay
information path, because the attacker directly senses the target throughout
the tested support state.

## Required user-level scientific choice

Continuation requires an explicitly authorized, independently justified
**relay-dependent task design**. It must state the real operational rationale
for why the attacker lacks direct target sensing while a scout/relay path is
necessary; it must define sensing geometry and initial conditions before any
outcomes; and it must include a feasibility gate demonstrating the intended
dependency for transparent controllers before learning begins.

That is a new research task, not a parameter tweak. It must be separately
designed and approved before implementation. No automatic failure-protocol or
observation change follows from this audit.
