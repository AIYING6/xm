# S0 stabilization seed provenance audit

Status: `PASS — UNUSED_FOR_SCIENTIFIC_RESULTS`

The candidate S1 paired training seeds are `2901`, `2902`, and `2903`.

The audit searched the working tree, retained `results/`, `archival/`,
`artifacts/`, `diagnostics/`, configuration/manifest text, checkpoint-path
names, launch arguments, and all reachable Git history for the seed semantics
`seed2901`--`seed2903`, JSON seed values, and `--seed` arguments. Numeric
coincidences such as update number 2901 were not counted as a seed use.

No prior scientific training, evaluation, debug/smoke result, checkpoint,
manifest, or abandoned scientific run was found for any of the three values.
They are therefore clean *development* seeds only. They are neither canonical
nor held-out/confirmatory seeds.

This audit does not authorize a run. If any contrary provenance is found before
launch, S1 is `S0_NOT_READY`; a replacement seed may only be proposed and
audited, never silently substituted.
