# Final Manuscript Self-Review

**Scope:** journal-neutral Simplified Chinese manuscript at `paper_chinese/manuscript_zh.md`, its Supplementary, frozen main-figure bundle, active BibTeX source and evidence audits.
**Scientific state:** frozen evidence only; no training, retraining or new evaluation was initiated.
**Overall decision:** `NOT_SUBMISSION_READY` for packaging/compliance reasons, not because a high-severity scientific contradiction was found.

## 18-pass review

| Pass | Status | Evidence / disposition |
|---|---|---|
| 1 Cold Read | PASS | `FULL_MANUSCRIPT_COLD_READ.md` reconstructs the same P1 story as the controlling evidence. |
| 2 RQ Closure | PASS | `RQ_CLAIM_EVIDENCE_CONCLUSION_MATRIX.md`. |
| 3 Innovation Thread | PASS | `INNOVATION_THREAD_AUDIT.md`; Role-Pair removed from the innovation hierarchy. |
| 4 Novelty Stress | PASS | Closest-work matrix prevents first-use claims; contribution is a focused problem–representation–endpoint combination. |
| 5 Scope & Assumption | PASS | 3DOF, nominal held-out, environment-driven communication and transfer limits are explicit. |
| 6 Method & Math | PASS | `METHOD_CODE_TRACE.md`; three relations, static Role-Pair and non-physical communication boundary match code. |
| 7 Protocol & Leakage | PASS | Locked held-out/matched-exposure protocol; OOD was not used to select the P1 endpoint. |
| 8 Baseline & Statistics | PASS | `STATISTICAL_PROVENANCE_AUDIT.md`; seeds are independent training units and RMST80 is the pre-specified P1 endpoint. |
| 9 Claim–Evidence | PASS | Claim ledger and P1/P2/P3 routing constrain every central assertion. |
| 10 Main–Supplement | PASS | Supplementary provenance paths updated to the frozen publication-figure generator. |
| 11 Narrative Strategy | PASS | `NARRATIVE_HIERARCHY.md` and proportionality audit enforce P1→P2→P3→P4. |
| 12 Paragraph & Language | PASS | Results remain question-led; Discussion was revised to interpret rather than repeat numbers. |
| 13 Figure/Table Standalone | PASS | `FINAL_FIGURE_VISUAL_FREEZE.md`; captions define panels, units and metric direction. |
| 14 Citation & Originality | PASS | 9/9 cited keys resolve; `REFERENCE_VERIFICATION_LEDGER.md` and claim-reference matrix define citation scope. |
| 15 Cross-Section Consistency | PASS | `CROSS_SECTION_CONSISTENCY_MATRIX.md` and closure audit find no terminology, number or symbol contradiction. |
| 16 Submission Compliance | CONDITIONAL | Target journal, authorship/affiliations, funding, declarations, data/code statement and final reference style are absent. |
| 17 Clean Build & PDF | CONDITIONAL | The manuscript is an evidence-led Markdown source; no final Chinese journal-template PDF exists for a second end-to-end reader review. |
| 18 Editor + Reviewer Read | CONDITIONAL | Bounded desk/reviewer/supervisor review below; no scientific P0, but final venue packaging remains necessary. |

## Required consolidated checks

