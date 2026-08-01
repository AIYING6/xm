# Method Naming Consistency Audit

Generated: 2026-08-02T01:40:23

Purpose:

```text
Ensure publishable manuscripts consistently use EA-RG-MAPPO-S as the final method name.
Historical RI-GMAPPO names are allowed in workflow logs and code paths, but not in publishable drafts.
The reproducibility mapping must still record the code directory names for traceability.
```

## Summary

| Item | Value |
|---|---:|
| Publishable files checked | 27 |
| Mapping checks | 1 |
| Failures | 0 |

## Rows

| File | Final name count | Old marker count | Status | Notes |
|---|---:|---:|---|---|
| `paper_latex/main.tex` | 5 | 0 | ok | publishable naming ok |
| `paper_latex/sections/01_introduction.tex` | 1 | 0 | ok | publishable naming ok |
| `paper_latex/sections/02_related_work.tex` | 0 | 0 | ok | publishable naming ok |
| `paper_latex/sections/03_problem.tex` | 0 | 0 | ok | publishable naming ok |
| `paper_latex/sections/04_method.tex` | 4 | 0 | ok | publishable naming ok |
| `paper_latex/sections/05_experiments.tex` | 11 | 0 | ok | publishable naming ok |
| `paper_latex/sections/06_discussion.tex` | 1 | 0 | ok | publishable naming ok |
| `paper_latex/sections/07_conclusion.tex` | 1 | 0 | ok | publishable naming ok |
| `paper_latex/sections/08_appendix_experiments.tex` | 10 | 0 | ok | publishable naming ok |
| `paper_latex_en/main.tex` | 3 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/01_introduction.tex` | 3 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/02_related_work.tex` | 0 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/03_problem.tex` | 0 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/04_method.tex` | 3 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/05_experiments.tex` | 10 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/06_discussion.tex` | 1 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/07_conclusion.tex` | 1 | 0 | ok | publishable naming ok |
| `paper_latex_en/sections/08_appendix_experiments.tex` | 10 | 0 | ok | publishable naming ok |
| `docs/paper_manuscript_zh_v1.md` | 20 | 0 | ok | publishable naming ok |
| `docs/english_abstract_and_contributions.md` | 4 | 0 | ok | publishable naming ok |
| `docs/english_introduction_draft.md` | 3 | 0 | ok | publishable naming ok |
| `docs/english_related_work_draft.md` | 1 | 0 | ok | publishable naming ok |
| `docs/english_problem_method_draft.md` | 2 | 0 | ok | publishable naming ok |
| `docs/english_experiments_draft.md` | 13 | 0 | ok | publishable naming ok |
| `docs/english_discussion_conclusion_draft.md` | 2 | 0 | ok | publishable naming ok |
| `docs/english_manuscript_draft.md` | 26 | 0 | ok | publishable naming ok |
| `publishable_bundle` | 135 | 0 | ok | required method names present across publishable bundle |
| `mapping_docs` | 14 | 10 | ok | code-directory mapping present |

## Naming Rule

```text
Paper method name: EA-RG-MAPPO-S.
Allowed code/result directory stem: ri_gmappo_edge_stage2_rand_seed*_20.
Old route names such as RI-GMAPPO or RI edge may remain only in internal history logs.
```
