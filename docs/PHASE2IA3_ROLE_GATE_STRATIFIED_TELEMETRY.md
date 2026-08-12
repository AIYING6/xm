# Phase 2I-A3 Role-Gate stratified telemetry

Existing telemetry was stratified by relation and ordered receiver/sender role pair without new training. Machine-readable output is `results/development/phase2ia3_riskset_audit/stratified_telemetry.csv`.

## Findings

- Relation strata 0, 1, and 2 are present; role-pair strata are retained separately.
- Gate means remain near their configured relation/role priors (approximately 0.4 or 0.5), with very small within-stratum update variation and no predominant 0.05/0.95 saturation.
- Effective payload `alpha × g` varies by relation/role pair with attention means; pooled `alpha–g` correlations from Phase 2I-A2 remain moderate and positive.
- The telemetry supports an active, non-saturated parameterization, but does not establish causal architectural value because strict recovery is unavailable.

This is mechanism evidence only and does not change `Role-Gate retention = UNRESOLVED`.
