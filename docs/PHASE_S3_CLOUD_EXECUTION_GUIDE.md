# S3 Cloud Execution Guide

Upload `EA-RG-MAPPO_S3_DEVELOPMENT_5c357e0.bundle` to
`/root/autodl-tmp` on the AutoDL instance. The bundle is a Git repository
snapshot pinned to commit `5c357e0396276463f7fc87038546bec561166cf4`.

The launcher starts the fixed nine S3 development-only runs in two batches:
six concurrent runs, then three concurrent runs. Each run retains the frozen
4 environments × 64 rollout steps × 782 updates = 200,192 environment steps.
It does not change the frozen per-run configuration. It shuts down only after
all nine manifests report completion; a failure preserves logs and does not
shut down the instance.

The exact shell commands are provided in the user-facing handoff. Results are
stored on `/root/autodl-tmp`, which survives instance shutdown but is not part
of a saved image. Download the resulting archive before deleting the instance.
