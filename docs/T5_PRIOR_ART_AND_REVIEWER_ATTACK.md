# T5 — Prior-Art Attack and Reviewer Review

## Closest primary literature

| Work | Core problem | Decision conditioning | Graph? | Role-aware? | Topology robustness? | Key overlap | Defensible difference / consequence |
|---|---|---|---|---|---|---|---|
| [FiLM](https://ojs.aaai.org/index.php/AAAI/article/view/11671) | general feature conditioning | affine feature modulation | No | No | No | context changes a decision pathway | Any support gate/modulation would be a direct special case; rejected. |
| [HyperNetworks](https://mlanthology.org/iclr/2017/ha2017iclr-hypernetworks/) | context-generated weights | generated/adaptive weights | No | No | No | conditional parameters | A support hypernetwork is capacity/conditioning, not a distinct T5 principle; rejected. |
| [Right for the Right Reasons](https://mlanthology.org/ijcai/2017/ross2017ijcai-right/) | explanation-guided generalization | input-gradient regularization | No | No | No | constraining decision dependence on inputs | A generic support-sensitivity loss is crowded by explanation regularization. |
| [Invariant Policy Optimization](https://proceedings.mlr.press/v144/sonar21a.html) | policy generalization across domains | invariant action predictor | No | No | domain shift | closest to cross-condition decision consistency | T5's response-contrast object differs from absolute action/representation invariance, but IPO makes a strong-novelty claim untenable. |
| [TarMAC](https://proceedings.mlr.press/v97/das19a.html) | learn who/what to communicate | targeted learned messages | No | implicit | changing communication | communication affects action | T5 does not learn or alter messages/topology; it audits use of legal, already delivered evidence. |
| [IMAC](https://proceedings.mlr.press/v119/wang20i.html) | bandwidth-limited MARL communication | information-bottleneck messages | No | No | limited communication | communication-use robustness | T5 has no learned message channel or information bottleneck. |
| [Communication-Constrained Priors](https://openreview.net/forum?id=1m177EsP3V) | lossy vs lossless communication | prior and mutual-information objective | No | No | communication degradation | robustness to communication quality | This is closer than a generic auxiliary; T5 cannot claim a new communication-information principle. |
| [Exponential Topology-enabled Communication](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3514dbacaebf0f38b25adfe59ed81a8a-Abstract-Conference.html) | scalable MARL communication topology | topology-enabled communication | Yes | No | topology change | graph/topology adaptation | T5 does not alter graph construction or communication protocol. |
| [Certifiably Robust MARL against Adversarial Communication](https://furong-huang.com/publications/certifiably-robust-multi-agent-reinforcement-learning-against-adversarial-communication-2/) | adversarial message robustness | certified robustness method | No | No | communication attack | robust decisions under disturbed communication | Different perturbation and guarantees, but raises the robustness-method bar. |
| [Robust MARL under Environmental Uncertainty](https://proceedings.mlr.press/v235/shi24d.html) | distributionally robust Markov games | worst-case game optimization | No | No | dynamics uncertainty | robust MARL objective | Distinct mathematical setting; confirms that generic robustness optimization is not a novel substitute. |

## Novelty assessment

A support-conditioned gate, FiLM layer, hypernetwork, MoE, extra attention, or simple sensitivity loss would be ordinary conditional policy learning. The sole response-contrast hypothesis is narrower: it constrains only how a legal support perturbation changes an action distribution across topology contexts, not absolute actions or latent features. This distinction is mathematically real but, given IPO and explanation-gradient literature, it is insufficient for a **Strong-Q2** claim without strong task-specific evidence and ablations.

The dedicated T5 offline falsification then removes the remaining empirical basis: good policies do not show the required pre-to-early response-consistency advantage. Therefore even a `SOLID_Q2` method claim is not supported.

## Mandatory reviewer attacks

### Reviewer A — “This is merely a conditional policy.”

The best possible answer would be that the object is an action-response difference under a specified legal support intervention, rather than a conditioned feature. However, FiLM, hypernetworks, and policy-invariance work leave this distinction too incremental without a demonstrated response law. **Attack not defeated.**

### Reviewer B — “T4 already says the representation contains support; this is latent reweighting.”

The response-contrast hypothesis does operate downstream of representation and would not reweight a latent. But T5.2 fails: the desired invariant response is absent in good policies. **Attack not defeated.**

### Reviewer C — “Five development seeds with correlational telemetry do not justify a new method.”

T4 was explicitly exploratory and makes no causal claim. A future method would need its own seed-consistent ablation and utilization-metric evidence. With the sole candidate falsified offline, this reviewer is correct that a new method would be premature. **Attack not defeated.**
