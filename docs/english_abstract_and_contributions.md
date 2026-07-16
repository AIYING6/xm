# English Abstract and Contributions

Date: 2026-07-13

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
