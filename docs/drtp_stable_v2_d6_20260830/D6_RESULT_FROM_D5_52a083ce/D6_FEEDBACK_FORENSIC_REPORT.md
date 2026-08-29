# Stable-v2 D6 sampler-feedback forensic

**Decision:** `D6_PAIRED_PROBE_DESIGN_AUDIT_AUTHORIZED`.

| Seed | First KLB trigger | First paired q divergence | Original mean $\|q-q_u\|_1$ | KLB mean $\|q-q_u\|_1$ | G Original | G KLB |
|---:|---:|---:|---:|---:|---:|---:|
| 3201 | 246 | 256 | 0.365 | 0.488 | -46.165 | -46.662 |
| 3202 | 262 | 416 | 0.552 | 0.626 | -7.868 | -31.342 |
| 3203 | 131 | 160 | 0.498 | 0.567 | -39.846 | -49.669 |

## Frozen criteria

```json
{
  "temporal_ordering_all_seeds": true,
  "sampler_amplification_all_seeds": true,
  "candidate_nonimprovement_all_seeds": true,
  "input_integrity": true
}
```

The observed ordering supports only the limited statement that KLB intervention
precedes later paired sampler divergence in these D5 trajectories. It does not
identify the cause of Original DRTP seed sensitivity and does not authorize a
new implementation or training run.
