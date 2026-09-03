# P3-P2 — Frozen Fresh-Seed Static-Topology Pilot

## Scope

This authorized pilot compares only two corrected-learner arms on the independent
training seeds `68011`--`68015` at the fixed 1,000,192-environment-step endpoint
(3,907 PPO updates):

- `utr_scout_terminal_assigned_role_sg_mappo`: uniform sampling over the seven
  existing topology groups at every update;
- `staged_topology_scout_terminal_assigned_role_sg_mappo`: the P3-P1 static
  schedule: updates `[0,977)` nominal only, `[977,2344)` uniform Tier-R, and
  `[2344,3907)` uniform over all seven groups.

The corrected role-specific actors and the opt-in scout/terminal assignment
observation are identical in both arms. Reward, transitions, action masks,
critic, PPO objective, optimizer, model size, rollout budget and evaluation
protocol are unchanged.

## Locked discipline

The schedule is non-adaptive: it reads only the update index and training RNG.
It must not read return, evaluation, gradient, policy, checkpoint or any
seed-outcome label. The development tape is read only after training and cannot
choose a checkpoint, alter a schedule, replace a seed or trigger continuation.

No early stopping, best-checkpoint promotion, rerun, seed replacement, threshold
tuning, independent-cohort run or automatic continuation is allowed.

## Pilot interpretation

The independent unit is the training seed. The pilot reports per-seed endpoint
success, score, collision and timeout on all seven topology groups, plus a
predeclared paired summary. It can only produce `P3_P2_SIGNAL_PASS`,
`P3_P2_NO_SIGNAL`, or `P3_P2_SAFETY_NO_GO`; none authorizes P3-P3 automatically.
