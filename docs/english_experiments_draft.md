# English Experiments Draft

Date: 2026-07-13

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
