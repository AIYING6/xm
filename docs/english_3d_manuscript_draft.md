# English 3DOF Manuscript Draft

Date: 2026-07-16

```text
Purpose:
This is a next-stage manuscript draft centered on the 3DOF heterogeneous UAV kill-chain recovery evidence.
It supersedes the old 2D-only narrative as the preferred Q2-oriented direction, but it is not yet a submission-ready paper.
```

## Title

Multi-Relation Role Graph Reinforcement Learning for Heterogeneous UAV Kill-Chain Recovery under Limited Communication and Intermittent Sensing

Alternative shorter title:

```text
Multi-Relation Role Graph Learning for Heterogeneous UAV Cooperative Interception
```

## Abstract

Heterogeneous unmanned aerial vehicle (UAV) teams must close cooperative kill chains under incomplete sensing, limited communication, and temporary platform or link degradation. A key challenge is that the platforms contributing to the kill chain often play different roles: a scout may detect the target, a relay may maintain information flow, and an attacker may form the final engagement window. Treating all relations as a single homogeneous graph can obscure whether an edge corresponds to perception, communication, or task support. This paper proposes EA-RG-MAPPO-S, a multi-relation edge-aware role graph multi-agent reinforcement learning method for 3DOF heterogeneous UAV cooperative interception. The method constructs separate perception, communication, and dynamic task-support relations, and performs role-pair-conditioned message propagation for centralized-training decentralized-execution policy learning. A staged topology curriculum is used to expose the policy to communication range variation, dropout, message delay, radar dropout, and temporary blue-node communication failure. Experiments in a constrained 3DOF cooperative interception environment show that the proposed method improves post-failure kill-chain recovery under relay-node communication failure. Compared with a single-graph MAPPO variant, EA-RG-MAPPO-S increases relay-failure recovery from 92.2% to 100.0% and reduces recovery time from 21.8 to 5.6 steps. Formal ablations show that removing dynamic task-support relations or role-pair message gates degrades recovery. A strict-sensing scenario-depth pilot further shows that the relay-failure recovery advantage remains when target-state fallback is removed from observations. These results indicate that multi-relation role-aware graph reasoning is useful for robust heterogeneous UAV cooperative decision making under limited communication and intermittent sensing.

## Keywords

Heterogeneous UAVs; multi-agent reinforcement learning; multi-relation graph; limited communication; intermittent sensing; cooperative interception; kill-chain recovery

## Contributions

1. A 3DOF heterogeneous UAV cooperative interception task is constructed around kill-chain closure rather than simple pursuit success. The task includes role-differentiated scout, relay, and attacker UAVs, constrained 3DOF motion, radar sensing, limited communication, message age, attack-window formation, and temporary communication-node failure.
2. A multi-relation role graph policy is proposed. Perception, communication, and dynamic task-support relations are encoded separately, and role-pair-conditioned message propagation is used to decide how information should flow between scouts, relays, attackers, and target nodes.
3. A staged topology curriculum is introduced for 3DOF training. The policy is fine-tuned under randomized communication range, dropout, delay, radar dropout, and temporary node failure, improving recovery under topology disruption.
4. A focused evidence chain is provided. Relay-failure recovery is used as the main statistical claim, task-support and role-pair-gate ablations support the mechanism, and a strict-sensing scenario-depth pilot verifies that the relay-failure advantage is not caused by target-state fallback in observations.

## Claim Boundary

```text
Supported:
Multi-relation role graph learning improves 3DOF relay-failure kill-chain recovery under matched seeds and paired evaluations.
Dynamic task-support relations and role-pair message gates are supported by formal ablations.
Strict sensing strengthens the relay-failure scenario-depth evidence.

Not yet supported:
Full 4v2 red-blue self-play superiority.
Full 6DOF JSBSim training with all baselines.
Online missile, radar, and human-UAV teaming validation.
General superiority under all communication, sensing, and maneuvering-target conditions.
```

## 1. Introduction

Cooperative UAV decision making is moving from platform-centric pursuit toward networked sensing, communication, and engagement. In such missions, success is not determined only by whether a single aircraft approaches a target. A team must detect the target, share or relay target information, keep usable communication paths, position an appropriate shooter, and form an engagement window before the target escapes or the team loses situational awareness. This sequence can be viewed as a cooperative kill chain. When sensing is intermittent or communication topology changes, the kill chain may break even if individual UAVs remain physically close to the target.

