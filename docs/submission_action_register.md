# Submission Action Register

Generated: 2026-08-02T01:40:08

Purpose:

```text
Track remaining submission-facing actions separately from reproducibility gates.
Open/deferred/blocked items do not mean the evidence chain is broken; they identify work needed before an actual journal submission.
```

## Summary

```text
items = 10
blocked = 2
deferred = 1
open = 7
```

## Action Items

| ID | Priority | Status | Category | Action | Evidence | Next step |
|---|---|---|---|---|---|---|
| A1 | high | blocked | pdf_validation | Compile Chinese and English LaTeX projects and visually inspect PDFs. | xelatex=missing; latexmk=missing; bibtex=missing | Run xelatex/bibtex in a full LaTeX environment, then inspect tables, figures, captions, references, and page breaks. |
| A2 | high | open | journal_target | Choose the target journal and migrate the English manuscript to its template. | docs/journal_target_shortlist.md and docs/journal_template_migration_plan.md exist. | Select one target venue, then replace the generic article class, bibliography style, declarations, and formatting. |
| A3 | high | open | metadata | Replace author placeholders in Chinese and English manuscripts. | english_placeholder=True; chinese_placeholder=True | Fill author names, affiliations, corresponding author, and acknowledgements after the submission route is chosen. |
| A4 | medium | open | declarations | Add data/code availability statements. | bilingual_manuscript_completeness_audit marks data_availability as action_item. | State which CSVs, scripts, checkpoints, and generated assets can be shared as supplementary material. |
| A5 | medium | open | declarations | Add funding, conflict-of-interest, and author-contribution statements if required. | bilingual_manuscript_completeness_audit marks funding_conflict_statement as action_item. | Use the selected journal's declaration wording and leave unknown funding as 'not applicable' only if true. |
| A6 | medium | open | formatting | Replace generic plain bibliography style with the target journal style. | english_plain_bib=True; chinese_plain_bib=True | Switch BibTeX style or bibliography package after target template migration. |
| A7 | medium | open | supplement | Decide which audit CSVs and result CSVs should be included as supplementary material. | docs/supplemental_data_readme.md lists current CSV inventory and interpretation boundaries. | Keep internal audits out of the journal package unless the venue permits or requests reproducibility supplements. |
| A8 | medium | deferred | statistics | Decide whether to add a larger scenario-depth formal evaluation beyond the completed five-seed Gate 1 package. | Current Gate 1 main evidence already uses five seeds, 100 matched test episodes per seed, and seed-aware hierarchical bootstrap. | Only run a new formal scenario-depth budget if the target venue or adviser requires stronger realism beyond the current 3v1 mechanism package. |
| A9 | medium | blocked | lag_jsbsim | Run real LAG/JSBSim reset/one-step probe before claiming 6DOF validation. | jsbsim_data_missing=True; docs/lag_jsbsim_migration_probe.md records current blocker. | Restore/install LAG envs/JSBSim/data and missing imports, then run a real MultipleCombatEnv smoke test. |
| A10 | high | open | review | Perform adviser/manual technical review of final claims, tables, and figures. | Automated gates pass, but they do not replace expert review. | Review claim_evidence_matrix.md, final main table, appendix diagnostics, and the target journal scope before submission. |

## Use Boundary

```text
Use this register to plan submission work. Do not use it to weaken current evidence boundaries.
The current paper still cannot claim real 6DOF/JSBSim validation until A9 is resolved and new evidence is generated.
```
