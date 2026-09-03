# P4-P0 — C-Group Headroom and Role-Assignment Attribution Audit

## Scope

This is a post-training diagnostic only. It reads the retained 1M checkpoints
from the completed P3-P2 UTR and static-schedule trajectories (`68011`--`68015`)
and evaluates only the frozen C topology groups: `C_relay_node`, `C_balanced`,
`C_cross`, and `C_same_relay`.

The diagnostic tape is frozen at 24 episodes per `(arm, seed, group)` and uses
the separate seed namespace `960000+`. It is not used by training, checkpoint
selection, sampling, parameter changes, or an online controller.

## Recorded observables

For each episode the audit records success, timeout, collision, completed
objectives, raw scout/terminal non-idle action rate, and assignment-consistent
non-idle action rate. The assignment measures are descriptive behaviour
observables, not causal proof of credit assignment.

## Predeclared decision rule

The training seed is the independent unit. A C-group headroom signal requires
at least three UTR seeds with mean C-group success below `0.75`. Among those
seeds, an assignment-attribution candidate requires at least three with either
scout or terminal assignment-consistent non-idle action rate at most `0.50`.

Possible outputs are `P4_P0_CREDIT_ASSIGNMENT_CANDIDATE`,
`P4_P0_HEADROOM_WITHOUT_ASSIGNMENT_MECHANISM`, or `P4_P0_NO_C_HEADROOM`.
No output authorizes a new algorithm, training, tuning, replication, or
automatic continuation.