Heterogeneous UAV teams make this problem more difficult. A scout UAV may have a wider radar field of view but weaker attack capability. A relay UAV may have a larger communication range but weaker maneuverability. An attacker may have better engagement geometry but may depend on target information discovered by another platform. Therefore, the relation between two UAVs is not simply a generic graph edge. A scout-to-attacker edge can represent target-information support; a relay-to-attacker edge can represent communication reconstruction; and an attacker-to-relay edge can represent a request to maintain a useful path to the shooter. A policy that collapses all these relations into one union graph may miss the role-specific meaning of information flow.

Multi-agent reinforcement learning provides a practical framework for learning cooperative policies under centralized training and decentralized execution. MAPPO and graph-attention-based variants have been widely used as strong baselines for multi-agent tasks. However, a standard graph attention encoder usually aggregates neighbor features without explicitly separating the relation type that creates the edge. For heterogeneous UAV kill-chain recovery, relation type matters: perception, communication, and task support have different semantics and different failure modes.

This paper studies a realistic but implementable intermediate step toward high-fidelity air-combat decision making. Instead of directly training all baselines in a full 6DOF JSBSim environment, we build a lightweight 3DOF tactical interception environment that preserves the key decision constraints: three-dimensional position, speed, heading, flight-path angle, altitude limits, turn and climb constraints, radar detection, limited communication, message age, and attack-window metrics. This setting is suitable for running controlled multi-seed experiments while remaining extensible to future LAG/JSBSim replay.

We propose EA-RG-MAPPO-S, a multi-relation edge-aware role graph MAPPO method with staged topology curriculum. The method represents the UAV team and target as a role graph, separates perception, communication, and task-support relations, and applies role-pair-conditioned message propagation. The strongest result appears under relay-node communication failure: the multi-relation policy restores the kill chain more reliably and more quickly than a matched single-graph variant. Formal ablations further show that task-support relations and role-pair message gates contribute to this recovery behavior.

## 2. Related Work

### 2.1 Multi-Agent Reinforcement Learning for UAV Cooperation

Multi-agent reinforcement learning has been applied to cooperative pursuit, formation control, air combat maneuvering, and UAV swarm coordination. Centralized training and decentralized execution is attractive because the critic can use global training information while deployed agents use local observations. MAPPO is a strong and stable baseline for cooperative multi-agent tasks and is therefore used as the learning backbone in this work.

For UAV interception, however, success metrics based only on target capture or average reward are not enough. A cooperative air task also depends on sensing continuity, communication topology, and whether a shooter can form a valid attack window. This motivates evaluating kill-chain closure and post-failure recovery rather than only pursuit distance.

### 2.2 Graph Neural Networks and Relation Modeling

Graph neural networks provide a natural representation for multi-agent systems. Graph attention networks can aggregate information from dynamically changing neighbors, and many multi-agent methods use graph encoders to model interaction topology. In UAV tasks, relative position, velocity, line-of-sight geometry, and communication reachability are physically meaningful edge features.

Nevertheless, a single adjacency matrix may be insufficient for heterogeneous kill-chain recovery. The same pair of nodes can be related by sensing, communication, or task-support semantics. The present work therefore uses a multi-relation graph and preserves a single-graph variant as a controlled baseline.

### 2.3 Limited Communication and Intermittent Sensing

Real UAV teams cannot assume globally available information. Communication links can disappear because of distance, dropout, delay, interference, or node failure. Sensing can also be intermittent due to radar field of view, range, and dropout. Existing communication-aware MARL methods often focus on when to communicate or how to compress messages. This paper focuses on a complementary question: how to structure role-aware relational reasoning so that a heterogeneous team can recover a kill chain when communication support is disrupted.

## 3. Problem Formulation

We consider a 3DOF cooperative interception task with three blue UAVs and one red high-value target. The blue team contains a scout, a relay, and an attacker. At each step, each blue UAV has a state including 3D position, speed, heading, flight-path angle, remaining energy, radar capability, communication range, and role type. The red target has 3D position, speed, heading, and flight-path angle.

Each blue agent selects a discrete high-level command from turn, climb, and speed-command combinations. The environment then updates the 3DOF dynamics under turn-rate, climb, speed, altitude, and boundary constraints. The policy therefore controls tactical maneuvering rather than low-level flight stabilization.

