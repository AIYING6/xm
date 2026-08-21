# M0 — Mature Method Literature Review

## Scope and search record

M0 is a zero-training, zero-rollout, zero-new-tape screen conducted on 2026-08-21. It preserves every historical closure: DRTP, TCR, T3/T5/T7, and EDR remain closed. The search covered sharpness-aware optimisation, Lipschitz/graph robustness, adversarial graph augmentation, robust MARL, and communication robustness. Search terms and primary sources were checked through CrossRef/OpenReview/PMLR/venue records; surveys were not used as sole evidence.

## Candidate family A — flatness / sharpness-aware policy optimisation

| Primary work | Venue | What it establishes | Relation to this project |
|---|---|---|---|
| Foret et al., *Sharpness-Aware Minimization for Efficiently Improving Generalization* ([record](https://mlanthology.org/iclr/2021/foret2021iclr-sharpnessaware/)) | ICLR 2021 | A practical two-gradient min–max update can seek locally flat solutions and improve out-of-distribution generalisation. | Mature optimisation principle; no actor-side information change and no execution overhead. |
| Kwon et al., *ASAM* ([arXiv](https://arxiv.org/abs/2102.11600)) | ICML 2021 | Scale-aware sharpness control avoids a parameterisation artefact of vanilla SAM. | Shows a mature family, but adds another adaptation choice; not selected for the first adaptation. |
| Du et al., *Efficient SAM* ([ICLR record](https://iclr.cc/virtual/2022/poster/6193)) | ICLR 2022 | SAM-like generalisation can be approximated more efficiently. | A possible implementation fallback only; it does not supply the topology-specific formulation. |
| Mai et al., *SHAPO: Sharpness-Aware Policy Optimization for Safe Exploration* ([OpenReview PDF](https://openreview.net/pdf?id=7cUxi8LbKD)) | ICLR 2026 | Sharpness-aware updates can be formulated directly for policy optimisation and can improve safety/performance in continuous control. | Direct RL precedent for applying a flatness principle to a policy objective rather than importing a supervised-learning claim unchanged. |

**M0 interpretation.** A fixed, topology-diverse UTR training mixture already supplies the perturbation distribution. A SAM-style update would act on *optimisation geometry*, not resample topology or change the actor input. The adaptation is therefore: seek a policy whose PPO objective remains locally good under a bounded parameter perturbation while retaining exactly the frozen legal topology exposure.

## Candidate family B — Lipschitz / spectral graph-policy stabilisation

| Primary work | Venue | What it establishes | Relation to this project |
|---|---|---|---|
| Gama et al., *Stability of Graph Neural Networks to Relative Perturbations* ([arXiv](https://arxiv.org/abs/1910.09655)) | 2020 | Certain graph filters can have bounded output variation under graph-topology perturbations. | The theoretical motivation for bounding response to edge changes. |
| Levie et al., *Transferability of Spectral Graph Convolutional Neural Networks* ([JMLR](https://www.jmlr.org/papers/v22/20-213.html)) | JMLR 2021 | Graph-filter transferability is linked to stability under topology changes. | Relevant but spectral convolution differs materially from this edge-aware GAT actor. |
| Wang et al., *Certified Robustness of GNNs against Adversarial Structural Perturbation* ([KDD record](https://kdd.org/kdd2021/accepted-papers/toc.html)) | KDD 2021 | Structural edge additions/deletions can be defended/certified in GNN classification. | Strong graph-perturbation precedent, but a different prediction setting and a potentially over-smoothing risk in control. |
| Bukharin et al., *Robust MARL via Adversarial Regularization* ([arXiv](https://arxiv.org/abs/2310.10810)) | NeurIPS 2023 | Lipschitz-controlled policies can improve robustness in MARL; authors also note adversarial-regularisation instability. | Direct MARL relevance and a caution against selecting a high-gain adversarial regulariser here. |

## Candidate family C — adversarial graph / communication perturbation training

| Primary work | Venue | What it establishes | Relation to this project |
|---|---|---|---|
| Feng et al., *Graph Adversarial Training* ([arXiv](https://arxiv.org/abs/1902.08226)) | TKDE 2020 | Neighbour-aware adversarial perturbation can regularise GNN representations. | Mature graph augmentation precedent, but not a control-policy or legal-topology protocol. |
| Kong et al., *FLAG* ([OpenReview PDF](https://openreview.net/pdf?id=mj7WsaHYxj)) | ICLR 2021 | Gradient-based graph-feature augmentation can be lightweight and backbone-agnostic. | Feature augmentation would conflict with the project’s strictly interpretable legal actor edge features unless carefully bounded. |
| Hassanzadeh et al., *Certifiably Robust MARL against Adversarial Communication* ([project record](https://parisa-h.github.io/publication/cmarl22/)) | ICLR 2023 | Communication corruption can be studied rigorously in cooperative MARL. | Uses an adversarial communication formulation rather than the frozen relay-node failure semantics. |
| Zhou et al., *Robust MARL with Stochastic Adversary* ([PMLR](https://proceedings.mlr.press/v267/zhou25o.html)) | ICML 2025 | Online adversaries can improve MARL perturbation robustness. | Explicitly rejected for this project: a learned/adaptive adversary reintroduces the moving-distribution feedback that harmed DRTP stability. |

## Candidate family D — robust communication bottlenecks

Ding et al., *Robust Multi-Agent Communication With Graph Information Bottleneck Optimization* ([TPAMI record](https://pubmed.ncbi.nlm.nih.gov/38019627/)) establishes a strong robust-GNN-MARL precedent through information-theoretic message regularisers. It is useful prior-art context, but is not selected: it requires an additional representation objective and communication-learning machinery, creates a less clean ablation against the matched SG backbone, and overlaps the already closed support-utilisation direction.

## Literature conclusion

The literature does **not** justify another adaptive scenario sampler, gradient surgery, or adversarial co-player. It supports a single low-risk candidate: **Topology-Conditioned Sharpness-Aware PPO (TC-SAM-UTR)** — a standard SAM policy update applied to the fixed UTR mixture, with the topology contribution located in the frozen legal perturbation distribution and OOD evaluation rather than privileged actor information.

This is an adaptation of a mature optimisation principle, not a claim to invent SAM or a new GNN operator.
