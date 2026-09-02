# Fixed-prior formulation audit

Let `s_g = E[duration_g] / T`, with `T=260`. This is a deterministic **schedule-exposure** score, not a topology score. A diagnostic normalization would be `q_g = s_g / sum_h s_h`:

| Group | Diagnostic duration-normalized q | Legacy bounds | Within bounds |
| --- | --- | --- | --- |
| F0 | 0.153846 | 0.05–0.35 | yes |
| TE | 0.153846 | 0.05–0.35 | yes |
| TL | 0.153846 | 0.05–0.35 | yes |
| DS | 0.096154 | 0.05–0.35 | yes |
| DL | 0.211538 | 0.05–0.35 | yes |
| CP | 0.230769 | 0.05–0.35 | yes |

This vector is deliberately **not emitted as p0**. It treats longer relay outages as intrinsically more valuable to sample, but the contract supplies no policy-independent theorem or task-semantic rule that equates outage duration with recoverability, learning utility, or topology severity. A genuine topology-informed prior therefore remains underdetermined.
