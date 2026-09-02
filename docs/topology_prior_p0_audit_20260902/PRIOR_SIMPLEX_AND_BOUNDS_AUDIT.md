# Prior simplex and bounds audit

For diagnostic purposes only, the duration-normalized vector sums to `1.0`, has range `[0.096154, 0.230769]`, and satisfies the legacy conditional-simplex bounds `[0.05, 0.35]`. Its L1 distance from uniform is `0.217949`.

A conditional L1 micro-adaptation radius of `0.10` is geometrically feasible around that vector: it permits at most `0.05` total probability mass transfer and the bounded simplex is non-empty. This is only a geometry result. It does **not** validate the diagnostic vector as a scientific prior or select a training hyperparameter.
