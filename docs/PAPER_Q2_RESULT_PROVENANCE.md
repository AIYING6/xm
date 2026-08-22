# PAPER-Q2 Result Provenance

The machine-readable version is `artifacts/paper_q2_p1/result_provenance.json`.

| Paper object | Source | Contract | Aggregation |
|---|---|---|---|
| Table 2 | T1 reference, DRTP development, DRTP held-out reports | T1 1M; DRTP 3M; DRTP held-out 10M | pooled seed means within each contract only |
| Table 3 / Fig. 6 | `DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md` | paired historical seed audit | DRTP−UTR by training seed |
| Fig. 1/2 | S1B/S2 mechanism reports | S2 frozen | topology/path telemetry |
| Fig. 7 | held-out v2 audit | 2001–2003, 10M | all safety/exposure rows retained |
| Supplement | FL/G0/negative-method reports | separate diagnostic contracts | limitation/negative evidence |

## Non-comparable sources

`paper_latex_3d_en/main.tex` and `results/gate1_safety_fx60_paper_tables/` belong to the legacy recovery/fx60 evidence chain. They must not supply a DRTP table, figure, or claim.

## Contract rule

Every manuscript number must retain method, training seed, budget, tape/condition, checkpoint rule, evaluator/aggregation source, and commit/hash where available. Development and held-out evidence are never silently pooled as one confirmatory sample.
