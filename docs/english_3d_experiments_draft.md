# English 3DOF Experiments Draft

Date: 2026-07-16

```text
Purpose:
This draft converts the current 3DOF evidence stack into manuscript-ready experimental narrative.
It is intended for the next-stage 3DOF paper direction, not for the older 2D-only manuscript without revision.
```

## Experiments

### Experimental Scenario

The 3DOF experiments evaluate heterogeneous UAV cooperative interception under limited communication, intermittent sensing, and temporary communication-node failure. The task contains three blue UAVs and one red high-value target. The blue team consists of a scout UAV, a relay UAV, and an attack UAV. The three platforms differ in radar range, communication range, maneuverability, speed envelope, and attack-window capability. The red target follows the configured target policy and must be detected, tracked, and approached until an effective attack window is formed.

Each blue UAV is controlled through a tactical 3DOF interface. The policy outputs discrete turn, climb, and speed commands, while the environment updates three-dimensional position, speed, heading, flight-path angle, altitude, and flight-envelope constraints. This interface avoids forcing the reinforcement learning policy to learn low-level flight stabilization, and focuses learning capacity on cooperative sensing, communication, and attack-window formation.

The task is evaluated as a kill-chain closure problem rather than a simple pursuit problem. A successful episode requires the blue team to detect the target, maintain usable target information, preserve or recover communication paths, and hold an attack window for the required duration. The key evaluation metrics are task success, post-failure kill-chain recovery, recovery steps, chain-closed rate during failure, tracking rate during failure, communication connectivity, message age, timeout rate, and episode length.

### Compared Policies and Training Protocol

The main comparison is between a single-graph MAPPO variant and the proposed multi-relation EA-RG-MAPPO-S policy. Both policies use the same MAPPO training framework, behavior-cloning warm start, and PPO fine-tuning interface. The single-graph variant uses the union graph as its relational input. EA-RG-MAPPO-S separates perception, communication, and dynamic task-support relations, and applies role-pair-conditioned message propagation over these relation channels.

The main topology-curriculum checkpoints are obtained by fine-tuning nominal 3DOF BC-to-PPO checkpoints under randomized communication range, communication dropout, message delay, radar dropout, and temporary blue-node communication failure. Evaluation uses matched training seeds, matched evaluation seeds, and paired episode bootstrap confidence intervals. Unless otherwise stated, each formal relay/scout node-failure result uses three seeds and 30 evaluation episodes per checkpoint-scenario.

An oracle geometric pursuit controller is evaluated only as a diagnostic reference. It directly uses simulator target state and therefore is not a fair decentralized learning baseline. Its role is to show task solvability and to expose whether a scenario is too easy, not to support the main method comparison.

### Node-Failure Recovery Results

The strongest main result is obtained under relay-node communication failure. In this setting, the communication function of the relay UAV is disabled for 80 steps starting at step 40. The single-graph policy recovers the kill chain in 92.2% of paired episodes, whereas EA-RG-MAPPO-S recovers in 100.0% of episodes. The paired recovery improvement is +7.8 percentage points with a 95% confidence interval of [+2.2, +13.3]. EA-RG-MAPPO-S also reduces post-failure recovery time from 21.8 steps to 5.6 steps, corresponding to a step reduction of -16.2 with a 95% confidence interval of [-28.0, -4.5].

This result supports the central claim that multi-relation role-graph reasoning improves kill-chain recovery after a key communication-support node is disrupted. The effect is not merely a higher final reward: it appears in recovery probability, recovery timing, and episode length.

The scout-failure scenario is positive but weaker. EA-RG-MAPPO-S improves recovery from 94.4% to 96.7%, but the paired confidence interval crosses zero. Recovery steps decrease from 17.1 to 12.7 on average, but this difference is also not separated. Therefore, scout failure should be reported as supporting trend evidence rather than a primary claim.

### Communication and Sensing Robustness

Additional robustness tests evaluate communication dropout, message delay, radar dropout, and communication range compression. EA-RG-MAPPO-S shows positive trends under communication dropout 0.30, two-step message delay, and radar dropout 0.25, with fewer average steps than the single-graph variant. However, the paired success confidence intervals cross zero in these scenarios. Communication range 0.75 is mixed and should be treated as a stress case rather than a positive result. These findings indicate that the method has useful robustness tendencies, but the manuscript should center the main statistical claim on relay-failure recovery.

### Mechanism Ablations

Two formal mechanism ablations support the design of the multi-relation role graph.

First, removing the dynamic task-support relation causes a clear performance drop. Under relay failure, the full model achieves 100.0% recovery, while the no-task-support variant achieves 88.9%. The recovery improvement is +11.1 percentage points with a 95% confidence interval of [+5.6, +17.8], and recovery time is reduced by -23.5 steps with a 95% confidence interval of [-37.7, -11.6]. Under scout failure, the full model also improves recovery by +8.9 percentage points with a 95% confidence interval of [+3.3, +15.6], and reduces recovery time by -18.8 steps with a 95% confidence interval of [-32.9, -7.0]. This ablation provides the strongest mechanism-level evidence: explicitly modeling task-support edges is important for recovering the cooperative kill chain.

