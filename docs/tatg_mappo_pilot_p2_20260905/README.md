# TATG-MAPPO pilot P2 runner implementation

Status: `TATG_PILOT_P2_RUNNER_IMPLEMENTED`.

This directory records a source-only audit of the frozen four-arm pilot
execution interface.  The runner is `scripts/run_tatg_mappo_pilot_single.py`.
It preserves the registered 4-environment by 64-step fixed-UTR layout and
contains no evaluation-tape reader.

The status is implementation-only: no pilot trajectory, local training,
cloud training, or endpoint evaluation has started.  A separate explicit cloud
execution authorization and a distinct endpoint-only evaluator remain required.
