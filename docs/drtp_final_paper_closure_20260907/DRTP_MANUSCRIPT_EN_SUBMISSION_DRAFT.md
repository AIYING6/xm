# Dynamic Robust Topology Prioritization for Heterogeneous UAV Cooperation Under Topology Failures

**Authors:** [Author names]  
**Affiliations:** [Affiliations]  
**Corresponding author:** [Email]

> **Manuscript status.** Submission-oriented English draft. The 3-UAV A/B, frozen OOD, and matched PLR-style results are complete. The formal 6-UAV block and measured runtime table remain placeholders and must be filled only from frozen aggregation artifacts.

## Abstract

Heterogeneous unmanned aerial vehicle (UAV) teams rely on role-specific sensing and communication paths to coordinate interception and tracking. Node failures, delayed links, and topology degradation can disrupt these paths, yet training commonly samples a finite set of failure conditions uniformly. We introduce Dynamic Robust Topology Prioritization (DRTP), a reset-side training-exposure allocation procedure for a frozen topology-failure support. DRTP leaves the policy architecture, observations, reward, transition dynamics, action masks, and PPO objective unchanged. Instead, it retains a fixed nominal-condition mass and reallocates the remaining probability across semantically defined failure groups according to their nominal-referenced completed-return deficits. A bounded-simplex projection preserves minimum exposure for every group and prevents any single group from dominating training.

We evaluate DRTP against fully matched Uniform Topology Replay (UTR) at a fixed 10M-environment-step endpoint using two independent five-seed training cohorts. DRTP achieved higher mean perturbed return than UTR in cohort A (216.66 versus 177.02) and cohort B (210.34 versus 187.18); the worst-seed return was also higher in both cohorts. Under frozen structural held-out conditions, mean DRTP–UTR return differences were +22.77 and +11.96 in cohorts A and B, respectively. A matched PLR-style comparator was competitive but cohort-dependent: cohort A favored DRTP on return, lower tail, and timeout, whereas cohort B favored PLR-style replay on return and dispersion while DRTP retained lower timeout. These results support a bounded conclusion: topology-semantic reset allocation can provide repeated cohort-level robustness gains over matched uniform replay under the evaluated frozen topology-failure interface. The study does not claim all-seed superiority, uniform safety improvement, real-flight readiness, or cross-scale transfer beyond the pending formal six-UAV evaluation.

**Keywords:** heterogeneous UAVs; multi-agent reinforcement learning; topology failures; robust training; prioritized sampling; MAPPO

## 1. Introduction

Cooperative UAV teams are increasingly considered for inspection, search, surveillance, and interception tasks that require agents with distinct sensing, relaying, and execution roles to act under partial observations. In such systems, a communication-node failure is not merely a local perturbation: it can alter the route through which task-relevant information reaches the agent that must act. Communication-aware multi-agent reinforcement learning (MARL) and distributed learning have therefore been studied as routes to robust coordination under noisy or impaired links [1,2].

This paper addresses a different, complementary question. Suppose the policy architecture, communication interface, reward, and topology-failure support are fixed. How should training exposure be allocated across the nominal and failure conditions in that support? Uniform sampling is transparent and forms a strong control, but it treats conditions that have already been learned and conditions that remain persistently difficult as equally deserving of the training budget. Curriculum learning and adaptive environment sampling motivate changing training distributions as learning evolves [3,4]. However, a topology-failure support is not an unstructured collection of levels: failed node identity, failure onset, and duration have role and information-path semantics. A useful allocation rule must retain nominal-task exposure and prevent a small number of extreme failures from consuming the training distribution.

We propose Dynamic Robust Topology Prioritization (DRTP), a constrained allocation mechanism that operates only when an environment is reset. DRTP partitions a frozen support into one nominal group and six non-nominal topology-failure groups. It estimates each group’s completed-return deficit relative to the nominal group, updates a conditional failure-group distribution on a bounded simplex, and samples uniformly within the selected frozen group. The procedure does not introduce a new graph, failure condition, actor input, critic input, reward, loss term, or policy objective. Consequently, UTR and DRTP differ only in their allocation of resets from the same frozen support.