Second, disabling the learned role-pair message gate while preserving the relation channels also degrades relay-failure recovery. Under relay failure, the full model improves recovery by +4.4 percentage points with a 95% confidence interval of [+1.1, +8.9], and reduces recovery time by -9.8 steps with a 95% confidence interval of [-19.2, -2.7]. Under scout failure, the effect is positive but not separated. This shows that relation channels alone are not the whole explanation; role-conditioned message weighting contributes to the relay-failure recovery behavior.

Other input ablations are treated as auxiliary diagnostics. Removing role identity yields a modest relay-failure recovery-speed benefit for the full model but mixed scout-failure results. Removing edge features has only weak diagnostic effect in the current setting. These results should not be promoted as primary mechanism claims.

### Strict-Sensing Scenario-Depth Experiment

The initial straight-target node-failure task is useful for recovery analysis, but it can be too easy because the original observation construction falls back to true target state before the first valid detection. To test a stricter partial-observation setting, an opt-in strict-sensing protocol is added. Under `--strict-target-sensing`, local observations, shared observations, and graph target nodes no longer fall back to true target state before detection. Before the first valid detection, the policy receives a fixed search prior; after detection, it receives the last detected target position and velocity.

Existing topology-curriculum checkpoints do not directly transfer well to this strict-sensing setting. A zero-shot screen shows that strict sensing must be trained with a matched curriculum rather than evaluated as an out-of-distribution perturbation. Therefore, the strict-sensing result is reported as a budget-labeled scenario-depth pilot: the existing node-failure curriculum checkpoints are fine-tuned for 10 PPO updates under strict sensing and then evaluated with three seeds and 30 episodes per checkpoint-scenario.

Under strict sensing and relay failure, EA-RG-MAPPO-S recovers the kill chain in 96.7% of episodes, while the single-graph policy recovers in 71.1%. The paired recovery improvement is +25.6 percentage points with a 95% confidence interval of [+15.6, +36.7]. Recovery time is reduced from 67.5 steps to 13.6 steps, corresponding to -53.9 steps with a 95% confidence interval of [-75.3, -32.6]. This is a strong scenario-depth result because it removes target-state leakage and still shows separated recovery improvement.

Under strict-sensing scout failure, the recovery improvement is positive but not separated. The recovery rate increases from 78.9% to 85.6%, and recovery time decreases from 51.0 steps to 37.0 steps, but the confidence intervals cross zero. Therefore, the strict-sensing claim should be restricted to relay-failure recovery and should not be generalized to all node failures.

### Qualitative Case Study

A replay case is selected from the relay-failure evaluation to illustrate the recovery mechanism. In the selected episode, the single-graph policy fails to recover the kill chain after relay failure and times out at 260 steps. In contrast, the multi-relation policy closes the kill chain at step 48. The trajectory and timeline visualization show that the multi-relation policy restores the support path more quickly and forms the attack window before the episode degenerates into a long timeout. This case study is qualitative; it should be used to explain the statistical result rather than replace it.

### Discussion of Experimental Boundaries

The 3DOF evidence supports a focused claim: multi-relation, role-aware graph reasoning improves cooperative kill-chain recovery under temporary communication-node failure, especially when the relay node is disrupted. The mechanism ablations further show that task-support relations and role-pair message gates are important contributors to this behavior. The strict-sensing experiment strengthens the scenario depth by removing target-state leakage from observations.

Several boundaries should remain explicit. First, the current 3DOF scenario is still a 3v1 cooperative interception task, not a full 4v2 red-blue self-play system. Second, the red target in the main table is the straight-target setting; maneuvering-target pilots are discriminative but not yet paper-ready because absolute success is low. Third, the strict-sensing result uses a 10-update fine-tuning pilot and should be labeled as such unless a longer fine-tuning budget is run. Fourth, JSBSim/LAG integration remains a future replay and feasibility-validation direction, not a completed 6DOF training result.

## Manuscript-Safe Claim Wording

The following wording is consistent with the current evidence:

```text
In a 3DOF heterogeneous UAV cooperative interception task, EA-RG-MAPPO-S improves post-failure kill-chain recovery under relay-node communication failure. Compared with a single-graph MAPPO variant, the proposed multi-relation role graph increases relay-failure recovery probability and reduces recovery time under matched seeds and paired evaluation episodes. Formal ablations show that dynamic task-support relations and role-pair-conditioned message gates are important for this improvement. A strict-sensing scenario-depth pilot further shows that the relay-failure recovery advantage remains when target-state fallback is removed from observations.
```

The following wording should be avoided:

```text
EA-RG-MAPPO-S is proven superior under all 3DOF communication and sensing perturbations.
The current system solves full 6DOF air combat with missiles and human-UAV teaming.
The strict-sensing result is a full-budget final result equivalent to all other formal experiments.
The oracle geometric pursuit controller is a fair decentralized baseline.
```
