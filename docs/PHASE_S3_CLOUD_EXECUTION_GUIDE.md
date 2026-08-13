# S3 Cloud Execution Guide

Upload the user-authorized nine-way S3 bundle to
`/root/autodl-tmp` on the AutoDL instance. The bundle is a Git repository
snapshot pinned to commit `5c357e0396276463f7fc87038546bec561166cf4`.

The launcher starts all fixed nine S3 development-only runs concurrently. Each run retains the frozen
4 environments × 64 rollout steps × 782 updates = 200,192 environment steps.
It does not change the frozen per-run configuration. Each process is limited to
one CPU thread; the single GPU is intentionally oversubscribed at the user's
direction. It shuts down only after
all nine manifests report completion; a failure preserves logs and does not
shut down the instance.

The exact shell commands are provided in the user-facing handoff. Results are
stored on `/root/autodl-tmp`, which survives instance shutdown but is not part
of a saved image. Download the resulting archive before deleting the instance.
