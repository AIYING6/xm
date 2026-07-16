# English Manuscript Draft

Date: 2026-07-13

```text
This is a merged English draft for the EA-RG-MAPPO-S paper.
It is generated from section-level drafts and keeps the current evidence boundary: 2D limited-communication UAV pursuit, not completed full 6DOF air combat validation.
```

<!-- Source: docs/english_abstract_and_contributions.md -->

## Title

Edge-Aware Role Graph Multi-Agent Reinforcement Learning for UAV Cooperative Pursuit under Limited Communication

## Abstract

Cooperative UAV pursuit requires multiple heterogeneous platforms to intercept a maneuvering target under limited communication while avoiding inter-UAV collisions. Existing multi-agent reinforcement learning methods usually rely on local observations or standard graph attention, and may fail to explicitly encode relative spatial relations and communication reachability when the communication radius changes. To address this issue, this paper proposes EA-RG-MAPPO-S, an edge-aware role graph multi-agent reinforcement learning method with staged random-radius fine-tuning. The method represents pursuers and targets as dynamic graph nodes with role semantics, and injects relative position, distance, bearing, relative velocity, and communication reachability into the graph attention score. A staged training strategy is further adopted: the policy first learns basic coordination under a fixed communication radius and is then fine-tuned with randomly sampled communication radii to improve cross-radius robustness. Experiments in a two-dimensional heterogeneous UAV pursuit environment show that EA-RG-MAPPO-S achieves lower collision rates and more stable performance than MAPPO and GAT-MAPPO under mixed target maneuvers. In the final 300-episode-per-seed evaluation, EA-RG-MAPPO-S obtains success rates of 0.926, 0.919, 0.890, and 0.879 at communication radii 4, 6, 8, and 10, respectively, while keeping collision rates between 0.054 and 0.086. Visualization results further indicate that the proposed graph policy adjusts its attention distribution according to communication constraints.

## Keywords

UAV swarm; multi-agent reinforcement learning; limited communication; graph attention network; cooperative pursuit; MAPPO

## Contributions

1. An edge-aware role graph policy representation is proposed for limited-communication UAV pursuit. Pursuers and targets are modeled as role-aware dynamic graph nodes, and relative position, distance, bearing, relative velocity, and communication reachability are explicitly injected into the attention score.
2. A staged random-radius fine-tuning strategy is introduced to improve robustness across communication radii. The policy first learns basic coordination under a fixed radius and is then fine-tuned with randomly sampled radii.
3. A reproducible experimental pipeline is built for heterogeneous UAV cooperative pursuit. The final 300-episode-per-seed evaluation shows that EA-RG-MAPPO-S keeps collision rates between 0.054 and 0.086 across four communication radii, supported by ablation, robustness, trajectory, and attention analyses.

## Claim Boundary

```text
Supported: limited-communication robustness and lower collision in a simplified 2D heterogeneous UAV pursuit environment.
Not supported yet: high-accuracy target intent recognition or full 6DOF air combat with missile, radar, and human-UAV teaming.
```

<!-- Source: docs/english_introduction_draft.md -->

## Introduction

Unmanned aerial vehicle (UAV) swarms have become increasingly important in cooperative reconnaissance, target interception, area patrol, and air combat related missions. Compared with single-platform decision making, swarm-level missions require multiple vehicles to share information, maintain safe spatial relations, and form coordinated behaviors under dynamic environmental constraints. In cooperative pursuit scenarios, several pursuer UAVs need to intercept a maneuvering target while avoiding inter-UAV collisions and mission timeouts. When communication is limited or the coordination policy is unstable, the team may suffer from inefficient pursuit, unsafe convergence, or failed interception.

Multi-agent reinforcement learning (MARL) provides an end-to-end learning framework for cooperative UAV decision making. The centralized training and decentralized execution paradigm allows a critic to exploit global information during training while each agent executes its policy based on local observations. MAPPO has been shown to be a strong and practical baseline for cooperative multi-agent tasks. However, a standard MAPPO policy lacks an explicit mechanism for relational reasoning. Under a limited communication radius, relative spatial relations and communication reachability among UAVs may not be fully exploited by a policy that mainly relies on local observations and a centralized critic.