The contribution of this study is fourfold.

1. We formulate topology-failure exposure allocation as a constrained reset-side training problem, preserving a nominal anchor and a finite, semantically specified failure support.
2. We provide an auditable DRTP procedure based on nominal-referenced group deficits, bounded group probabilities, and unchanged MAPPO learning.
3. We evaluate the method using two independent fresh five-seed cohorts at a fixed 10M-step endpoint, with cohort A and B reported separately rather than pooled for a primary conclusion.
4. We use frozen structural and parameter-shift evaluations and a matched PLR-style comparator to delimit the empirical scope of the method. The six-UAV cross-scale protocol is retained as a pending formal evidence block.

## 2. Related Work

### 2.1 MARL for communication-constrained UAV coordination

Communication-aware MARL has been used to jointly model coordination and information exchange under noisy channels [1]. Distributed reinforcement learning has also been used for UAV swarm control with communication impairments and transfer across scenarios [2]. These studies focus on learning control or communication policies under a specified interaction model. DRTP instead holds the policy learner and the topology-failure support fixed, and asks how often semantically different failures should be encountered during training.

### 2.2 Training-distribution design

Curriculum learning organizes tasks or samples to make a target problem more learnable [3], while domain randomization changes simulated conditions to improve transfer across specified variations [5]. Prioritized Level Replay (PLR) adapts level replay according to estimated learning potential [4]. DRTP shares the high-level premise that exposure may change with learning, but its allocation object is a hierarchy of topology-failure groups with explicit role semantics. In addition, DRTP fixes nominal exposure and constrains non-nominal probabilities to a bounded simplex.

### 2.3 Positioning of DRTP

DRTP is not an architecture modification, a communication-learning method, or a reward-shaping method. Its contribution is a topology-aware training-exposure allocator. The PLR-style implementation is therefore treated as a matched external comparator rather than a weak baseline or a reproduction of every PLR variant. The comparison is intended to test whether topology-semantic allocation is empirically distinguishable from a generic priority-driven allocation under a common support and budget.

## 3. Problem Formulation

Consider a cooperative team of `n` heterogeneous UAV agents with role-specific observations and communication adjacency. At reset, the environment selects a condition `c` from a finite frozen condition set `C`. Each condition specifies a failed node, onset time, and duration. `C` is partitioned into a nominal group `N` and six non-nominal failure groups

`F = {F0, TE, TL, DS, DL, CP}`,

where `F0` denotes a fixed node failure; `TE` and `TL` denote early and late onsets; `DS` and `DL` denote short and long durations; and `CP` denotes compound conditions. Every group contains a pre-specified finite set of frozen members.

UTR and DRTP share the state space, action space, role-graph policy, centralized critic, reward, transition dynamics, action mask, PPO objective, training budget, and endpoint evaluation tape. Their only distinction is the reset-condition distribution. UTR assigns a fixed nominal mass `m_N = 0.5` and samples the six non-nominal groups uniformly. DRTP retains the same nominal mass and learns a conditional distribution `q_t` across the same six groups.

The independent statistical unit is a trained policy seed, not an individual evaluation episode. The primary endpoint is the checkpoint at 39,063 updates (10,000,128 environment steps); neither early stopping nor checkpoint selection is permitted.

## 4. Dynamic Robust Topology Prioritization

### 4.1 Frozen support and reset-side allocation

DRTP starts from the UTR distribution. At each reset, it selects the nominal group with probability `0.5`; otherwise it samples a non-nominal group from `q_t` and then samples uniformly among that group’s frozen members. Thus, the method reallocates exposure across existing groups and never generates a new topology or changes its semantics.

### 4.2 Nominal-referenced group difficulty

Completed episode returns are recorded in a group-specific window. After a 128-update warm-up, DRTP updates group exponential moving averages every 32 updates with coefficient `κ = 0.20`. When all groups have valid values, the non-negative difficulty of failure group `g` is

