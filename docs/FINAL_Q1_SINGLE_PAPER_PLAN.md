# Final Q1 Single-Paper Plan

Last updated: 2026-07-24

This document is the controlling plan for the current project. If older planning documents conflict with this file, follow this file.

## Target

Produce one high-quality paper:

- target level: Q1 attempt;
- fallback level: solid Q2;
- project style: one focused paper, not an indefinitely expanding air-combat system.

Core research question:

> Under limited communication, intermittent sensing, message loss/delay, and relay-node failure, can a perception-communication-task-support multi-relation role graph improve heterogeneous UAV kill-chain recovery?

The paper should be positioned as a heterogeneous UAV kill-chain resilience method, not as a complete 6DOF red-blue air-combat system.

## Main Scenario

The main statistical evidence remains the 3DOF 3v1 strict-sensing kill-chain recovery task:

- Scout detects the target.
- Relay forwards target information.
- Attacker forms and holds an attack window.
- Red target follows a controlled target policy.
- Relay fails during the episode.
- Remaining UAVs must recover the reconnaissance-information-attack chain.

Required environment properties:

- strict intermittent target sensing;
- communication radius constraint;
- packet dropout;
- message delay;
- message cache, TTL, and confidence;
- relay-node failure;
- target information must propagate through physically valid sensing/communication paths;
- decentralized actor information boundary and centralized critic separation.
- target-prior sensitivity must be diagnosed after validation-selected checkpoints are available; follow `docs/target_prior_ablation_protocol.md`.

## Method Name

Use the main paper name:

> EA-RG-MAPPO: Edge-Aware Multi-Relation Role-Graph MAPPO

`-S`, staged curriculum, reward shaping, rules, demonstrations, ELO, and self-play are training or evaluation support only. They are not primary innovations unless new evidence explicitly supports them.

## Contributions

Contribution 1:

Define a communication-feasible heterogeneous UAV kill-chain recovery problem under strict sensing, message uncertainty, and relay-node failure.

Contribution 2:

Propose a perception-communication-task-support multi-relation role graph that separates sensing reachability, message delivery, and task-support relations instead of mixing them in a single graph.

Contribution 3:

Propose role-pair-conditioned message passing so Scout-to-Relay, Scout-to-Attacker, Relay-to-Attacker, and peer-support messages can be weighted differently during recovery.

Contribution 4, Q1-supporting rather than core:

Validate scenario depth and realism with controlled maneuvering-target, 4v2/5v2 rule-red, and LAG/JSBSim replay evidence after the 3v1 main evidence is scientifically hardened.

## Required Baselines

For the Q1 target, the baseline set is:

- Rule / Geometric Controller;
- IPPO, if the existing MAPPO code path can support it with low risk;
- MAPPO / no-graph CTDE baseline;
- Single-Graph GAT-MAPPO;
- HAPPO-style / heterogeneous sequential PPO as the current external strong-baseline attempt;
- Parameter-Matched Single Graph;
- EA-RG-MAPPO.

The current code path is not to be described as standard HAPPO. It is a HAPPO-style heterogeneous sequential PPO baseline unless the original HAPPO objective and update correction are implemented or a trusted public implementation is integrated. The stop rule is:

> If a standard HAPPO implementation cannot pass smoke, BC compatibility, fair PPO training, and evaluation within 3-5 focused engineering days, report the current baseline honestly as HAPPO-style and proceed with IPPO/MAPPO/Single-Graph/Parameter-Matched Single as the minimum defensible baseline package.

Do not add many external algorithms. One strong external MARL baseline is enough if it is fair and reproducible.

## Required Ablations

Required mechanism ablations:

- w/o Role-Pair Gate;
- w/o Task-Support Relation;
- w/o Explicit Role Identity;
- Parameter-Matched Single Graph.

Optional or appendix-level diagnostics:

- w/o Edge Features;
- no-curriculum;
- scout-failure and delayed scout-failure diagnostics.

## P0 Scientific Validity Gate

Before any long training, finish the following:

1. Replace magic-number observation slices with a documented observation schema.
2. Verify or correct the no-role-identity actor observation slice.
3. Ensure no-role-identity removes explicit role labels from:
   - actor local observation;
   - graph node features;
   - role embedding;
   - role-pair message path.
4. Remove global attack-chain progress from actor graph inputs:
   - `attack_hold`;
   - `attack_hold_steps`;
   - normalized attack-hold progress.
5. Keep attack-chain progress available to the centralized critic and to evaluation metrics.
6. Add actor information-boundary tests:
   - target state changes do not affect actor logits when no sensing, no communication, and no valid cache exist;
   - global attack-hold changes do not affect actor logits;
   - unreachable agents' hidden/target states do not affect actor logits;
   - dropout and delay prevent premature message visibility;
   - stale or low-confidence caches cannot keep the chain valid;
   - relay failure prevents new relay-originated message propagation.
7. Mark all pre-hardening results that violate the above boundary as development evidence only.

