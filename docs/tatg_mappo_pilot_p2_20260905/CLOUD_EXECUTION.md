# TATG pilot cloud training package

The package is training-only. It launches exactly the twelve frozen pilot
trajectories: four arms by three seeds, with 4 environments and 64 rollout
steps per update. It never reads the offline development tape and does not
evaluate, aggregate, select checkpoints, or start a successor phase.

The cloud launcher dynamically fills up to `MAX_PARALLEL` slots. On a
single-GPU machine, choose the largest value that does not cause GPU-memory
pressure; setting it higher changes wall time only, not the registered
trajectory definitions. The separate endpoint-only evaluation interface is
intentionally not packaged as a training continuation.