`d_g = min{2, max[0, (J̄_N − J̄_g) / max(|J̄_N|, 10⁻⁸)]}`.

The reference is the nominal group rather than an arbitrary global score: a group is emphasized only when its completed-return estimate remains below nominal performance.

### 4.3 Bounded probability update

Let `d̄` denote the mean difficulty across the six failure groups. DRTP forms a centered exponential candidate `q̃_g ∝ q_t,g exp(d_g − d̄)`, smooths it with the previous distribution using `β = 0.5`, and projects it to

`Q = {q : Σ_g q_g = 1, 0.05 ≤ q_g ≤ 0.35}`.

The lower bound guarantees continuing exposure to every frozen failure group, whereas the upper bound prevents a difficult group from absorbing the failure-training budget. The updated `q_(t+1)` affects later resets only; the actor, critic, PPO clipping, value targets, reward, and action masks remain unchanged.

### Algorithm 1. DRTP training procedure

**Input:** frozen groups `{N} ∪ F`, nominal mass `m_N`, PPO configuration, and a fixed training budget.

1. Initialize `q_0` to the uniform non-nominal distribution and initialize group windows and EMAs.
2. At reset, sample `N` with probability `m_N`; otherwise sample a group from `q_t` and then sample a frozen member uniformly within that group.
3. Run the unchanged MAPPO rollout and update.
4. Append each completed episode return to its selected group window.
5. Every 32 updates after warm-up, compute available group EMAs and nominal-referenced deficits.
6. Smooth and project the candidate group distribution to `Q`; use the result for subsequent resets.
7. Persist policy, optimizer, environment random state, and sampler runtime state until the fixed endpoint.

### Table 1. Mechanism comparison

| Property | UTR | PLR-style comparator | DRTP |
|---|---|---|---|
| Sampling object | Frozen topology conditions | Matched frozen support | Frozen topology-failure groups |
| Adaptation signal | None | Generic priority-driven replay signal | Nominal-referenced group return deficit |
| Topology semantics | Fixed but not used for allocation | Not topology-specific | Explicit failure group and within-group hierarchy |
| Nominal anchor | Fixed matched mass | Matched protocol | Fixed mass `m_N = 0.5` |
| Probability constraint | Uniform conditional allocation | Comparator-specific priority allocation | `0.05 ≤ q_g ≤ 0.35` |
| Policy/reward/PPO modification | None | None in the matched implementation | None |

## 5. Experimental Protocol

### 5.1 Matched controls

All methods used the same heterogeneous-UAV environment, role-graph policy, centralized critic, reward, action mask, communication interface, condition support, PPO hyperparameters, rollout layout, and training budget. The **only** experimental difference between UTR and DRTP was reset-condition allocation. EGTR and GA-EGTR were development candidates and are not combined with the confirmatory Original DRTP evidence.

### 5.2 Training and endpoint evaluation

Each trajectory used four parallel environments, 64 rollout steps, and 39,063 updates, totaling 10,000,128 environment steps. Two independent training cohorts were frozen in advance: A (`78011–78015`) and B (`78021–78025`). Each final checkpoint was evaluated on a fixed tape inaccessible during training. Cohorts are reported separately; any pooled ten-seed statistic is descriptive only.

### 5.3 Metrics and reporting

The primary endpoint is perturbed return. We also report median, worst seed, sample SD, nominal return, success, timeout, and collision from the frozen aggregation artifacts. Collision and timeout are not merged into a synthetic safety score. Structural held-out and parameter-shift evaluations use frozen tapes. No seed is replaced, excluded, or selected post hoc.

## 6. Results

### 6.1 Repeated cohort-level gains over UTR

