# Phase 2IA8 P1 pre-completion mechanism-probe report

## Scope

P1 used transparent fixed controllers only—no learned policy, checkpoint,
optimizer, training update, canonical seed, or canonical result. It tested the
frozen pre-completion sequence:

```text
two consecutive chain_support_t steps → next-step relay-1 failure (80 steps)
```

Six hundred fresh DEVELOPMENT_ONLY episodes were generated: two controllers ×
three seeds (701–703) × 100 episodes.

## Integrity and timing

- 600 raw episodes and six controller/seed timestep traces were produced.
- Independent reconstruction covered all 600 episodes with zero mismatches.
- All 600 episodes were support-eligible (100 in each controller × seed cell).
- In every eligible episode, fault activation was exactly the timestep after
  the frozen two-step support trigger.

Thus Phase2IA7's semantic correction is confirmed: a pre-completion support
state is observable and can be fault-aligned before terminal mission success.

## P1 Gate

| Controller | Support eligible | Eligible post-failure support losses | P1 |
|---|---:|---:|---|
| structural_oracle | 300 / 300 | 0 | FAIL |
| legal_observation | 300 / 300 | 0 | FAIL |

All eligibility and trace/timing conditions pass, but the preregistered
requirement of at least one eligible support loss fails for both controllers.

## Mechanistic interpretation

The relay-1 failure was active in 600 recorded timesteps (one pre-terminal and
one terminal timestep per episode). `chain_support_t` remained true in all 600
of those active timesteps. This is consistent with the executable support
semantics: `_comm_has_chain_to_attacker()` is satisfied whenever an attacker
has direct detection or a fresh own cache. The current support predicate does
not establish that the relay is a necessary member of the information path.

This is not a controller-performance finding and does not imply that more
training is needed. It establishes a failure-dependency ambiguity: relay-1 may
be redundant under the current initial geometry and sensing conditions.

## Decision

**P1 MECHANISM GATE: FAIL (NO OBSERVED SUPPORT LOSS)**  
**Phase2IA8 P2 archived-checkpoint probe: NO-GO**  
**Role-Gate retention: UNRESOLVED**  
**Architecture Freeze / Phase 3A: NO-GO**

## Minimal next action

Do not change failure duration, choose a different failed agent, suppress
direct sensing, alter initial geometry, or rerun P1 based on this outcome.
First conduct an independent **failure-dependency/path audit**: log the
attacker's information source (direct versus cache), cache source/path and
hop count, and relay participation at the two support-trigger and active
failure timesteps. A subsequent scientific design decision can then determine
whether a relay-dependent task is justified; it cannot be silently created to
make recovery occur.
