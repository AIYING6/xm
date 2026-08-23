# PAPER-Q2 Efficiency Audit

**Status:** partial but publication-safe.

UTR and DRTP have identical 116,728 trainable parameters and use the same Single-Graph actor/critic. DRTP adds no inference-time network or input and changes only the training-time topology-group weighting controller. The retained P3 architecture check stores equal model files of 479,288 bytes for the matched architecture.

No common-hardware, complete wall-clock or peak-memory log supports a fair numerical comparison. Such a comparison is therefore intentionally **not claimed**. The paper may report matched parameter count and training-only controller scope, but must not report invented speedup, GPU-memory, or hardware-efficiency claims.