The episode objective is to close the cooperative kill chain. A chain is considered closed when the target is detected, target information is available to an attack-capable platform through sensing or communication, and a valid attack window is held for the required duration. Temporary communication-node failure disables the communication contribution of a specified blue UAV for a fixed interval, forcing the team to recover the information path or form the attack window through other relations.

The main metrics are:

- task success rate;
- post-failure kill-chain recovery rate;
- post-failure recovery steps;
- chain-closed rate during failure;
- tracking rate during failure;
- communication connectivity;
- mean message age;
- timeout rate;
- episode length;
- collision and flight-constraint violation rates.

## 4. Method

### 4.1 Overview

EA-RG-MAPPO-S combines a MAPPO-style training objective with a multi-relation role graph actor. The critic uses centralized training information, while the actor receives local observations and graph observations. The policy is executed in a decentralized manner.

The method contains three main components:

1. a role-aware graph representation for UAV and target nodes;
2. multi-relation message propagation over perception, communication, and task-support relations;
3. staged topology curriculum training.

### 4.2 Multi-Relation Role Graph

At each step, the graph contains blue UAV nodes and a red target node. Each node includes normalized motion features, role indicators, detection status, attack-window status, and team-specific state. Directed edge features include relative position, distance, line-of-sight direction, relative velocity, team relation, sensing availability, communication reachability, task-support relation, message age, information confidence, and attack-hold progress.

Three relation channels are constructed:

- perception relation: a blue UAV directly detects the target;
- communication relation: two blue UAVs can exchange information;
- task-support relation: a role-compatible UAV is currently useful for reconnaissance, relay, or attack support.

The single-graph baseline uses the union of these relations. The proposed model keeps relation channels separate and learns role-pair-conditioned messages. This allows the model to treat scout-to-attacker, relay-to-attacker, attacker-to-relay, and attacker-to-attacker information flows differently.

### 4.3 Topology Curriculum

The training process starts from behavior cloning on a geometric demonstrator and then uses PPO fine-tuning. The topology curriculum gradually exposes the policy to communication range variation, communication dropout, message delay, radar dropout, and random temporary blue-node communication failure. This curriculum is a training aid rather than the primary innovation. The main method contribution remains the multi-relation role graph and role-conditioned message propagation.

### 4.4 Strict-Sensing Option

The default 3DOF environment is kept reproducible for historical experiments. A stricter sensing option is added for scenario-depth evaluation. Under strict sensing, local observations, shared observations, and graph target nodes do not fall back to the true target state before detection. Before the first valid detection, a fixed search prior is used; after detection, the last detected target position and velocity are used. This setting tests whether the learned recovery behavior depends on target-state leakage.

## 5. Experiments

### 5.1 Experimental Setup

The main experiments compare a single-graph MAPPO variant and EA-RG-MAPPO-S. Both use the same 3DOF environment, behavior-cloning warm start, PPO interface, and topology-curriculum budget. Evaluation uses matched training seeds and matched evaluation seeds. Paired bootstrap confidence intervals are reported for key deltas.

The main node-failure scenarios are relay failure and scout failure. In both cases, the selected blue node loses communication functionality for 80 steps starting at step 40. The primary metrics are recovery rate and recovery steps after failure begins.

### 5.2 Main Node-Failure Results

Relay failure is the strongest main result. The single-graph policy recovers the kill chain in 92.2% of paired episodes, while EA-RG-MAPPO-S recovers in 100.0%. The paired recovery improvement is +7.8 percentage points with a 95% confidence interval of [+2.2, +13.3]. Recovery steps are reduced from 21.8 to 5.6, with a paired delta of -16.2 and a 95% confidence interval of [-28.0, -4.5].

These results show that the proposed multi-relation role graph improves not only final success but also the speed of restoring a broken kill chain. This is the main statistical claim of the 3DOF study.

Scout failure is positive but weaker. Recovery increases from 94.4% to 96.7%, and recovery steps decrease from 17.1 to 12.7, but the confidence intervals cross zero. Therefore, scout failure is treated as supporting trend evidence.

### 5.3 Robustness Trends

Additional evaluations include communication dropout 0.30, two-step message delay, radar dropout 0.25, and communication range 0.75. EA-RG-MAPPO-S shows positive trends under dropout, delay, and radar perturbation, but the paired confidence intervals are not separated. Communication range 0.75 is mixed. These scenarios should be reported to show evaluation breadth, but not used as primary conclusions.

