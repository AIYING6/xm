# Pre-training state reconciliation

**Baseline commit:** `6e4703ae7f4a30699ea465e901f9688b263fdaf`  
**Reconciliation date:** 2026-08-12  

The local Wave 1 launcher did execute partial optimization steps and wrote partial checkpoints/logs for Full and MAPPO. It was then stopped by explicit user request. It did **not** complete the frozen formal budget, validation checkpoint selection, canonical test evaluation, or survival analysis.

Therefore the unambiguous provenance state is:

```text
FORMAL_OPTIMIZATION_PARTIAL / NOT A COMPLETED CANONICAL RESULT
```

The partial artifacts are preserved under `results/canonical_v2/formal/wave1/` and the stop is recorded in `results/canonical_v2/manifests/wave1/run_incident_log.csv`. No partial metric, checkpoint, or log is promoted as a canonical result. No canonical performance result was inspected or reported.
