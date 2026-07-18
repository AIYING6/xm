# Submission Readiness Report

Generated: 2026-07-16T22:21:38

## Summary

```text
Research manuscript package is internally consistent and evidence-backed.
Not final submission-ready in this runtime because PDF rendering cannot be verified without a LaTeX toolchain.
Current strongest claim: EA-RG-MAPPO-S improves limited-communication stability and reduces collision in simplified 2D heterogeneous UAV pursuit.
Boundary: full 6DOF air combat, missile/radar modeling, and human-UAV teaming have not been experimentally validated yet.
```

## Main Evidence

| Radius | EA-RG-MAPPO-S Success | EA-RG-MAPPO-S Collision |
|---:|---:|---:|
| 4 | 0.926 ± 0.004 | 0.054 ± 0.007 |
| 6 | 0.919 ± 0.012 | 0.064 ± 0.006 |
| 8 | 0.890 ± 0.021 | 0.083 ± 0.012 |
| 10 | 0.879 ± 0.017 | 0.086 ± 0.020 |

## Material Coverage

| Category | Present | Missing |
|---|---:|---:|
| Manuscripts | 4 | 0 |
| Result evidence | 8 | 0 |
| Reproducibility gates | 16 | 0 |

## Missing Internal Artifacts

None.

## Quantitative Warnings

None. Final EA-RG-MAPPO-S success/collision values satisfy the current readiness thresholds.

## Runtime and Submission Limitations

- xelatex is not available in the current runtime
- latexmk is not available in the current runtime
- bibtex is not available in the current runtime
- PDF layout has not been verified in the current runtime.
- Journal-specific template formatting has not been performed.
- Real LAG/JSBSim smoke testing remains blocked until the missing JSBSim data/submodule is available.

## Recommended Next Actions

1. Compile `paper_latex/main.tex` and `paper_latex_en/main.tex` in an environment with `xelatex`, `bibtex`, and a full LaTeX distribution.
2. Perform visual PDF layout checks for tables, figures, captions, and references.
3. Choose the target journal/template and adapt the English LaTeX project accordingly.
4. If the target venue expects stronger statistics, extend the final comparison to five seeds or add a small LAG/JSBSim migration experiment.
