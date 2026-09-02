# P2.7 assignment-interface formulation audit contract

## Status

`P2_7_ZERO_TRAINING_AUDIT_ONLY`. P2-R reached
`P2_R_BASE_TASK_NOT_LEARNABLE`: the corrected learner completed one objective
but not both under all ten endpoint policies. P2.7 neither changes that result
nor authorizes a replacement training run.

## Question

Can the task expose a deterministic, role-local terminal-to-objective
assignment cue that breaks interchangeable-terminal symmetry without changing
the physics, topology, failure semantics, reward, action masks, critic,
evaluation information or PPO?

## Candidate interface

For `K` terminals and `K` objectives, order terminal starting lanes and
objective lanes by their fixed initial y-coordinate. Terminal rank `i` receives
one persistent `K`-dimensional preference one-hot whose preferred objective is
the objective with rank `i`.

- This is a task configuration/role-local observation, available from reset.
- It is independent of training seed, faults, future state and every evaluation
  tape.
- It does not restrict any legal action: a terminal may still act on every
  objective for which it has a valid token.
- It does not alter the reward, deadline, graph, automatic relay forwarding,
  centralized critic or failure groups.
- It is scalable: the mapping is derived from ordered lanes, not hard-coded
  agent IDs or a main-scale special case.

## Required zero-training evidence

The audit must establish all of the following:

1. A scripted assignment-consistent trajectory reaches both objectives.
2. A scripted same-objective trajectory reaches only one objective and times
   out, reproducing the partial-completion mode visible in P2-R.
3. The mapping is a bijection at small, main and large scales.
4. The candidate cue is available before terminal action selection, while no
   transition, reward, action-mask or evaluation-tape information is added.

## Outcomes

Only `P2_7_ASSIGNMENT_INTERFACE_FEASIBLE` or `P2_7_ASSIGNMENT_INTERFACE_NO_GO`
may be emitted. A feasible audit permits an implementation-contract review;
it does not authorize implementation, RL training, a seed allocation, P3 or
automatic continuation.
