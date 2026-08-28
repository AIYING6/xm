# Recommended B3 pilot horizon

The frozen first stage is **1,000,192 environment steps per trajectory**.
Archived paired training-return proxy separation appears by 0.384M steps, so
1M is a meaningful horizon for the stated mechanism hypothesis.

After 1M, only these rulings are permitted:

- `MECHANISM_CANDIDATE`: a time-leading, DRTP-specific, multi-layer candidate
  appears in at least 2/3 DRTP seeds; the same six runtime states may be
  strictly continued to 3M.
- `MECHANISM_HYPOTHESIS_NO_GO`: valid trajectories and telemetry show no such
  repeatable chain; close this mechanism hypothesis.
- `INCONCLUSIVE_TIME_HORIZON`: only a pre-recorded observational obstruction,
  not an unfavorable score or absent signal, may justify this status.

There is no 2M stage. 3M is conditional, strict-continuous follow-on only;
10M is not authorized by this preparation.
