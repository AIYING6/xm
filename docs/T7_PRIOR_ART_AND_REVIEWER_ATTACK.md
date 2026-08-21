# T7 — Prior Art and Reviewer Attack

## Closest primary literature

| Work | Core mechanism | Conditioned object | Sensitivity explicit? | Calibration explicit? | MARL / graph / topology | Consequence for T7 |
|---|---|---|---|---|---|---|
| [FiLM](https://ojs.aaai.org/index.php/AAAI/article/view/11671) | Feature-wise affine modulation | Intermediate features | No | No | No / No / No | Any support-conditioned modulation is a direct generic baseline. |
| [HyperNetworks](https://mlanthology.org/iclr/2017/ha2017iclr-hypernetworks/) | Context-generated weights | Model weights | No | No | No / No / No | A support hypernetwork is capacity conditioning, not calibration. |
| [Right for the Right Reasons](https://mlanthology.org/ijcai/2017/ross2017ijcai-right/) | Input-gradient explanation regularization | Input dependence | Yes | Targeted by annotation | No / No / No | A direct sensitivity/Jacobian penalty is crowded prior art. |
| [Invariant Policy Optimization](https://proceedings.mlr.press/v144/sonar21a.html) | Cross-domain policy invariance | Action predictor | Indirect | Domain-driven | RL / No / domain shift | T7 cannot relabel invariance as topology calibration. |
| [Action-Robust RL](https://proceedings.mlr.press/v97/tessler19a.html) | Worst-case action robustness | Action under disturbance | No | No | RL / No / perturbation | Robustness alone is not a sufficient novelty claim. |
| [TarMAC](https://proceedings.mlr.press/v97/das19a.html) | Targeted learned messages | Communication recipient/content | Indirect | No | MARL / No / communication | T7 keeps delivery fixed and only audits decision use. |
| [I2C](https://proceedings.neurips.cc/paper/2020/hash/fb2fcd534b0ff3bbed73cc51df620323-Abstract.html) | Value-informed communication prior | Communication necessity | Yes | Value-related | MARL / No / communication | Shows that communication-use regularization is an established space. |
| [TMC](https://proceedings.neurips.cc/paper/2020/hash/c82b013313066e0702d58dc70db033ca-Abstract.html) | Temporal message control | Message transmission | No | No | MARL / No / lossy links | Different layer, but robust communication is crowded. |
| [Communication-Constrained Priors](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e26502ce357ce3015e8778f0e85d4b39-Abstract-Conference.html) | Communication-condition prior and MI objective | Lossy/lossless message effects | Indirect | Scenario-driven | MARL / No / lossy links | Makes a generic support-use auxiliary insufficient. |
| [Universally Expressive Communication](https://proceedings.neurips.cc/paper_files/paper/2022/hash/d8a19c815a8bef25e6094e87f963d28e-Abstract-Conference.html) | GNN expressivity augmentation | Communication protocol | No | No | MARL / GNN / task-dependent | Architecture expansion cannot substitute for a calibration law. |

## Reviewer A — “This is another conditional policy.”

**Attack succeeds.** The only defensible distinction would have been a
state-conditional calibration target for a finite action-response object, not
feature modulation. T7 cannot identify such a target from legal support
quality; a gate, FiLM, hypernetwork, or support concatenation would therefore
be ordinary conditioning.

## Reviewer B — “This is input-gradient or sensitivity regularization.”

**Attack succeeds.** A finite TVD response is behaviorally preferable to an
unbounded Jacobian, but without a data-supported `\tau(x)` the proposed loss is
still just a generic encouragement or suppression of input sensitivity. The
matched T7 premise test provides no calibration law that distinguishes it from
existing explanation/gradient regularization.

## Reviewer C — “The five-seed telemetry is exploratory.”

**Attack succeeds for method justification.** T4/T6 are appropriate for
discovering a utilization gap, but they do not identify a causal intervention.
T7 deliberately does not convert their seed correlations into supervision. A
future performance result could not repair this missing ex ante mechanism.

## Novelty conclusion

No candidate clears Strong-Q2 or Solid-Q2. The failures are scientific, not
engineering: no supported calibration reference and no remaining difference
from generic conditional or sensitivity regularization.
