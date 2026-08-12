# Survival v2 Validation Report

Status: implementation and synthetic validation completed; third-party reference validation blocked by missing standard survival package in the configured environment.

## Implemented

- Independent grouped-time Kaplan–Meier implementation.
- RMST integration with explicit horizon handling.
- Correct removal of both events and censorings from the risk set at tied times.
- Tau-specific observed deltas.
- Synthetic tests for no censoring, all censoring, all events, horizon censoring, event/censor ties, monotonic KM, and tau sensitivity.

## Historical implementation findings

The historical survival v1.1 script has two findings requiring correction before its outputs can be called canonical:

1. Its risk-set update subtracts events but not censorings at the same time point.
2. Its hierarchical-bootstrap `observed_delta` is computed once from the primary tau and reused for every sensitivity tau.

The old RMST/KM outputs are therefore retained as legacy evidence only. They must not be overwritten or silently relabeled as v2 results.

## External reference blocker

The configured `cac` environment does not contain `lifelines`, `scikit-survival`, `statsmodels`, or R. Installing `lifelines` failed because the configured package mirror could not pass SSL verification. A third-party numerical cross-check is required before Gate B can be marked passed.

## Current decision

Statistical Gate B: **NO-GO** for updating headline survival numbers. The v2 implementation is ready for cross-validation, but canonical empirical RMST/KM tables must wait until the strict endpoint fields and a standard reference implementation are available.
