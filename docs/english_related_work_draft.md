# English Related Work Draft

Date: 2026-07-13

## Related Work

### Multi-Agent Reinforcement Learning

Multi-agent reinforcement learning has been widely used in cooperative control, resource allocation, and adversarial decision-making tasks. PPO improves the stability of on-policy policy-gradient training through a clipped surrogate objective \cite{schulman2017ppo}. In multi-agent settings, MADDPG, COMA, VDN, and QMIX address non-stationary training and cooperative credit assignment from different perspectives, including centralized critics, counterfactual policy gradients, and value decomposition \cite{lowe2017maddpg,foerster2018coma,sunehag2018vdn,rashid2018qmix}. The centralized training and decentralized execution paradigm allows the learning algorithm to use global information during training while preserving decentralized execution at test time. MAPPO has become a strong practical baseline for cooperative multi-agent tasks. Yu et al. show that PPO-style multi-agent methods can achieve competitive performance on several cooperative benchmarks when implemented and tuned carefully \cite{yu2021mappo}. Therefore, this paper treats MAPPO as a serious baseline rather than a weak reference method.

In UAV cooperative tasks, reinforcement learning has been applied to trajectory planning, pursuit-evasion, air combat maneuvering, and swarm coordination. Recent work on UAV cooperative pursuit-evasion also suggests that reinforcement learning can learn complex pursuit policies \cite{zhao2024uav_pursuit_evasion}. However, under limited communication, relying only on local observations and a centralized critic may still lead to high variance across random seeds and high collision rates at small communication radii.

### Graph Neural Networks for Multi-Agent Coordination

Graph neural networks are well suited for relational modeling in multi-agent systems. GAT uses masked self-attention to adaptively aggregate information from neighboring nodes \cite{velickovic2017gat}. In multi-agent reinforcement learning, methods such as MAGNet explore how graph networks can be integrated into deep MARL policies \cite{malysheva2020magnet}. Recent surveys further summarize the combination of GNNs and MARL in communication and coordination problems \cite{liu2024gnn_marl,cuzin2026gnn_comm_survey}.

Nevertheless, standard graph attention usually computes attention scores mainly from node embeddings. In UAV cooperative pursuit, relative distance, bearing, velocity difference, and communication reachability are key variables that affect coordination and safety. If these physical relations are only implicitly encoded in node states, the policy must infer edge relations indirectly. This can increase learning difficulty and weaken robustness when the communication graph changes. This paper therefore injects relative edge features directly into the attention score, enabling the graph encoder to explicitly perceive spatial relations and communication topology.

### Limited-Communication UAV Cooperation

Communication in real UAV systems is affected by distance, bandwidth, link quality, and occlusion. IC3Net studies when agents should communicate and how communication gates can be learned in cooperative and competitive multi-agent tasks \cite{singh2018ic3net}. In UAV communication networks and mobile edge computing scenarios, existing studies have combined graph attention and multi-agent reinforcement learning for trajectory design, resource assignment, and cooperative optimization \cite{feng2024gat_uav_comm,kim2024uav_mec_madrl}.

Different from these studies, this paper focuses on robustness under explicitly limited communication in cooperative pursuit. Communication radius is directly modeled and evaluated at radii 4, 6, 8, and 10. The evaluation considers not only success rate, but also collision rate and seed-to-seed variation, so that the practical safety and stability of the learned policy can be assessed.

### Position of This Work

Existing studies have advanced multi-agent decision making from several directions, including stable MAPPO-style training, graph-based relational modeling, and learning communication mechanisms. However, there remains a gap in limited-communication UAV pursuit. First, MAPPO alone cannot explicitly represent spatial relations among agents. Second, standard GAT can aggregate neighboring nodes, but does not directly use edge semantics such as distance, bearing, velocity difference, and communication reachability. Third, training under a fixed communication topology may not ensure stable behavior when the communication radius changes. This paper addresses this gap by combining an edge-aware role graph encoder with MAPPO and by using staged random-radius fine-tuning to improve cross-radius robustness.

## Boundary for Later Use

```text
This related-work draft supports the EA-RG-MAPPO-S paper narrative.
It should not be used to claim that full 6DOF air combat or high-accuracy target intent recognition has been experimentally verified.
```