```text
MACRO STORY                         PASS
RQ CONSISTENCY                      PASS
INNOVATION THREAD                   PASS
NOVELTY STRESS TEST                 PASS
SCOPE / ASSUMPTIONS                 PASS
METHOD / CODE                       PASS
MATH / NOTATION / DIMENSIONS        PASS
DATA SPLIT / LEAKAGE                PASS
BASELINE COVERAGE / FAIRNESS        PASS
STATISTICAL INTERPRETATION          PASS
CLAIM–EVIDENCE CLOSURE              PASS
RESULT-SELECTION INTEGRITY          PASS
MAIN–SUPPLEMENT CONSISTENCY         PASS
CORE-CLAIM VISIBILITY               PASS
ANTI-LAB-REPORT                     PASS
SCIENTIFIC INSIGHT                  PASS
PARAGRAPH COHERENCE                 PASS
ANTI-AI / LANGUAGE                  PASS
FIGURE/TABLE STANDALONE             PASS
CROSS-REFERENCE CLOSURE             CONDITIONAL
REFERENCE VERIFICATION              PASS
LITERATURE COVERAGE                 PASS
CLAIM–REFERENCE BINDING             PASS
CONTRADICTION SEARCH                PASS
CLOSEST-WORK COVERAGE               PASS
ZOTERO / BIB SYNC                   NOT_APPLICABLE
TEXT ORIGINALITY                    PASS
DRAFT HYGIENE                       PASS
ANONYMIZATION / COMPLIANCE          CONDITIONAL
CLEAN-ROOM REPRODUCIBILITY          PASS
FINAL ARTIFACT PROVENANCE           PASS
PDF VISUAL REVIEW                   CONDITIONAL
EDITORIAL DESK REVIEW               CONDITIONAL
TECHNICAL REVIEWER SIMULATION       CONDITIONAL
SUPERVISOR REVIEW                   CONDITIONAL
```

## Reviewer-style final read

### Reviewer 1 — evidence and statistical emphasis

**Assessment:** The main endpoint is aligned with the fault-duration question, and the manuscript correctly treats three training seeds rather than episodes as independent training repetitions.
**Strength:** Fig. 2 reports the pre-specified RMST80 comparison, seed directions and hierarchical paired-bootstrap interval.
**Concern R1-M1 (minor):** A final formatted manuscript must preserve the recovered-only condition in every rendering of \(t_{rec}\). **Claim pointer:** Table 1/2. **Evidence pointer:** captions and Sections 4.1, 5.1–5.2. **Resolution test:** retain the current conditional column title and notes in the selected venue template.
**Concern R1-M2 (conditional):** Readers need a rendered bibliography and final Supplementary file locations. **Resolution test:** compile the chosen journal source and verify the reference list and links.

### Reviewer 2 — method and claim-moderation emphasis

**Assessment:** The manuscript has a defensible focused positioning because it does not claim graph MARL, learned communication or air-combat graph decision making as first.
**Strength:** The method figure now displays exactly three implemented relations and explicitly separates graph aggregation from physical communication control.
**Concern R2-M1 (minor):** Component results support the design only at the stated empirical level. **Claim pointer:** Section 5.2. **Evidence pointer:** Table 2 and `METHOD_CODE_TRACE.md`. **Resolution test:** retain the present limited wording and keep unavailable Gate-Prior trajectory evidence out of the manuscript.

### Reviewer 3 — reproducibility and engineering-scope emphasis

**Assessment:** The locked nominal evidence supports a controlled-simulation result, not an operational UAV-system claim.
**Strength:** The manuscript transparently keeps full-horizon and OOD boundaries visible without letting them displace the P1 result.
**Concern R3-M1 (conditional):** The scientific package is traceable, but a submission package lacks author metadata, venue-specific data/code disclosure and a final rendered Chinese manuscript. **Claim pointer:** front matter and submission materials. **Evidence pointer:** manuscript blockquote and `PAPER_AUTOPILOT_STATUS.md`. **Resolution test:** author supplies metadata and target venue; production source is compiled and visually reviewed.

### Cross-review synthesis

All three reads support the narrow central claim. Consensus is that the remaining risks are packaging and final-format risks, not an unreported adverse scientific result. The strongest scientific constraint remains unchanged: the evidence establishes earlier nominal-window recovery against MAPPO, not universal full-horizon, OOD or real-platform superiority.

## AUTHOR_DECISION_REQUIRED

1. Select the target Chinese journal and its Word/LaTeX template.
2. Supply author names, affiliations, funding, contributions, conflict statement and data/code availability decision.
3. After the venue is known, produce and visually inspect the final journal-template PDF, including the rendered reference list.

Until these items are resolved, do not set `SUBMISSION_READY_INTERNAL`.