Graph neural networks and graph attention mechanisms provide a natural way to model relations among multiple agents. A graph attention network can adaptively aggregate information from neighboring nodes, and has been used in several multi-agent coordination and communication problems. Nevertheless, standard graph attention usually computes attention scores from node embeddings. In UAV pursuit tasks, edge-level physical relations such as relative distance, bearing, relative velocity, and communication reachability directly affect formation geometry, collision avoidance, and target encirclement. If these relations are only implicitly encoded in node states, the policy must learn to infer them indirectly, which can increase training difficulty and reduce robustness when the communication topology changes.

Realistic UAV swarms cannot assume global and stable communication. Communication radius, link quality, bandwidth, and occlusion may all change the set of information available to each platform. Existing learning-to-communicate and graph-based MARL studies have investigated when and how agents should exchange information, and UAV communication or mobile edge computing studies have also combined graph attention with multi-agent learning. In cooperative pursuit, however, communication constraints are not only graph connectivity changes. The geometry and motion relationship between agents also determine whether an information edge is useful for safe and efficient pursuit. Therefore, it remains important to design a policy representation that explicitly embeds physical edge semantics and remains stable across different communication radii.

This paper focuses on a realistic and implementable research step: validating a limited-communication graph MARL method in a simplified two-dimensional heterogeneous UAV pursuit environment before moving to full 6DOF air combat, missile, radar, and human-UAV teaming systems. This choice reduces simulation complexity, isolates the algorithmic contribution, and provides a reusable representation layer for future migration to LAG/JSBSim or other 6DOF simulators. We propose EA-RG-MAPPO-S, an edge-aware role graph MAPPO method with staged random-radius fine-tuning. The method consists of three components: an edge-aware role graph representation, a MAPPO-based centralized-training decentralized-execution optimizer, and a staged fine-tuning strategy over randomly sampled communication radii.

The main contributions are as follows:

1. We propose an edge-aware role graph policy representation for limited-communication UAV pursuit. Pursuers and targets are modeled as dynamic graph nodes with role semantics, and relative position, distance, bearing, relative velocity, and communication reachability are injected into the graph attention score.
2. We introduce a staged random-radius fine-tuning strategy. The policy first learns basic coordination under a fixed communication radius and is then fine-tuned with randomly sampled radii, improving stability across communication topologies instead of overfitting to a single radius.
3. We build a reproducible heterogeneous UAV pursuit benchmark and evaluate MAPPO, GAT-MAPPO, EA-RG-MAPPO-S, and ablation variants over multiple seeds. The final 300-episode-per-seed evaluation shows that EA-RG-MAPPO-S keeps collision rates between 0.054 and 0.086 across four communication radii, supported by trajectory, scatter, attention, robustness, and edge-feature diagnostic analyses.

It should be noted that an auxiliary target-intent prediction branch was explored during development. Diagnostic results show insufficient balanced accuracy, indicating that this branch cannot yet support a high-accuracy intent-recognition claim. Therefore, the main contribution of this paper is limited-communication edge-aware role graph coordination rather than target intent recognition.

## Boundary for Later Use

```text
This draft is intended for future English manuscript conversion.
It should not be interpreted as evidence that full 6DOF air combat, missile, radar, or human-UAV teaming experiments have already been completed.
```

<!-- Source: docs/english_related_work_draft.md -->

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

<!-- Source: docs/english_problem_method_draft.md -->

## Problem Formulation

