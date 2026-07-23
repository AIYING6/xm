# Q1 Three-Stage Execution Plan

Last updated: 2026-07-22

## Governing Route

The project now follows this staged route:

1. Finish the current Gate 1 manuscript/evidence package.
2. Promote `nominal weaving_mild` into a formal scenario-depth experiment.
3. Only after the first two stages are stable, evaluate a small realism supplement through 4v2/5v2 or LAG/JSBSim replay.

This plan is designed to improve paper quality without wasting the current Gate 1 experiments. The Gate 1 evidence remains the core mechanism proof; later stages are extensions, not replacements.

## Stage 1: Gate 1 Manuscript Package Closure

### Objective

Make the strict-sensing dropout-relay Gate 1 package internally consistent, reproducible, and ready for journal-template migration.

### Claim Boundary

Defensible claim:

> Under strict intermittent sensing, target-information bottleneck, communication dropout, and relay-node failure, multi-relation role-graph reasoning with role-pair-conditioned message passing improves heterogeneous UAV kill-chain recovery reliability.

Do not claim:

- topology curriculum as a primary contribution;
- full 4v2 red-blue air-combat validation;
- online missile/radar closure;
- real 6DOF/JSBSim validation;
- self-play/ELO contribution.

### Required Closure Checks

- English 3D manuscript readiness audit has zero hard errors.
- LaTeX reference/static check passes.
- Paper-claim consistency check passes.
- Paper text-risk check passes.
- Reproducibility artifact check passes.
- Gate 1 communication-feasibility regression tests pass.
- Submission package manifest points to the current `paper_latex_3d_en/` artifacts.
- Open submission items are separated from experiment readiness items.

### Current Status

Mostly complete. Remaining blockers are not core experiment blockers:

- PDF rendering cannot be verified locally because the LaTeX toolchain is missing.
- Author/funding/data-availability/journal-template fields require user/adviser input.
- Real LAG/JSBSim validation remains blocked by missing JSBSim data/submodule.

### Exit Criteria

Stage 1 is considered closed when:

- all automated checks pass;
- the manuscript package contains no outdated contribution or no-curriculum wording;
- `docs/submission_action_register.md` lists only human/template/environment items as open or blocked;
- `docs/PROJECT_STATE.md` and `docs/ROADMAP.md` both mark the next technical stage as `nominal weaving_mild` formalization.

## Stage 2: Formal `nominal weaving_mild` Scenario-Depth Experiment

### Objective

Convert the current maneuvering-target development evidence into a formal scenario-depth section.

Current development signal:

- validation-selected nominal `weaving_mild`;
- `multi_relation` success around 63.3%;
- `single` around 11.1%;
- `no_graph` around 0.0%;
- zero collisions in the current development test.

This is promising but not yet the same quality level as Gate 1.

### Formalization Plan

Use a frozen protocol before any new formal run:

- methods: `no_graph`, `single`, `multi_relation`;
- optional capacity-control single-graph only if runtime allows;
- same oracle-assisted BC route across methods;
- same PPO budget across methods;
- fixed validation split for checkpoint selection;
- disjoint final test split;
- no tuning on final test split;
- five training seeds if compute permits, otherwise three seeds clearly labeled as development;
- seed-aware hierarchical bootstrap;
- report success, attack-window formation, collision, timeout, minimum distance, and episode steps.

### Acceptance Gate

Promote `nominal weaving_mild` to paper-facing scenario-depth evidence only if:

- `multi_relation` reaches roughly 60%-80% success or better;
- collision remains near zero;
- `multi_relation` clearly exceeds both `single` and `no_graph`;
- the test split is not reused for tuning;
- the protocol and selected checkpoints are documented.

### Non-Goals

Do not add strict sensing, relay failure, escort, jammer, missile, or 6DOF during Stage 2. The point is to prove maneuvering-target scenario depth cleanly, not to create a new hard task that collapses training.

## Stage 3: Small Realism Supplement

### Objective

Add one limited realism bridge after Stage 1 and Stage 2 are stable.

Candidate A: small 4v2/5v2 scripted-red scenario.

- Best if the target journal emphasizes multi-UAV team complexity.
- Keep red policy rule-based or lightly scripted.
- Do not introduce full self-play/ELO as a core claim.
- Use a small evaluation-only transfer or short fine-tuning budget.

Candidate B: LAG/JSBSim replay.

- Best if the target journal emphasizes flight realism.
- Use high-level policy replay/control feasibility, not full baseline retraining.
- Verify reset/step, trajectory feasibility, attack-window consistency, and visualization.
- Do not claim full 6DOF training unless actually trained and evaluated.

### Selection Rule

Choose only one first:

- If Stage 2 is strong and reviewers may ask for dynamics realism, choose LAG/JSBSim replay.
- If Stage 2 is strong and reviewers may ask for team/task scale, choose small 4v2/5v2.
- If Stage 2 is weak, do not start Stage 3; fix Stage 2 or submit with Gate 1 as a Q2-focused paper.

## Immediate Next Action

Complete Stage 1 closure:

1. rerun the updated readiness/action/manifest generators;
2. rerun manuscript and reproducibility checks;
3. update `PROJECT_STATE.md`, `ROADMAP.md`, and `NEXT_THREAD_TEMPLATE.md`;
4. then start a frozen-protocol document for formal `nominal weaving_mild`.
