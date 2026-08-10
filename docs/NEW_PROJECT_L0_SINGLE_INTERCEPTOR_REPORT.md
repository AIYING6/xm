# L0 Single-Interceptor Learnability Report

## Final verdict

`L0_NO_GO__PHYSICS_REACHABLE_BUT_VANILLA_RL_LEARNABILITY_NOT_ESTABLISHED`

This development stage was authorized only to test the smallest mission task;
it is not paper evidence and does not authorize L1 or N3.

## Protocol

L0 used one attacker and one target, the existing 3DOF dynamics, the guidance-
level action interface, unchanged `engage_commit`, four-step neutralization
hold, failure precedence, reward, and RMTN180 endpoint. Scout, relay,
communication, cache, delay, packet loss, and failure were absent. The target
was fixed to `straight` after the initial evasive-target reachability check
failed for the single-attacker configuration.

Two vanilla MAPPO seeds were trained for 60 updates and evaluated on 32 fixed
episode seeds. Random, scripted, and true-state oracle controllers were run on
the same population.

## Results

| controller | geometry entry | neutralization | RMTN180 |
|---|---:|---:|---:|
| random | 2/32 (6.25%) | 1/32 (3.125%) | 175.94 |
| scripted legal heuristic | 32/32 | 32/32 | 54.19 |
| true-state oracle | 32/32 | 32/32 | 52.97 |
| vanilla MAPPO seed 8101 | 0/32 | 0/32 | 180.0 |
| vanilla MAPPO seed 8102 | 0/32 | 0/32 | 180.0 |

The initial L0 configuration with an evasive target also produced oracle 0/32,
so it was retained only as a reachability-failed diagnostic and not used for
the final learnability decision. The corrected straight-target L0 establishes
that the mission is physically reachable and nontrivial, while both learned
seeds fail to enter geometry at all.

## Decision

The smallest single-interceptor task is reachable but does not establish
repeatable vanilla-RL learnability under the frozen 60-update development
budget. Per the author gate, stop before restoring heterogeneous agents or
communication. Do not add another task-interface repair, change reward/physics,
increase budget, design a method, or enter L1/N3 without a new author decision.

Artifacts:

- `results/new_project_l0_single_interceptor_v2/L0_MANIFEST.json`
- `results/new_project_l0_single_interceptor_v2/summary.csv`
- `results/new_project_l0_single_interceptor_v2/L0_VERDICT.json`
