# S2 versus prior-plus-adaptation audit

S2 begins from an adaptive DRTP target, projects it, mixes it with a 0.20 uniform anchor, then applies a final L1 trust region. A valid prior-plus-micro method would instead anchor all residual motion to a **fixed, non-uniform, independently defined** `p0` and bound distance from `p0` directly.

The formulas would be distinguishable only if `p0` is genuinely structural. The present audit cannot establish that condition: the static relay-deletion topology is identical across all groups, while dynamic connectivity is trajectory-dependent. Therefore this is not yet a novelty claim and cannot be presented as an S2 replacement.
