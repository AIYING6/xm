# Visualization and Intent Diagnostics

Date: 2026-07-13

## Generated Trajectory Cases

Script:

```text
scripts/plot_trajectory_cases.py
```

Generated figures:

```text
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
```

Radius 4 case:

```text
env seed = 20000
MAPPO: collision, step=34
GAT-MAPPO: success, step=31
RI edge staged: success, step=52
```

Radius 10 case:

```text
env seed = 20001
MAPPO: success, step=36
GAT-MAPPO: collision, step=46
RI edge staged: success, step=47
```

Current use:

```text
These figures can support qualitative discussion, but they are case studies only.
They should be paired with the 3-seed quantitative table.
```

## Intent Confusion Matrix

Script:

```text
scripts/plot_intent_confusion.py
```

Original RI edge staged checkpoint:

```text
model = results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt
episodes = 100
radius = 8
accuracy = 0.587
balanced_accuracy = 0.200
```

Per-class recall:

| Intent | Recall |
|---|---:|
| straight | 0.000 |
| escape_nearest | 1.000 |
| turn_left | 0.000 |
| turn_right | 0.000 |
| unknown | 0.000 |

Diagnosis:

```text
The intent head collapses to predicting escape_nearest.
The apparent 0.587 accuracy is caused by class imbalance, not real multi-class intent recognition.
```

Balanced-loss diagnostic fine-tune:

```text
model = results/ri_gmappo_edge_balanced_intent_seed1_20/actor_critic_latest.pt
episodes = 100
radius = 8
accuracy = 0.348
balanced_accuracy = 0.203
```

Per-class recall:

| Intent | Recall |
|---|---:|
| straight | 0.000 |
| escape_nearest | 0.505 |
| turn_left | 0.005 |
| turn_right | 0.264 |
| unknown | 0.240 |

Diagnosis:

```text
Class-balanced cross entropy prevents complete single-class collapse,
but it does not produce meaningful balanced intent recognition.
The underlying issue is likely observability/label design, not just loss weighting.
```

## Research Implication

Do not claim:

```text
The current model accurately recognizes target intent.
```

Defensible wording:

```text
An auxiliary target-intent branch was explored, but single-frame intent prediction under the current mixed-policy labels is weak.
The stronger current evidence comes from role graph representation, edge-aware attention, and staged communication-radius adaptation.
```

Recommended next fix if intent remains a main innovation:

```text
Use short-horizon kinematic history or observed target turn-rate features.
Then evaluate intent by balanced accuracy and confusion matrix, not plain accuracy alone.
```

Recommended practical paper direction if time is limited:

```text
Make edge-aware role graph coordination under limited communication the main contribution.
Keep intent prediction as an auxiliary/ablation module unless the balanced accuracy is fixed.
```

## RI Attention Heatmaps

Script:

```text
scripts/plot_ri_attention_heatmap.py
```

Generated figures:

```text
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

Generated CSV files:

```text
results/ri_attention_heatmap_r4.csv
results/ri_attention_heatmap_r10.csv
```

Radius 4 observation:

```text
UAV nodes mainly attend to themselves and the target.
Some teammate attention weights are zero because communication edges are unavailable.
```

Radius 10 observation:

```text
Attention is more evenly distributed across teammates and target.
This reflects the denser communication graph under a larger communication radius.
```

Use in paper:

```text
These heatmaps support the limited-communication graph interpretation.
They are more defensible than the current intent confusion result.
```
