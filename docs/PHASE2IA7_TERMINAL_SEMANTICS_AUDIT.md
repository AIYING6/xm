# Phase 2IA7 terminal-semantics audit

## Finding

The Phase 2IA5 E0 and Phase 2IA6 Gate F feasibility condition required four
consecutive observations of `chain_closed`. That condition is unreachable in
the current default environment semantics.

The relevant executable logic is:

```text
attack_hold += 1 while support condition holds
chain_closed = (attack_hold >= attack_hold_steps)
success = chain_closed          # default non-v16 mode
done = success OR collision OR constraint_violation OR timeout
```

`attack_hold_steps` is 4. Thus `chain_closed` first becomes true on the fourth
consecutive underlying support timestep, and that same transition terminates
the episode. No fifth step is available; four consecutive *closed* timesteps
cannot be observed.

## Consequence for prior development gates

- The zero E0 eligibility count does not establish that the archived policies
  could not generate a chain-support period. E0 was defined with an impossible
  eligibility predicate.
- The zero Phase 2IA6 Gate F count does not establish structural task
  infeasibility. Both its oracle and legal-controller probes used the same
  impossible predicate.
- These outputs remain preserved as protocol-invalid diagnostics. They must
  not be deleted, re-labelled as valid negative evidence, or used for any
  Role-Gate comparison.

The earlier statements that the nominal task formulation was closed are
therefore superseded. This is a semantic/protocol defect, not a model result.

## What remains frozen

The primary strict recovery endpoint is not modified by this audit. The issue
is that its prerequisite must be represented by a nonterminal observable
**support predicate**, rather than by the terminal `chain_closed` completion
flag. No new training, no canonical experiment, and no new recovery claim is
authorized here.

## Required correction path

Before any rerun, an independent amendment must define and log an exact
per-timestep `chain_support_t` predicate. It must use the same components that
increment `attack_hold` in the environment, be observable before terminal
success, and be separately distinguished from `chain_closed`/mission success.
The amendment must also state a failure schedule that occurs after a sustained
support run but before terminal mission completion, or explicitly define a
continuation-after-completion task mode with scientific justification.

Until that amendment, **Role-Gate remains UNRESOLVED, Architecture Freeze is
NO-GO, and Phase 3A is NO-GO.**
