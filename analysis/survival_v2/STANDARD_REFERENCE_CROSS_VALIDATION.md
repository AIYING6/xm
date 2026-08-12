# Standard Reference Cross-Validation

Status: **NO-GO / external library unavailable**

## Required reference

The protocol requires numerical comparison against `lifelines`, R `survival`, or `scikit-survival`.

## Environment checks

| Environment | Standard library | Result |
|---|---|---|
| `cac` | `lifelines`, `scikit-survival`, `statsmodels`, R | unavailable |
| `cac_clean` | `lifelines`, `scikit-survival`, `statsmodels`, R | unavailable |
| PyPI install | `lifelines==0.27.8` | blocked by SSL verification failure in configured mirror and PyPI |
| Conda package cache | lifelines/scikit-survival packages | not present |

SSL verification was not disabled and no unsafe installation workaround was used.

## Local cross-validation available

The independent v2 implementation is covered by synthetic tests in `analysis/survival_v2/tests/`:

- no censoring;
- all censoring;
- all events;
- horizon censoring;
- event/censor ties;
- tau sensitivity;
- monotone KM survival.

These tests are necessary but do not substitute for third-party validation.

## Empirical dataset

Empirical cross-validation is blocked for two independent reasons:

1. No standard survival package is installed in the available environments.
2. The recovered historical episode package does not contain checkpoint bytes and lacks the strict pre-failure endpoint fields required by Protocol v2.

## Gate decision

Gate B remains **NO-GO**. Do not label v2 empirical RMST/KM outputs canonical until a standard reference environment is available and the empirical endpoint schema is complete.
