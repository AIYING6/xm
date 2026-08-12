# Phase 2IA8 P0 support-instrumentation audit

P0 adds exactly one diagnostic info field: `chain_support_t`. It is the same
nonterminal conjunction already used to increment `attack_hold` in default
task execution: attack window, tracking, and target-information chain to an
attacker.

The P0 tests must show, timestep by timestep, that `attack_hold` increments
iff this field is true and resets otherwise; repeated seeded rollouts must be
bitwise-equivalent in reward, done, support, and closure observations. Static
audit additionally verifies that success and termination code remains exactly
unchanged.

P0 is logging/instrumentation only. It does not authorize triggered failure,
P1 mechanism probes, learned-policy evaluation, or training.
