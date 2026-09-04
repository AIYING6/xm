# TATG-MAPPO fresh-seed pilot P0

This is the pre-execution contract for TATG's first and only directional
development pilot. It does not implement or start training.

- Three new matched seeds: `75011–75013`.
- Four arms: snapshot UTR, CETM-UTR, capacity-matched snapshot-GRU-UTR and
  zero-residual-CETM-UTR.
- Each trajectory has the fixed endpoint of 3,907 updates / 1,000,192
  environment steps under the same fixed UTR exposure.
- The fixed post-training development tape contains five conditions and 100
  common base episodes each; it has no online training input.

Only `TATG_PILOT_P0_PREREGISTRATION_READY` lets the user separately authorize
the 12-trajectory execution. A directional result would still require an
independent five-seed replication; it cannot be reported as a reliability
claim by itself.
