# Submission Readiness Report

Generated: 2026-08-02T01:40:09

## Summary

```text
Research manuscript package is internally consistent and evidence-backed.
Not final submission-ready in this runtime because PDF rendering cannot be verified without a LaTeX toolchain.
Current strongest claim: EA-RG-MAPPO-S improves post-relay-failure kill-chain recovery in a hardened 3DOF strict-sensing, limited-communication heterogeneous UAV task.
Boundary: full 4v2 red-blue combat, 6DOF JSBSim execution, online missile closure, high-fidelity radar, and human-UAV teaming have not been experimentally validated yet.
```

## Main Evidence

| Method | Recovery | Tracking | Chain | Collision |
|---|---:|---:|---:|---:|
| MAPPO (no graph) | 21.8 ± 41.9 | 14.8 | 3.7 | 0.8 |
| Single-graph MAPPO | 53.2 ± 38.1 | 47.5 | 7.6 | 2.8 |
| Full multi-relation | 88.6 ± 13.7 | 77.6 | 13.8 | 0.0 |

## Material Coverage

| Category | Present | Missing |
|---|---:|---:|
| Manuscripts | 9 | 0 |
| Result evidence | 16 | 0 |
| Reproducibility gates | 23 | 0 |

## Missing Internal Artifacts

None.

## Quantitative Warnings

None. Full EA-RG-MAPPO-S recovery/collision values and full-vs-single separation satisfy the current readiness thresholds.

## Runtime and Submission Limitations

- xelatex is not available in the current runtime
- latexmk is not available in the current runtime
- bibtex is not available in the current runtime
- PDF layout has not been verified in the current runtime.
- Journal-specific template formatting has not been performed.
- Real LAG/JSBSim smoke testing remains blocked until the missing JSBSim data/submodule is available.

## Recommended Next Actions

1. Compile `paper_latex_3d_en/main.tex` in an environment with `xelatex`, `bibtex`, and a full LaTeX distribution.
2. Perform visual PDF layout checks for tables, figures, captions, and references.
3. Choose the target journal/template and adapt the English LaTeX project accordingly.
4. If the target venue expects stronger realism, add a limited 5v2 or LAG/JSBSim replay extension after the 3v1 manuscript is stable.
