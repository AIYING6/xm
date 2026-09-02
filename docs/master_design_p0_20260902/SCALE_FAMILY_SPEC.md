# Scale-family specification

| Scale | role counts | role in project | training interpretation |
|---|---|---|---|
| Small | 1S+2R+1T (4) | semantic smoke, visualization, ablation | independently trained |
| Main | 2S+2R+2T (6) | formal claims, external comparators, reliability | independently trained |
| Large | 2S+3R+3T (8) | scalability and structural stress | independently trained |

All scales must be emitted by one configuration-driven generator: role inventory, positions, directed support graph, per-role observation schema, failure masks, reward normalization and task-success contract. Cross-scale evaluation is optional and must be labeled zero-/few-shot only if it actually uses a model trained at another scale; it cannot be conflated with in-scale performance.
