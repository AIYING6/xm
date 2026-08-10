# N2 repair protocol: physical potential shaping

**Status:** `N2_REPAIR_AUTHORIZED__NO_N3__NO_FORMAL_TRAINING`.

This is one bounded repair of the N2 learnability failure. The sole hypothesis
is that the joint four-transition physical commit condition and terminal-only
credit assignment are too sparse for the transparent vanilla MAPPO pilot.

## Exactly one changed factor

The repair enables `mission_progress_shaping_enabled=True`. It adds only

\[
r_t^{shape}=0.25\,[0.99\Phi(s_{t+1})-\Phi(s_t)]
\]

to the existing mission reward. The potential is fixed as

\[
\Phi=0.90(0.50D+0.30H+0.20V)+0.10C,
\]

where, for attacker/interceptor roles, `D` is normalized distance progress,
`H` is line-of-sight heading alignment, `V` is normalized relative closing
velocity, and `C` is the true physical four-step `engage_commit` hold fraction.
All terms use simulator kinematics only. `C` advances only when the existing
N0 true-standoff eligibility predicate is satisfied. No sensing, packet, cache,
message age, communication, graph relation, `chain_closed`, attack-window or
engagement-ready predicate is used.

The following remain unchanged: action space, N0 transition, four-step hold,
collision/constraint precedence, target escape, horizon 360, `RMTN180`, all
outcome categories, actor contract, network, optimizer and training budget.
`NEUTRALIZED` remains the only mission success terminal outcome.

## Frozen re-test

The same vanilla no-graph MAPPO baseline, seeds `7201` and `7202`, 60 updates,
four environments, 128 rollout steps, four PPO epochs, hidden size 128, and
learning rate `3e-4` are used. The same paired evaluation seeds
`730000`--`730047` are used. Final update 60 is used directly; no checkpoint
search or extra budget is allowed. Outputs are development-only and cannot
enter N3, F1 or F2.

## Decision rule

`N2_LEARNABILITY_PASS__READY_FOR_N3_METHOD_SELECTION` requires at least one
learned neutralization, pooled `RMTN180 < 180`, a neutralization incidence
above the random floor, and no immediate oracle-ceiling behavior. Otherwise
the state is
`N2_REPAIR_NO_GO__TASK_LEARNABILITY_NOT_ESTABLISHED`, and this project stops
without a new method or another reward repair.
