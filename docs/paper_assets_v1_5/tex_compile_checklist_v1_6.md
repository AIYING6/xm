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

## 4. RQ7 / OOD content checks (added 2026-08-08)

- [ ] `sections/05_experiments.tex` contains RQ7 subsection (zero-shot OOD, protocol v1.1)
- [ ] `tables/table5_ood.tex` is `\input` at the end of RQ7 and renders (wide `table*`)
- [ ] Labels: `tab:ood` unique; `eq:delta_ood` unique; no collision with existing
      `tab:*` / `eq:*` labels (grep `\label\{` in `paper_latex_3d_en`)
- [ ] Table numbering: after adding table5, Tables render 1..6 in order
      (held_out, rmst, ablation, robustness, efficiency, ood) — verify `\ref{tab:ood}`
- [ ] Claim consistency (Gate C, distribution-dependent):
  - Abstract: "distribution-dependent under zero-shot OOD shifts" present; statistical
    detail kept minimal (no `+2.565` in abstract)
  - Discussion: geometry = "preserve part of the benefit"; communication =
    "reverse the comparison"; maneuver/joint = "RMST80 early-window saturation,
    recovery largely fails" with the single M2 MAPPO late-recovery exception stated
  - Conclusion: same wording as Discussion; `+2.565 ± 5.567`, CI, P(Δ<0)=0.175,
    Gate C all present
  - No claim of "generalization across unseen shifts" anywhere

## 5. PDF-level human audit (after compile)

- [ ] Table II (RMST 50/80/100/220) renders inside column width, numbers legible
- [ ] Table VI (OOD, `table5_ood.tex`) fits `table*` width; delta table + family/boot lines legible
- [ ] KM figure (km_recovery_curve_primary.pdf) readable in grayscale; marker identity works
- [ ] 5 vector figures (PDF) embed correctly; text not clipped
- [ ] Supplementary conditional Pareto (fig_pareto_recovery) caption matches "conditional
      mean recovery time among recovered failure-exposed episodes"
- [ ] Equations (RMST integral, softmax, eq:delta_ood) break cleanly
- [ ] Table numbering 1..6 in order (held_out, rmst, ablation, robustness, efficiency, ood)
- [ ] References (21 entries) all resolve; no bibtex warnings that change numbering

## 6. Post-verification tags

- After PASS: `git tag paper-v1.6-journal-agnostic-ready` (never overwrite
  `paper-v1.6-survival-locked` / `paper-v1.6-p2-aligned`).
- Until PASS: current tag remains the intermediate `paper-v1.6-p2.5-content-ready`.
