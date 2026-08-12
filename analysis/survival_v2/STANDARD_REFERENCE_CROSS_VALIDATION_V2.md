# Standard survival reference cross-validation v2

**Status: Gate B1 NO-GO pending an executable third-party reference.**

## Required independent reference

The project v2 implementation is in `analysis/survival_v2/reference_survival.py`. A clean-environment check was performed in the configured `cac` environment and in the isolated `cac_clean` environment. `lifelines`, `scikit-survival`, and `Rscript` were unavailable. Attempts to install a reference package through normal SSL verification failed; SSL verification was not disabled.

Therefore no third-party numerical agreement is claimed in this commit. The existing local synthetic tests remain useful regression tests but cannot close Gate B1.

## Required test matrix

The validation harness must execute both implementations on: no censoring, all censoring, all events, horizon censoring, event/censor ties, multiple ties, every frozen tau, and the empirical episode dataset. It must report package/version, input hash, output hash, absolute error, relative error, and tolerance.

The frozen tolerance is `1e-10` absolute for KM probabilities and `1e-10` absolute for RMST on deterministic synthetic inputs; empirical comparisons use the same deterministic tolerance after identical preprocessing.

The executable harness is `analysis/survival_v2/validate_standard_reference.py`. It fails closed when `lifelines` is missing and never substitutes the historical survival v1.1 implementation.