At the fixed endpoint, DRTP achieved a higher perturbed-return mean than UTR in both fresh cohorts (Table 2). In cohort A, the mean was 216.66 for DRTP and 177.02 for UTR; the worst-seed return was 191.49 and 79.75, respectively. In cohort B, the corresponding means were 210.34 and 187.18, and the worst-seed returns were 172.03 and 164.98. The primary result is therefore a repeated positive cohort-level contrast rather than all-seed dominance.

### Table 2. Main fixed-endpoint results (`n = 5` independently trained policies per row)

| Cohort | Method | Perturbed return, mean ± SD | Median | Worst seed | Mean collision | Mean timeout |
|---|---|---:|---:|---:|---:|---:|
| A | UTR | 177.02 ± 64.53 | 181.12 | 79.75 | 0.003 | 0.730 |
| A | Original DRTP | 216.66 ± 23.48 | 223.82 | 191.49 | 0.009 | 0.597 |
| B | UTR | 187.18 ± 21.66 | 181.42 | 164.98 | 0.000 | 0.711 |
| B | Original DRTP | 210.34 ± 30.54 | 218.78 | 172.03 | 0.000 | 0.602 |

### 6.2 Frozen held-out structural and parameter shifts

DRTP retained positive cohort-level mean differences under the pre-defined structural held-out protocol: +22.77 in cohort A and +11.96 in cohort B. Worst-seed differences were +32.48 and +20.03, respectively. Under the evaluated parameter shift, mean differences were +51.71 in A and +17.48 in B. These results support transfer within the frozen shifts tested here; they do not establish robustness to arbitrary real-world failures.

### Table 3. Frozen OOD contrasts (DRTP minus UTR)

| Cohort | Shift family | Mean return difference | Worst-seed difference | Claim boundary |
|---|---|---:|---:|---|
| A | Structural held-out | +22.77 | +32.48 | Transfer within the evaluated structural shift |
| B | Structural held-out | +11.96 | +20.03 | Transfer within the evaluated structural shift |
| A | Parameter shift | +51.71 | [import final artifact] | Transfer within the evaluated parameter shift |
| B | Parameter shift | +17.48 | [import final artifact] | Transfer within the evaluated parameter shift |

### 6.3 Competitive matched comparison with PLR-style replay

The PLR-style comparison does not identify a uniform winner. In cohort A, DRTP had a higher perturbed-return mean (216.66 versus 203.87), higher worst seed (191.49 versus 142.02), and lower timeout (0.597 versus 0.742) than PLR-style replay. In cohort B, PLR-style replay had a higher mean (220.03 versus 210.34), a higher worst seed (201.06 versus 172.03), and lower SD (13.98 versus 30.54), whereas DRTP retained lower timeout (0.602 versus 0.699). This matched comparison shows that generic priority-driven allocation is competitive and that its ordering relative to topology-semantic allocation is cohort-dependent.

### Table 4. Matched external comparison (`n = 5` independently trained policies per row)

| Cohort | Method | Perturbed return, mean ± SD | Median | Worst seed | Collision | Timeout |
|---|---|---:|---:|---:|---:|---:|
| A | UTR | 177.02 ± 64.53 | 181.12 | 79.75 | 0.003 | 0.730 |
| A | PLR-style | 203.87 ± 36.12 | 214.02 | 142.02 | 0.014 | 0.742 |
| A | Original DRTP | 216.66 ± 23.48 | 223.82 | 191.49 | 0.009 | 0.597 |
| B | UTR | 187.18 ± 21.66 | 181.42 | 164.98 | 0.000 | 0.711 |
| B | PLR-style | 220.03 ± 13.98 | 218.22 | 201.06 | 0.000 | 0.699 |
| B | Original DRTP | 210.34 ± 30.54 | 218.78 | 172.03 | 0.000 | 0.602 |

### 6.4 Cross-scale six-UAV evaluation

**[6UAV_RESULT_PLACEHOLDER]** Insert only the completed frozen 2-scout/2-relay/2-terminal UTR-versus-DRTP results, including five fresh training seeds, perturbed return, success, timeout, collision, and paired deltas. Do not use interim checkpoints or the stopped legacy run.

