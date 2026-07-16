# Evaluation Budget Consistency Audit

Generated: 2026-07-16T21:04:38

Purpose:

```text
Check that main, appendix, and diagnostic tables keep their intended evaluation budgets.
This audit prevents 300-episode main results, 100-episode appendix results, and smaller diagnostics from being mixed without labels.
```

## Summary

| Item | Value |
|---|---:|
| Budget groups checked | 6 |
| Failures | 0 |

## Rows

| Name | Rows | Episodes | LaTeX marker | Status | Notes |
|---|---:|---:|---|---|---|
| `final_main` | 12 / 12 | 300 / 300 | `Final 300-episode evaluation` | ok | Main evaluation table. |
| `ablation` | 20 / 20 | n/a / n/a | `Ablation study` | ok | 100-episode-per-seed module ablation; source CSV is legacy formatted without an episodes column. |
| `speed_robustness` | 18 / 18 | 100 / 100 | `100 episodes per seed` | ok | Appendix target-speed robustness diagnostic. |
| `comm_dropout` | 18 / 18 | 50 / 50 | `50 episodes per seed` | ok | Appendix communication-dropout diagnostic. |
| `radius_interpolation` | 9 / 9 | 50 / 50 | `50 episodes per seed` | ok | Appendix unseen-radius interpolation diagnostic. |
| `edge_feature_masking` | 14 / 14 | 30 / 30 | `30 episodes per seed` | ok | Appendix evaluation-time edge-feature masking diagnostic. |

## Use Boundary

```text
Use this audit to keep evaluation-budget wording synchronized.
Do not treat a smaller appendix diagnostic as equivalent to the final 300-episode main table.
```
