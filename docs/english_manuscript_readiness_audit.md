# English Manuscript Readiness Audit

Generated: 2026-07-16T22:21:38

Purpose:

```text
Audit the English LaTeX manuscript for submission-facing structure, evidence boundaries, and low-cost action items.
This report does not replace journal-template compilation or adviser review.
```

## Summary

| Item | Value |
|---|---:|
| Title words | 13 |
| Abstract words | 200 |
| Main-text words, excluding appendix | 3187 |
| Total words, including appendix | 4288 |
| LaTeX files checked | 9 |
| Hard errors | 0 |
| Action items | 4 |

## File Statistics

| File | Lines | Words | Tables/inputs | Figures | Cite commands |
|---|---:|---:|---:|---:|---:|
| `main.tex` | 41 | 259 | 0 | 0 | 0 |
| `sections/01_introduction.tex` | 20 | 613 | 0 | 0 | 4 |
| `sections/02_related_work.tex` | 23 | 514 | 0 | 0 | 9 |
| `sections/03_problem.tex` | 22 | 396 | 0 | 0 | 0 |
| `sections/04_method.tex` | 66 | 558 | 0 | 1 | 0 |
| `sections/05_experiments.tex` | 47 | 574 | 3 | 2 | 0 |
| `sections/06_discussion.tex` | 17 | 404 | 0 | 0 | 0 |
| `sections/07_conclusion.tex` | 3 | 128 | 0 | 0 | 0 |
| `sections/08_appendix_experiments.tex` | 115 | 842 | 7 | 9 | 0 |

## Hard Errors

None.

## Submission Action Items

- Replace the author placeholder in paper_latex_en/main.tex.
- Add a Data/Code Availability statement after the target journal is selected.
- Add funding, conflict-of-interest, and author-contribution statements if required by the journal.
- Replace the generic plain bibliography style with the selected journal template style.

## Notes

- Air-combat/radar/missile/human-UAV terms occur 13 times; keep them in limitations/future-work context.
- PDF rendering is not verified in the current runtime because xelatex/latexmk/bibtex are unavailable.

## Recommended Next Edit

```text
For Drones/Aerospace/JIRS first submission: keep the current technical core, replace the generic article class with the target template,
add required declarations, and avoid turning future 6DOF/radar/missile extensions into current experimental claims.
```
