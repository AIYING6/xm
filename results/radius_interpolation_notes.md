# Communication-Radius Interpolation Diagnostic

Purpose:

```text
Evaluate fixed trained checkpoints at unseen communication radii 5, 7, and 9.
This is a lightweight appendix diagnostic and does not replace the 300-episode main table at radii 4, 6, 8, and 10.
```

## Summary

| Method | Radius | Success | Collision | Timeout |
|---|---:|---:|---:|---:|
| MAPPO | 5 | 0.733 +/- 0.154 | 0.227 +/- 0.124 | 0.040 +/- 0.033 |
| MAPPO | 7 | 0.800 +/- 0.173 | 0.200 +/- 0.173 | 0.007 +/- 0.009 |
| MAPPO | 9 | 0.827 +/- 0.077 | 0.153 +/- 0.050 | 0.020 +/- 0.028 |
| GAT-MAPPO | 5 | 0.847 +/- 0.019 | 0.113 +/- 0.066 | 0.047 +/- 0.052 |
| GAT-MAPPO | 7 | 0.820 +/- 0.049 | 0.140 +/- 0.016 | 0.040 +/- 0.043 |
| GAT-MAPPO | 9 | 0.793 +/- 0.066 | 0.173 +/- 0.075 | 0.033 +/- 0.047 |
| EA-RG-MAPPO-S | 5 | 0.927 +/- 0.009 | 0.067 +/- 0.009 | 0.013 +/- 0.009 |
| EA-RG-MAPPO-S | 7 | 0.880 +/- 0.016 | 0.100 +/- 0.016 | 0.020 +/- 0.028 |
| EA-RG-MAPPO-S | 9 | 0.880 +/- 0.028 | 0.067 +/- 0.038 | 0.053 +/- 0.034 |

## Key Checks

```text
radius=5: EA collision=0.067, MAPPO collision=0.227, GAT collision=0.113.
radius=7: EA collision=0.100, MAPPO collision=0.200, GAT collision=0.140.
radius=9: EA collision=0.067, MAPPO collision=0.153, GAT collision=0.173.
```

Use boundary:

```text
Can write: unseen-radius diagnostics support the cross-radius stability trend.
Do not write: this small-budget diagnostic replaces the final 300-episode main evaluation.
```