### 6.5 Computational overhead

**[RUNTIME_RESULT_PLACEHOLDER]** Report measured wall-clock time per one million environment steps, peak GPU memory, sampler-update time, and policy parameter counts on matched hardware. Unchanged policy parameters alone are not a runtime measurement.

## 7. Discussion

The central implication of the results is not that one adaptive sampler must beat all alternatives. Rather, when a topology-failure support carries role and information-path semantics, training exposure can be allocated in a way that preserves those semantics and remains auditable. DRTP makes this allocation explicit: it fixes nominal exposure, evaluates failures against a nominal reference, samples frozen members uniformly within a selected group, and constrains group probabilities.

The two independent UTR comparisons are the strongest evidence. The positive mean contrasts recur in both cohorts, and the structural held-out contrasts remain positive under the evaluated shift family. The large improvement in cohort A’s lower tail indicates that exposure allocation can mitigate a severe downside in a trained-policy distribution. The more moderate cohort B effect reinforces why this evidence should be interpreted at the cohort level rather than through a single selected run.

The PLR-style outcome helps set the correct scope. It rules out an unqualified claim that DRTP uniformly dominates generic prioritized replay. It does not weaken the main matched UTR result: instead, it identifies an empirical design boundary between generic priority-driven allocation and topology-semantic constrained allocation. This is valuable for method selection because timeout, return, lower-tail behavior, and dispersion need not rank methods identically across cohorts.

## 8. Limitations

The study is simulation based and evaluates a finite, pre-defined topology-failure support. It does not establish real-flight performance, all-seed superiority, or monotonic improvement in every safety metric. The parameter and structural held-out results are bounded by their frozen shift protocols. Cross-scale transfer must be assessed only after the six-UAV formal block is complete. Finally, DRTP reallocates the exposure of existing failures rather than generating new failures or learning a new communication protocol.

## 9. Conclusion

DRTP is a constrained reset-side training-exposure allocator for heterogeneous UAV cooperation under topology failures. It preserves the policy learner and environment interfaces while using nominal-referenced group deficits to reallocate exposure over a frozen failure support. In two independent fresh cohorts, DRTP showed repeated cohort-level perturbed-return gains over matched UTR, and frozen held-out evaluations retained positive cohort-level contrasts under the tested shifts. The matched PLR-style comparison was competitive and cohort-dependent, which bounds rather than invalidates the contribution. The completed six-UAV protocol will determine whether a cross-scale claim is warranted.

## References to verify and complete before submission

1. Tung, T., et al. Effective communications: A joint learning and communication framework for multi-agent reinforcement learning over noisy channels. *IEEE Journal on Selected Areas in Communications*, 39(8), 2590–2603, 2021. https://doi.org/10.1109/JSAC.2021.3087248
2. Chen, X., et al. Distributed reinforcement learning for flexible and efficient UAV swarm control. *IEEE Transactions on Cognitive Communications and Networking*, 7(3), 955–969, 2021. https://doi.org/10.1109/TCCN.2021.3063170
3. Narvekar, S., Peng, B., Leonetti, M., Sinapov, J., Taylor, M. E., & Stone, P. Curriculum learning for reinforcement learning domains: A framework and survey. *Journal of Machine Learning Research*, 21(181), 1–50, 2020.
4. Jiang, M., Grefenstette, E., & Rocktäschel, T. Prioritized Level Replay. *Proceedings of the 38th International Conference on Machine Learning*, 4940–4950, 2021.
5. Tobin, J., Fong, R., Ray, A., et al. Domain randomization for transferring deep neural networks from simulation to the real world. *IEEE/RSJ International Conference on Intelligent Robots and Systems*, 2017. https://doi.org/10.1109/IROS.2017.8202133
6. Yu, C., Velu, A., Vinitsky, E., et al. The surprising effectiveness of PPO in cooperative, multi-agent games. *NeurIPS Datasets and Benchmarks Track*, 2022. arXiv:2103.01955.