P0 is mandatory. Do not launch million-step training before it passes.

## Training Protocol

Use environment interaction steps as the official training budget:

```text
environment steps = num_envs * rollout_steps * updates
```

Maintain three disjoint groups:

- training seeds;
- validation episodes/seeds for checkpoint selection and hyperparameter decisions;
- final test episodes/seeds used only after configuration freeze.

Checkpoint policy:

- save checkpoints at fixed environment-step milestones;
- select checkpoint by validation set only;
- evaluate final test set once after method/configuration freeze;
- do not tune on final test results.

Development budget:

- start with 1M environment steps for MAPPO, Single-Graph, HAPPO, and EA-RG-MAPPO;
- extend to 2M or 5M only if validation curves have not plateaued;
- define a final common budget `B*`;
- train all formal methods to `B*` with comparable logging and checkpoint rules.

Formal training:

- 5 training seeds for main methods;
- 100 matched final test episodes per seed;
- same BC/demo protocol when BC is used;
- same reward, scenario, safety constraints, and evaluation seeds;
- report per-seed scatter, mean, seed standard deviation, and confidence intervals.

## Metrics

Primary metrics:

- kill-chain recovery rate;
- restricted mean recovery time.

Secondary task metrics:

- timeout rate;
- completion time;
- target tracking rate after failure;
- attacker fresh target-cache ratio;
- chain-closed probability;
- communication connectivity.

Safety metrics:

- collision rate;
- minimum blue-blue distance;
- minimum blue-red distance;
- flight-envelope violation rate.

Communication metrics:

- delivered messages;
- dropped messages;
- expired-message ratio;
- active directed communication edges;
- mean message age;
- messages per successful recovery.

All custom metrics must have explicit definitions in the paper or appendix.

## Statistics

Use seed-aware hierarchical bootstrap:

1. resample training seeds;
2. resample matched episodes within each seed;
3. repeat sufficiently many times, normally 10,000;
4. report mean, seed-level spread, and 95% confidence interval.

Use seed-level paired tests only as secondary evidence, with multiple-comparison correction when needed.

Do not treat episodes from the same trained model as fully independent model samples.

## Q1 Scenario-Depth Supplements

After P0 and the formal 3v1 baseline package are stable, add controlled supplements in this order:

1. Maneuvering-target generalization:
   - `weaving_mild` or a revised mild maneuver target;
   - use frozen checkpoints first;
   - promote to paper-facing evidence only if success is not saturated and not collapsed.
2. 4v2/5v2 rule-red extension:
   - scripted/red-rule target and escort or jammer;
   - no full self-play requirement;
   - validate scalability and system complexity, not all-baseline retraining.
3. LAG/JSBSim replay:
   - small reset/step or replay feasibility validation;
   - verify high-level command feasibility, flight envelope, attack-window consistency, and Tacview-style trajectory display;
   - do not train all baselines in JSBSim.

These supplements strengthen Q1 credibility, but the main statistical claim remains the 3DOF strict-sensing relay-failure recovery task unless the extension evidence becomes equally rigorous.

## Not Main Contributions

Do not claim the following as primary innovations:

- reward shaping;
- rule-based policies;
- curriculum schedule alone;
- ELO;
- self-play;
- online missile closed-loop training;
- full 6DOF reinforcement learning;
- high-fidelity radar/electronic-warfare modeling;
- complete red-blue air-combat system.

## Execution Order

P0: scientific validity hardening.

- observation schema;
- no-role-identity correctness;
- actor/critic information boundary;
- attack-hold removal from actor graph inputs;
- information-boundary tests.

P1: unified training protocol.

- configs under `configs/paper/`;
- train/validation/test split;
- environment-step budget logging;
- checkpoint selection by validation;
- required metric schema.

P2: development training.

- MAPPO;
- Single-Graph GAT-MAPPO;
- HAPPO;
- EA-RG-MAPPO;
- 1M steps first, extend only if needed.

P3: formal 3v1 training and evaluation.

- main baselines;
- parameter-matched control;
- mechanism ablations;
- five seeds;
- seed-aware statistics.

P4: Q1 supplements.

- mild maneuver target;
- 4v2/5v2 rule-red extension;
- LAG/JSBSim replay.

P5: paper package.

- training curves;
- failure-aligned mechanism curves;
- representative trajectory/case;
- main tables;
- ablation tables;
- reproducibility package;
- English manuscript and PDF-ready review.

## Stop Conditions

The project is ready for paper writing when:

- P0 information-boundary tests pass;
- main and strong baselines have fair training curves;
- EA-RG-MAPPO is better than Single-Graph or has a clear recovery/safety advantage under seed-aware statistics;
- key ablations degrade in the expected direction;
- HAPPO is either fairly reported or its blocker is documented;
- at least one Q1 supplement is completed without weakening the main claim;
- paper tables, figures, configs, logs, checkpoints, and scripts are reproducible.

If the final evidence only supports Q2, write a strong Q2 paper instead of expanding uncontrolled new modules.
