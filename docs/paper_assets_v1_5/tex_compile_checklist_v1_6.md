# TeX True-Compile Checklist — v1.6 (journal-agnostic)

- precondition: this machine has NO TeX install. Run on a TeX Live / MiKTeX machine.
- target: compile the canonical `article` manuscript (NOT any publisher template).
- gate: only after PASS here may the tag `paper-v1.6-journal-agnostic-ready` be created.

## 1. Commands (main manuscript)

```bash
cd paper_latex_3d_en
latexmk -C
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

(If latexmk is missing: `pdflatex -interaction=nonstopmode -halt-on-error main.tex` ×2,
then `bibtex main`, then `pdflatex` ×2.)

## 2. Commands (supplementary)

```bash
cd paper_latex_3d_en/supplementary
latexmk -C
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex
```

## 3. Acceptance (from main.log and supplementary.log)

```bash
grep -Ei "undefined|citation.*undefined|reference.*undefined|multiply defined|missing file|error" main.log
```

Required (hard gate):

| check | requirement |
|---|---|
| compile exit code | 0 |
| undefined citations | 0 |
| undefined references | 0 |
| missing files | 0 |
| multiply-defined labels | 0 |

`overfull`/`underfull` boxes: record but do NOT mechanically zero them; judge box by box
at the PDF audit.

## 4. PDF-level human audit (after compile)

- [ ] Table II (RMST 50/80/100/220) renders inside column width, numbers legible
- [ ] KM figure (km_recovery_curve_primary.pdf) readable in grayscale; marker identity works
- [ ] 5 vector figures (PDF) embed correctly; text not clipped
- [ ] Supplementary conditional Pareto (fig_pareto_recovery) caption matches "conditional
      mean recovery time among recovered failure-exposed episodes"
- [ ] Equations (RMST integral, softmax) break cleanly
- [ ] Table I–V numbering is 1..5 in order (held_out, rmst, ablation, robustness, efficiency)
- [ ] References (21 entries) all resolve; no bibtex warnings that change numbering

## 5. Post-verification tags

- After PASS: `git tag paper-v1.6-journal-agnostic-ready` (never overwrite
  `paper-v1.6-survival-locked` / `paper-v1.6-p2-aligned`).
- Until PASS: current tag remains the intermediate `paper-v1.6-p2.5-content-ready`.
