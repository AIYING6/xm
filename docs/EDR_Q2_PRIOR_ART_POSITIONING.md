# EDR-Q2 — Prior-Art Positioning

| Work | Core aggregation | Neighbor normalization | Edge deletion behavior | MARL? | Failure-specific? | EDR distinction |
|---|---|---|---|---|---|---|
| [GAT](https://arxiv.org/abs/1710.10903) | Attention-weighted sum | Receiver softmax | Deletion renormalizes survivors | No | No | EDR targets this measured denominator coupling. |
| [MPNN](https://proceedings.mlr.press/v70/gilmer17a/gilmer17a.pdf) | Learned messages + invariant aggregation | General | Aggregator dependent | No | No | EDR is a restricted failure-aligned instance. |
| [Residual Gated Graph ConvNets](https://arxiv.org/abs/1711.07553) | Edge gates + residuality | Non-softmax gates | Can be deletion local | No | No | Closest primitive; EDR claims no new gating theory. |
| [Structural Message Passing](https://proceedings.neurips.cc/paper/2020/hash/a32d7eeaae19821fd9ce317f3ce952a7-Abstract.html) | Structural aggregation | Global average-degree construction | Not Relay/MARL specific | No | No | EDR fixes `C` for the stated deletion-local property. |
| [Certified structural robustness](https://arxiv.org/abs/2008.10715) | Randomized smoothing | Model dependent | Certifies adversarial edits | No | Structural attack | EDR offers no certificate. |
| [IC3Net](https://openreview.net/pdf?id=rye7knCqK7) | Communication gating | Learned gates | Learned topology use | Yes | No | EDR does not learn or alter topology. |
| [ATOC](https://proceedings.neurips.cc/paper/2018/file/6a8018b3a00b69c008601b8becae392b-Paper.pdf) | Attentional communication | Attention-based | Adaptive communication | Yes | No | EDR holds delivery fixed and changes encoder response. |
| [TMC](https://proceedings.neurips.cc/paper/2020/hash/c82b013313066e0702d58dc70db033ca-Abstract.html) | Temporal message control | N/A | Lossy-message robustness | Yes | Yes | Different layer: no bandwidth/message policy. |
| [Correlated communication topology](https://ifaamas.org/Proceedings/aamas2021/pdfs/p456.pdf) | Learned topology | Topology generator | Changes graph | Yes | No | EDR handles exogenous legal deletion only. |

## Q2 positioning

The primitive operations are known. The defensible claim is not “a new gated
GNN,” but **failure-aligned deletion-local graph aggregation**: an explicit
property that removes a measured GAT redistribution pathway under a physical
Relay-link deletion, within decentralized heterogeneous UAV MARL.

### Reviewer attack

- **MARL:** Standard components are acknowledged; the complete paper must add
  physical failure validity, matched exposure, OOD/safety, seed stability, and
  property ablations. Application alone is insufficient.
- **Graph learning:** Fixed-normalized gating is not new. EDR claims only the
  event-aligned formulation and mechanism validation, not general GNN theory.
- **UAV systems:** Removing a Relay edge rescales a legal surviving direct edge
  in softmax even when that direct edge's descriptor is unchanged. EDR blocks
  this specific representation redistribution. Performance remains prospective.

This positioning is insufficient for Strong-Q2, but is defensible for the
complete Q2 paper bundle if future controls and results succeed.
