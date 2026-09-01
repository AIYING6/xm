# C2-D1 temporal-precedence analysis

Early and middle windows occur before the final 0.5M checkpoint evaluation. They support only training-signal timing descriptions; the archive has no intermediate frozen performance evaluations, so temporal precedence over task-performance divergence is not identifiable.

| Phase | Timing status | Rescue train reward | Harm train reward | Direction | Rescue advantage SD | Harm advantage SD | Direction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| early | before terminal evaluation | -0.0004 | -0.0090 | rescue_higher | 0.7617 | 0.7671 | rescue_lower |
| middle | before terminal evaluation | 0.0412 | 0.0269 | rescue_higher | 0.7419 | 0.6272 | rescue_higher |
| late | late descriptive only | 0.0788 | 0.0706 | rescue_higher | 0.8313 | 0.8098 | rescue_higher |
