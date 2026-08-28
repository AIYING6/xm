# Save/resume validation report

Status: `PASS`.

An uninterrupted two-update telemetry run was compared byte-for-state with a
one-update run saved mid-window and strictly resumed for its next update. The
final runtime checkpoints, PPO CSV, and DRTP sampler CSV were exactly equal.
The persisted runtime state includes the telemetry buffer and its episode
state, so failure-relative windows cannot be silently reset at a checkpoint.
