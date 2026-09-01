# C2-D1 advantage and actor-loss analysis

The archive stores aggregate advantage moments and post-update per-group surrogate values, but not per-group advantage samples, signs, medians, or exact per-group actor-loss contributions. Direct groupwise advantage-sign analysis is therefore not identifiable.

| Phase | Rescue advantage mean | Harm advantage mean | Rescue advantage SD | Harm advantage SD | Rescue surrogate concentration | Harm concentration | Rescue post-update KL | Harm post-update KL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| early | 0.0403 | 0.0380 | 0.7617 | 0.7671 | 0.6573 | 0.6672 | 0.0043 | 0.0045 |
| middle | 0.0212 | 0.0144 | 0.7419 | 0.6272 | 0.6545 | 0.6682 | 0.0035 | 0.0045 |
| late | 0.0303 | 0.0302 | 0.8313 | 0.8098 | 0.6465 | 0.6783 | 0.0035 | 0.0035 |
