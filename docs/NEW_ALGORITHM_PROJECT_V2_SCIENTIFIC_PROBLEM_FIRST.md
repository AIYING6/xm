# New Algorithm Project V2: scientific-problem-first charter

Status: `PROJECT_V2_MAJOR_REDESIGN_AUTHORIZED__PAPER_FIRST__NO_MORE_MICRO_PATCHING`

The next paper project is independent of the current UAV benchmark.  The
scientific problem must be selected before choosing an environment or reusing
the UAV platform.

## Entry requirements

Each surviving candidate problem must have:

1. a concrete 2024--2026 literature gap;
2. a mechanism that is more than a renamed module combination;
3. a simple falsifiable benchmark before large-scale implementation;
4. a clear actor-information and estimator contract;
5. a path to fair baselines and mechanism-level evidence;
6. a natural decision about whether the current UAV platform is suitable.

The project may use the UAV platform only after the scientific problem is
independently justified.  If a better benchmark is required, the benchmark may
be changed rather than distorting the problem to fit existing code.

## Current authorization

The previous literature-first candidate search is closed.  The next stage is
`V2-R0_MULTI_TASK_HETEROGENEOUS_UAV_MAJOR_REDESIGN`: freeze a larger
multi-task, capability-constrained, physically completed UAV specification
before implementation or training.  This is a major redesign, not a repair of
the single-target task.  The detailed specification is in
`docs/V2_R0_MULTI_TASK_HETEROGENEOUS_UAV_MAJOR_REDESIGN.md`.

No algorithm implementation or training is authorized at R0.  After the
specification is frozen, exactly one direct-neighbor review (R1) and one
scripted/oracle feasibility review (R2) are allowed before baseline
learnability.  If the task construct fails, close or redesign it once; do not
re-enter an unbounded micro-patch loop.