We consider a cooperative pursuit task with \(N\) pursuer UAVs and \(M\) maneuvering targets. In the current experimental setting, \(N=3\) and \(M=1\). At time step \(t\), the motion state of pursuer \(i\) is denoted as \(x_i^t=(p_i^t,\psi_i^t,v_i^t,\eta_i^t)\), where \(p_i^t\) is the two-dimensional position, \(\psi_i^t\) is the heading angle, \(v_i^t\) is the speed, and \(\eta_i^t\) denotes the remaining energy or platform-specific state variable. The target state is denoted as \(x_{\mathrm{tar}}^t=(p_{\mathrm{tar}}^t,\psi_{\mathrm{tar}}^t,v_{\mathrm{tar}}^t)\). Each pursuer selects a discrete action \(a_i^t\) according to its local observation \(o_i^t\) and graph information \(G^t\). The action space consists of turning and acceleration/deceleration combinations.

### Centralized Training and Decentralized Execution

The policy is trained under the centralized training and decentralized execution paradigm. During training, a centralized critic \(V_\phi(s^t)\) uses the global state \(s^t\), which contains all pursuer and target states. During execution, each agent only uses its local observation and graph-encoded representation. The learning objective is to maximize the expected discounted team return:

```text
max_theta E[ sum_{t=0}^{T} gamma^t r^t ].
```

### Limited-Communication Graph

Limited communication is modeled by a communication radius \(R_c\). The communication reachability between pursuers \(i\) and \(j\) is defined as:

```text
I_ij^comm = I( ||p_i^t - p_j^t||_2 <= R_c ).
```

If the distance between two pursuers is larger than \(R_c\), their direct teammate edge is unavailable, and the corresponding teammate-observation slot is masked to zero. The dynamic graph used by the policy is denoted as \(G^t=(V^t,E^t)\), where nodes include pursuers and the target. Edges among pursuers are constrained by the communication radius. The target node is retained as a task-relevant observation node, while the edge feature records communication reachability. The main evaluation uses \(R_c \in \{4,6,8,10\}\).

### Reward and Evaluation Metrics

The reward consists of target-approaching reward, individual distance reward, heading reward, successful interception reward, collision penalty, and timeout-related penalty. The evaluation metrics include success rate, collision rate, timeout rate, and average episode length. Collision rate is emphasized as the main safety metric. An episode is counted as successful if any pursuer reaches the target capture radius within the time limit. A collision is counted if the distance between pursuers is below the safety threshold. An episode is counted as timeout if the maximum number of steps is reached without successful capture.

## Method

### Overview

The proposed method is denoted as EA-RG-MAPPO-S, namely Edge-Aware Role Graph MAPPO with Staged random-radius fine-tuning. It contains a local-observation encoder, an edge-aware role graph encoder, a centralized critic, and a staged random-radius fine-tuning procedure. The actor input is the concatenation of the local observation representation and the graph representation, while the critic uses the centralized global state.

### Role Graph Construction

At each time step, a dynamic graph \(G^t=(V^t,E^t)\) is constructed. The node set includes pursuer nodes and the target node. Each node contains normalized position, heading, speed, and platform-related state features. A role indicator is used to distinguish UAV nodes from target nodes. The node feature and role embedding are concatenated before entering the graph encoder:

```text
h_i^0 = f_in([x_i, Emb(role_i)]).
```

The role graph allows the model to distinguish teammates from the target, avoiding a homogeneous treatment of all graph nodes.

### Relative Edge-Feature Enhanced Attention

For the directed edge from node \(i\) to node \(j\), a relative edge feature vector \(e_{ij}\) is constructed:

```text
e_ij = [
  Delta x_ij,
  Delta y_ij,
  d_ij / d_max,
  d_ij / R_c,
  cos(beta_ij),
  sin(beta_ij),
  Delta v_ij^x,
  Delta v_ij^y,
  I_ij^comm,
  I_j^target
].
```

Here \(d_{ij}\) is the distance between nodes, \(d_{\max}\) is the environment-scale normalization constant, \(\beta_{ij}\) is the relative bearing, \(I_{ij}^{comm}\) indicates communication reachability, and \(I_j^{target}\) indicates whether node \(j\) is the target. The edge-aware attention score is computed as:

```text
score_ij = LeakyReLU( a^T [W h_i, W h_j] ) + g_e(e_ij),
```