### 5.4 Mechanism Ablations

Removing the dynamic task-support relation produces the clearest mechanism-level degradation. Under relay failure, the full model improves recovery over the no-task-support variant by +11.1 percentage points with a 95% confidence interval of [+5.6, +17.8], and reduces recovery steps by -23.5 with a 95% confidence interval of [-37.7, -11.6]. Under scout failure, the full model also improves recovery by +8.9 percentage points with a 95% confidence interval of [+3.3, +15.6], and reduces recovery steps by -18.8 with a 95% confidence interval of [-32.9, -7.0].

Disabling the role-pair message gate also reduces relay-failure recovery. The full model improves recovery by +4.4 percentage points with a 95% confidence interval of [+1.1, +8.9], and reduces recovery steps by -9.8 with a 95% confidence interval of [-19.2, -2.7]. This indicates that the relation channels and role-pair-conditioned messages both contribute to the recovery mechanism.

### 5.5 Strict-Sensing Scenario Depth

To test a stricter partial-observation setting, existing node-failure curriculum checkpoints are fine-tuned for 10 PPO updates under strict sensing and then evaluated with three seeds and 30 episodes per checkpoint-scenario. This result is labeled as a scenario-depth pilot rather than a full-budget final experiment.

Under strict-sensing relay failure, EA-RG-MAPPO-S recovers the kill chain in 96.7% of episodes, compared with 71.1% for the single-graph policy. The paired recovery delta is +25.6 percentage points with a 95% confidence interval of [+15.6, +36.7]. Recovery steps decrease from 67.5 to 13.6, corresponding to -53.9 steps with a 95% confidence interval of [-75.3, -32.6].

This result is important because it removes the target-state fallback from observations and still shows a separated relay-failure recovery advantage. The scout-failure strict-sensing result remains positive but non-separated and is therefore kept as a trend.

### 5.6 Qualitative Relay-Failure Case

A representative replay case illustrates the statistical result. Under the same relay-failure episode, the single-graph policy fails to restore the kill chain and times out at 260 steps, while EA-RG-MAPPO-S closes the chain at step 48. The trajectory and timeline visualization indicate that the multi-relation policy reconstructs useful support relations earlier and forms an attack window before the episode becomes a long timeout.

## 6. Discussion

The experiments support a focused conclusion: multi-relation role-aware graph reasoning improves kill-chain recovery when a key communication-support node fails. The relay-failure result is statistically separated, the task-support and role-pair-gate ablations support the mechanism, and the strict-sensing pilot strengthens the partial-observation credibility of the result.

The evidence should be interpreted carefully. First, the current setting is a 3v1 constrained 3DOF interception task, not a complete 4v2 red-blue self-play environment. Second, the main target policy is still the straight-target setting. Maneuvering-target pilots are useful for scenario screening, but their absolute success rates are not yet high enough for main-table claims. Third, strict sensing is currently a 10-update fine-tuning pilot. It is useful as scenario-depth evidence, but should be labeled honestly. Fourth, LAG/JSBSim is currently a migration and replay direction, not a completed full-baseline training environment.

## 7. Conclusion

This paper presents EA-RG-MAPPO-S for 3DOF heterogeneous UAV cooperative interception under limited communication and intermittent sensing. The method separates perception, communication, and task-support relations and uses role-pair-conditioned message propagation to support cooperative kill-chain recovery. In relay-node communication failure, EA-RG-MAPPO-S improves post-failure recovery probability and reduces recovery time compared with a single-graph MAPPO variant. Formal ablations show that dynamic task-support relations and role-pair message gates are important contributors to this behavior. A strict-sensing scenario-depth pilot further shows that the relay-failure recovery advantage remains when target-state fallback is removed from observations.

Future work will extend the current 3v1 task to 4v2 red-blue confrontation, add online missile and radar models, and use LAG/JSBSim for higher-fidelity replay and feasibility validation.

## Next Revision Checklist

- Replace placeholder related-work paragraphs with cited references.
- Decide whether to run a longer strict-sensing fine-tuning budget.
- Add a task-scene figure and a multi-relation role-graph figure.
- Convert the main 3DOF table into a manuscript-ready LaTeX table.
- Decide whether the old 2D results should be moved to appendix or treated as preliminary evidence.
