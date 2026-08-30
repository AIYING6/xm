# B1-Lite execution note

The full frozen B1 endpoint evaluation was stopped for compute reasons after
partial progress.  Its partial rows must not be used as scientific evidence.

B1-Lite is a separate, zero-environment descriptive analysis of the already
completed 320 frozen short branches.  It reads branch checkpoints and their
training logs only.  It does not resume training, run evaluation episodes,
select checkpoints, or authorize Reliable-DRTP.  Any later endpoint check
requires a new frozen protocol before execution.
