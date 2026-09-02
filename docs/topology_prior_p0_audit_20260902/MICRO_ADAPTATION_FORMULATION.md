# Bounded micro-adaptation formulation (conditional only)

If a future audit supplies a valid fixed prior `p0`, a mathematically distinct residual sampler could be defined as

`q_t = Project_[floor, cap](p0 + r_t),  sum_g q_t[g]=1,  ||q_t-p0||_1 <= 0.10`.

`r_t` would be a bounded, training-only residual derived from completed training episodes; it must not read any evaluation tape. This document specifies no update rule, threshold, or training run. The current P0 verdict prevents implementation because `p0` has not been justified as topology-informed.
