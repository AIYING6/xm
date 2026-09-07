# DRTP journal-ready missing-evidence checklist

This checklist records only evidence needed to turn the manuscript from a submission-oriented draft into a final submission package. It is not a request to reopen algorithm development or to rerun completed A/B, OOD, or PLR experiments.

## Required before a cross-scale claim

| Item | Status | Required frozen artifact | Manuscript action |
|---|---|---|---|
| Formal six-UAV UTR/DRTP endpoint | running | Five fresh seeds per arm; fixed endpoint aggregates; success, timeout, collision, perturbed return, and paired deltas | Populate RQ4, Table 4, Figure 6, and only then update the abstract/discussion/conclusion cross-scale wording |

## Required for final production quality

| Item | Status | Required artifact | Manuscript action |
|---|---|---|---|
| Runtime and resource overhead | pending short benchmark | Matched-hardware wall-clock per one million environment steps, peak GPU memory, sampler-update cost, and parameter counts | Populate the computational-overhead paragraph and supplementary runtime table |
| Citation verification | pending | Verified authors, title, venue, volume, pages, DOI, and in-text mapping | Convert anchor references to the target journal style |
| Final figure rendering | pending source CSV staging | Source-data manifest and reproducible plotting script | Render Figures 1–6 using the approved figure plan; do not redraw or hand-enter numerical data |

## Known submission risk: component ablation

The completed evidence distinguishes DRTP from UTR and compares it with a matched PLR-style allocator, but it does **not** yet contain a formal frozen component ablation of the nominal anchor, topology grouping, or bounded-simplex constraint. Table 5 is intentionally marked `TBD`. Before submitting to a venue that requires a mechanism ablation, either:

1. execute one pre-registered, matched ablation protocol; or
2. retain Table 5 as a limitation and target a venue where the completed independent-cohort, OOD, external-comparator, and six-UAV evidence is sufficient for the stated algorithmic claim.

No ablation result may be inferred from sampler logs or from post-hoc changes to the completed cohorts.

## Do not reopen

- The frozen A/B cohorts;
- fixed OOD tapes;
- completed PLR external comparison;
- Original DRTP hyperparameters;
- development-only EGTR or GA-EGTR variants.

The final paper's central statement remains: **DRTP demonstrates repeated cohort-level robustness gains over UTR under the evaluated frozen topology-failure settings.**
