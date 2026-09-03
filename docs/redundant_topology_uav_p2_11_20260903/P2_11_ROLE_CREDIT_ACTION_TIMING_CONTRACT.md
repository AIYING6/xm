# P2.11 — role credit and action-timing forensic contract

## Purpose

P2.9 established that the corrected assigned-observation baseline does not
learn the base task. P2.10 established that the terminal preference cue is
present in the interface but does not yield a single minimal interface defect.
P2.11 identifies whether the retained final policies collapse at Scout target
coverage, Terminal target selection after information becomes legal, or neither.

## Frozen inputs and probes

- only the ten retained P2.9 `runtime_1m.pt` checkpoints;
- a one-step scripted support setup: Scout 0 senses objective 0 and Scout 1
  senses objective 1 while terminals remain idle;
- one masked, deterministic policy forward pass at the next state;
- fixed three-step, non-learning action scripts for full coordination, same-target
  behavior, Scout ablation, and Terminal ablation.

The policy probe does not execute the policy's selected action. The fixed
scripts exist only to inspect action timing, completion consequences, and
whether the environment broadcasts a common reward. They are not evaluation
episodes and never read an evaluation tape.

## Forbidden operations

- PPO rollout, update, training, checkpoint selection, score comparison, or
  formal/development/held-out evaluation;
- any reward, transition, observation, mask, learner, or source modification;
- any automatic continuation.

## Required outputs

- `P2_11_FINAL_POLICY_ACTION_PROBE.csv`;
- `P2_11_FIXED_SCRIPT_COUNTERFACTUALS.csv`;
- `P2_11_ROLE_CREDIT_REPORT.md`;
- `P2_11_FINAL_VERDICT.md`.

## Interpretation boundary

This is a causal interface diagnosis, not a new performance claim. Its outcome
may identify a candidate location for a future minimal repair, but never
authorizes that repair or P3 automatically.
