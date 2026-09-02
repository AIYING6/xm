# C2-M3 1M fixed post-hoc evaluation contract

**Status:** `M3_1M_POSTHOC_EVALUATION_AUTHORIZED`.

This cloud-only stage evaluates the newly produced 625k, 750k, 875k and 1M
checkpoints from the existing 20 trajectories. It reuses exactly the frozen
50-episode, five-condition development tape from the 500k post-hoc stage:
20 trajectories × 4 checkpoints × 5 conditions × 50 episodes = 20,000
evaluation episodes.

Training is forbidden. The evaluation cannot alter checkpoints, choose a best
checkpoint, change methods, access formal/held-out tape, or start any further
continuation. The two cohorts remain separate in the longitudinal report.

The automatic output is evidence readiness only. A mechanism claim, a new
algorithm, or any action after 1M requires a separate human scientific review.
