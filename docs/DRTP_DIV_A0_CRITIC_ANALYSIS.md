# DRTP-DIV-A0 — Critic Analysis

The archived critic-related fields are value loss and explained variance.
They do not demonstrate a common critic collapse.

| Window | weak DRTP value loss | strong DRTP value loss | weak DRTP explained variance | strong DRTP explained variance |
|---|---:|---:|---:|---:|
| 0–0.25M | 0.417 / 0.349 | 0.346–0.461 | 0.794 / 0.816 | 0.742–0.791 |
| 0.5–1M | 0.752 / 0.777 | 0.896–1.077 | 0.902 / 0.908 | 0.884–0.907 |
| 1–2M | 0.786 / 0.831 | 1.212–1.391 | 0.914 / 0.921 | 0.900–0.954 |

Neither weak seed shows persistently poorer explained variance or a uniquely
exploding value loss. Since the archives do not retain per-condition critic
error, Bellman residual decomposition, or milestone behavior evaluation, this
result is limited to an absence of a shared aggregate critic signature.

**Conclusion:** the evidence does not support critic failure as the primary
shared cause of DRTP weak-seed divergence.

