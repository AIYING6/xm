# B-line P0 scientific contract

## Question

Can two legal multi-UAV histories with the same current geometry, current topology, and remaining mission demand require different **deterministically preferred** reconfiguration decisions because a continuity-relevant transition state differs?

This is independent of TATG-CETM and excludes neural actors, PPO, checkpoints, training, and solver optimization.

## Formal P0 interface

Input is a fixed tuple `(X_t, A_t, M_t, H_t)`: current UAV geometry `X_t`, current communication topology `A_t`, remaining mission demand `M_t`, and an auditable transition summary `H_t` such as consecutive outage duration. Output is one action from a pre-enumerated finite candidate set with a fixed lexicographic tie-break.

P0 freezes `X_t`, `A_t`, and `M_t` across paired cases. Only `H_t` changes. Same input must always produce the same output.

## Minimal continuity hypothesis

If a communication route has a maximum permitted consecutive outage duration, then a newly disconnected route and a persistent disconnected route may have identical current adjacency but different feasibility of deferring reconfiguration. The hypothesis is conditional on that continuity semantics being legitimate for the target system.

## P0 evaluation units

A unit is a paired, hand-specified deterministic instance, not an episode or a training seed. The initial P0 set contains two histories and two candidate actions, with no tuning or search.

## Gate

`B_P0_GO` requires at least two independently justified paired instances with identical `(X_t, A_t, M_t)`, distinct legal histories, different preferred decisions, deterministic byte-identical reruns, and an established match between the tested continuity semantics and the target environment.

`B_P0_CONDITIONAL` applies when the counterexample exists only under an explicit but as-yet unverified system semantic, such as an outage-duration continuity contract.

`B_P0_NO_GO` applies if fixed history cannot change feasibility or the preferred action, or if the distinction arises only from post-hoc objective weights rather than a defensible requirement.

## P0 exclusions

No RL/PPO training, TATG checkpoint, 10M run, solver development, parameter sweep, neural architecture, evaluation tape, or automatic P1 transition is permitted.