where \(g_e\) is an edge-feature scoring network. A masked softmax is then applied over reachable neighbors:

```text
alpha_ij = exp(score_ij) / sum_{k in N_i} exp(score_ik),  j in N_i.
```

The node representation is updated by:

```text
h_i' = tanh( sum_{j in N_i} alpha_ij W h_j ).
```

Compared with standard GAT, which computes attention only from node embeddings, EA-RG-MAPPO-S directly uses distance, bearing, velocity difference, and communication reachability to adjust neighbor weights. This design makes the graph policy more aware of physical relations and communication constraints.

### MAPPO Optimization

The policy network outputs the action distribution \(\pi_\theta(a_i|o_i,G)\) for each agent. MAPPO is used with the clipped surrogate objective. The probability ratio is:

```text
rho_i^t(theta) = pi_theta(a_i^t | o_i^t, G^t) /
                 pi_theta_old(a_i^t | o_i^t, G^t).
```

The policy loss is:

```text
L_policy = - E[ min(
  rho_i^t A_i^t,
  clip(rho_i^t, 1-epsilon, 1+epsilon) A_i^t
) ].
```

The total loss is:

```text
L = L_policy + c_v L_value - c_H L_entropy + c_aux L_aux.
```

\(L_{aux}\) is an optional auxiliary loss. Since the current target-intent branch does not achieve reliable balanced accuracy, the main conclusions do not depend on that auxiliary branch.

### Staged Random-Radius Fine-Tuning

Training only under a fixed communication radius may make the policy over-adapt to a single communication topology. This paper uses a two-stage training strategy. In the first stage, the edge-aware role graph policy is trained under a fixed communication radius \(R_c=8\) to learn basic coordination. In the second stage, the policy is initialized from the first-stage checkpoint and fine-tuned with a smaller learning rate. For each episode, the communication radius is sampled from:

```text
R_c ~ U(4, 10).
```

The purpose of this stage is to improve adaptation to different communication topologies rather than merely increasing the total training time.

## Boundary for Later Use

```text
This method draft describes the current 2D limited-communication pursuit implementation.
It provides a reusable representation and training structure for later LAG/JSBSim or 6DOF migration, but it is not itself a completed 6DOF air-combat validation.
```

<!-- Source: docs/english_experiments_draft.md -->

## Experiments

### Environment Settings

The experiments are conducted in a two-dimensional heterogeneous UAV cooperative pursuit environment with three pursuer UAVs and one maneuvering target. The pursuers have different maximum speeds, sensing ranges, and energy-related parameters. The target follows a mixed maneuvering policy, which combines escaping from the nearest pursuer and random turning. The final main evaluation uses the mixed target policy, target speed 0.75, communication radii \(4,6,8,10\), 300 evaluation episodes per seed, and three random seeds.

All methods use the centralized training and decentralized execution setting. MAPPO uses a shared actor and a centralized critic. GAT-MAPPO adds node-level graph attention on top of MAPPO. EA-RG-MAPPO-S further introduces role embeddings, relative edge features, and staged random-radius fine-tuning. During training, the policy first learns basic coordination under a fixed communication radius \(R_c=8\). It is then fine-tuned from the fixed-radius checkpoint under randomly sampled radii \(R_c \sim U(4,10)\). This setup is used to test whether the learned policy can adapt to changing communication topology rather than only fitting a single radius.

### Compared Methods

We compare three main methods:

1. MAPPO, a multi-agent reinforcement learning baseline without an explicit graph structure.
2. GAT-MAPPO, which adds standard graph attention to the MAPPO framework.
3. EA-RG-MAPPO-S, the final proposed method with edge-aware role graph encoding and staged random-radius fine-tuning.

For ablation analysis, RG-MAPPO and EA-RG-MAPPO are also included to analyze the effects of role graph modeling, edge-aware attention, and staged fine-tuning.

### Main Results

