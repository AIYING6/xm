# English Manuscript Readiness Audit

Generated: 2026-08-12T12:01:21

Purpose:

```text
Audit the English LaTeX manuscript for submission-facing structure, evidence boundaries, and low-cost action items.
This report does not replace journal-template compilation or adviser review.
```

## Summary

| Item | Value |
|---|---:|
| Title words | 13 |
| Abstract words | 243 |
| Main-text words, excluding appendix | 6256 |
| Total words, including appendix | 6561 |
| LaTeX files checked | 8 |
| Hard errors | 9 |
| Action items | 4 |

## File Statistics

| File | Lines | Words | Tables/inputs | Figures | Cite commands |
|---|---:|---:|---:|---:|---:|
| `main.tex` | 40 | 305 | 0 | 0 | 0 |
| `sections/01_introduction.tex` | 16 | 481 | 0 | 0 | 0 |
| `sections/02_related_work.tex` | 29 | 676 | 0 | 0 | 20 |
| `sections/03_problem.tex` | 18 | 337 | 0 | 1 | 0 |
| `sections/04_method.tex` | 94 | 1278 | 0 | 1 | 0 |
| `sections/05_experiments.tex` | 122 | 2126 | 0 | 3 | 0 |
| `sections/06_discussion.tex` | 53 | 964 | 0 | 0 | 0 |
| `sections/07_conclusion.tex` | 9 | 394 | 0 | 0 | 0 |

## Hard Errors

- missing evidence-boundary marker: training protocol in this paper, not as a primary contribution
- missing evidence-boundary marker: nor does it claim full-system 4v2 red-blue air-combat validity
- missing evidence-boundary marker: future scenario-depth work
- missing evidence marker: fixed-budget checkpoint rule
- missing evidence marker: five training seeds
- missing evidence marker: 100 matched test episodes per seed
- missing evidence marker: 88.6\%
- missing evidence marker: role-pair-conditioned message gating
- missing evidence marker: 100 matched test episodes per seed

## Submission Action Items

- Replace the author placeholder in paper_latex_3d_en/main.tex.
- Add a Data/Code Availability statement after the target journal is selected.
- Add funding, conflict-of-interest, and author-contribution statements if required by the journal.
- Replace the generic plain bibliography style with the selected journal template style.

## Notes

- Air-combat/radar/missile/human-UAV terms occur 14 times; keep them in limitations/future-work context.
- PDF rendering is not verified in the current runtime because xelatex/latexmk/bibtex are unavailable.

## Recommended Next Edit

```text
For Drones/Aerospace/JIRS first submission: keep the current 3DOF Gate 1 technical core, replace the generic article class with the target template,
add required declarations, and avoid turning future 6DOF/radar/missile extensions into current experimental claims.
```
