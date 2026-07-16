# English Discussion and Conclusion Draft

Date: 2026-07-13

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