The final main table is based on 300 evaluation episodes per seed. EA-RG-MAPPO-S achieves success rates from 0.879 to 0.926 across four communication radii and keeps collision rates between 0.054 and 0.086. At radius 4, MAPPO has a collision rate of \(0.228 \pm 0.099\), while EA-RG-MAPPO-S reduces it to \(0.054 \pm 0.007\). Compared with GAT-MAPPO, EA-RG-MAPPO-S achieves higher success rates and lower collision rates at radii 8 and 10, with smaller standard deviations. These results indicate that standard graph attention alone does not guarantee cross-radius stability, while edge-aware attention and random-radius fine-tuning jointly provide a more robust coordination representation.

The key EA-RG-MAPPO-S results are:

```text
radius=4:  success=0.926 ± 0.004, collision=0.054 ± 0.007
radius=6:  success=0.919 ± 0.012, collision=0.064 ± 0.006
radius=8:  success=0.890 ± 0.021, collision=0.083 ± 0.012
radius=10: success=0.879 ± 0.017, collision=0.086 ± 0.020
```

The corresponding source files are:

```text
results/final_comm_300_summary.csv
results/latex_final_comm_300_table.tex
results/figures/final_300_success_rate.png
results/figures/final_300_collision_rate.png
```

### Ablation Analysis

The full ablation table is evaluated with 100 episodes per seed and is used for module analysis. The comparison among RG-MAPPO, EA-RG-MAPPO, and EA-RG-MAPPO-S indicates that relative edge features reduce collision under small communication radii and alleviate instability at radius 8 for some seeds. Staged random-radius fine-tuning improves generalization at radius 10 and makes the policy more balanced across multiple communication radii.

This ablation table has a different evaluation budget from the 300-episode final main table. Therefore, it is used as module-level evidence and should not be merged with the final main results without clearly marking the number of evaluation episodes.

### Visualization Analysis

Per-seed scatter plots show that MAPPO has larger seed-to-seed variation, while EA-RG-MAPPO-S has more concentrated success and collision values. Trajectory case studies show that baseline methods may produce inter-UAV collisions under the same environment seed, whereas EA-RG-MAPPO-S can maintain successful pursuit. Attention heatmaps show that the graph attention distribution changes with communication radius, supporting the interpretation that the policy adapts its information aggregation under limited communication.

The visualization files include:

