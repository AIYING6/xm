# Mechanism logging invariance report

**Status:** NO-GO / implementation pending.

The current evaluator records compact environment info but has no explicit OFF/ON mechanism logging switch and no paired deterministic replay harness. Therefore identical action sequence, trajectory, endpoint times, and exogenous realization under logging OFF/ON have not been demonstrated. Mechanism logging must be added and tested before Gate M can pass.