```text
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

### Target-Intent Branch Diagnostic

The implementation previously included an auxiliary target-intent prediction branch. Diagnostic results show a plain accuracy of 0.587 and a balanced accuracy of 0.200, indicating that the branch mainly predicts the majority class. Therefore, this branch cannot support a high-accuracy intent-recognition claim and is not used as a main contribution. Future work on intent modeling should introduce short history, target turning-rate features, more balanced target maneuver sampling, and balanced accuracy as a primary metric.

### Target-Speed Robustness

To check whether the limited-communication stability is tied to a single target-speed setting, an appendix-level robustness evaluation is conducted without retraining. The mixed target speed is set to 0.60, 0.75, and 0.90, and policies are evaluated at communication radii 4 and 8 with 100 episodes per seed. As target speed increases, all methods tend to have lower success rates and higher collision rates. However, EA-RG-MAPPO-S still keeps lower collision rates under stronger target motion.

At target speed 0.90, EA-RG-MAPPO-S obtains a success rate of 0.867 and a collision rate of 0.097 at radius 4, while MAPPO and GAT-MAPPO have collision rates of 0.240 and 0.237, respectively. At radius 8, EA-RG-MAPPO-S has a collision rate of 0.130, lower than MAPPO's 0.300 and GAT-MAPPO's 0.203. This result supports the claim that the low-collision behavior is not caused only by the default target-speed setting.

This robustness evaluation is an appendix-level 100-episode evaluation and does not replace the final 300-episode main table.

### Evaluation-Time Edge-Feature Masking Diagnostic

To analyze the dependence on different edge-feature groups, an evaluation-time masking diagnostic is performed. The trained EA-RG-MAPPO-S parameters are kept fixed, and one group of edge-feature dimensions is set to zero during evaluation. This is not a retrained structural ablation, so it is used only as mechanism-level diagnostic evidence.

Masking relative position, distance, bearing, or relative velocity individually leads to small changes in the 30-episode diagnostic mean. Masking communication reachability and target-node flags produces a small but consistent success drop and collision increase at radii 4 and 8. Masking all edge features does not cause catastrophic degradation, suggesting that node features, adjacency masks, and local observations contain redundant information. Therefore, this diagnostic should be interpreted together with the training-time ablation table.

## Boundary for Later Use

```text
The main quantitative claim should use the 300-episode final table.
The ablation, target-speed robustness, and edge-feature masking results are supporting or appendix-level evidence with different evaluation budgets.
```

<!-- Source: docs/english_discussion_conclusion_draft.md -->

## Discussion

### Source of Stability under Limited Communication

The results suggest that stability under limited communication depends not only on whether a graph structure is used, but also on whether the graph contains task-relevant physical edge semantics. Standard GAT-MAPPO improves MAPPO under some communication radii, but still suffers from lower success rates and higher collision rates at radii 8 and 10. EA-RG-MAPPO-S maintains more stable behavior across radii by combining relative edge features with staged random-radius fine-tuning.

Mechanistically, the edge features provide two types of information. The first type is physical geometry, including distance, bearing, and relative velocity, which directly affects target encirclement and inter-UAV safety margins. The second type is communication topology, including communication reachability and distance normalized by the communication radius, which reflects the current information-sharing boundary. Staged random-radius fine-tuning further encourages the policy to behave consistently under different adjacency structures, making it more suitable for changing communication conditions than training only under a fixed radius.

### Boundary of Extension to LAG/6DOF Systems

An important property of the proposed method is the extensibility of its representation layer. Although the current experiments validate the algorithmic contribution in a two-dimensional pursuit environment, the role graph and edge-feature design are not restricted to two-dimensional states. When migrating to LAG/JSBSim or 6DOF air-combat simulators, node features can be extended to include three-dimensional position, attitude, velocity, overload, radar observations, and weapon states. Roles can also be extended to manned aircraft, UAVs, missiles, targets, and wingmen. Edge features can be expanded to include line-of-sight relation, radar detectability, missile no-escape-zone indicators, communication link quality, and formation-task relations.

This extension is not a direct reuse of the entire training environment. The reusable components are the role graph encoder, the edge-feature design principle, the communication masking mechanism, and the MAPPO training interface. The parts that must be re-adapted include 6DOF dynamics, action space, reward function, sensor model, weapon engagement logic, and simulator stepping interface. Therefore, future work can preserve the core algorithmic structure, but still requires platform-level engineering migration and new experimental validation.

### Limitations

This work has several limitations. First, the current environment is a simplified two-dimensional pursuit task and should not be treated as a full air-combat system. Second, the auxiliary target-intent branch has not achieved reliable balanced accuracy, so it is not used as a main contribution. Third, the final main results are based on three random seeds. Although 300 evaluation episodes per seed improve reliability, a more demanding journal submission may still benefit from five-seed evaluation or a small-scale LAG/JSBSim migration experiment.

## Conclusion

This paper proposes EA-RG-MAPPO-S for cooperative UAV pursuit under limited communication. The method uses a role graph representation and relative edge-feature enhanced graph attention to explicitly model relations among UAVs, targets, and communication topology. It further adopts staged random-radius fine-tuning to improve adaptation to changing communication radii. Experiments in a two-dimensional heterogeneous UAV pursuit environment show that the proposed method achieves lower collision rates and more stable behavior under mixed target maneuvers and multiple communication radii. These results indicate that injecting physical edge semantics into graph-based multi-agent reinforcement learning is valuable for limited-communication cooperative control. Future work will migrate the role graph and edge-aware policy structure to LAG/JSBSim or 6DOF air-combat environments and validate radar, missile, and human-UAV teaming factors in those new simulation platforms.

## Boundary for Later Use

```text
The discussion and conclusion describe extensibility, not completed 6DOF validation.
Any manuscript using this text should keep the current evidence boundary explicit.
```
