# Dynamic Robust Topology Prioritization for Fault-Resilient Heterogeneous UAV Coordination

## Abstract

Communication and sensing disruptions can change the effective interaction topology of a heterogeneous UAV team during a mission. A common training practice is to expose a multi-agent policy uniformly to a fixed collection of such conditions. This uniform allocation does not distinguish conditions that remain difficult as learning progresses from those already solved. We introduce **Dynamic Robust Topology Prioritization (DRTP)**, a reset-side training sampler that reallocates exposure across a frozen taxonomy of topology-failure conditions. DRTP uses only completed-episode returns to estimate a nominal-referenced difficulty signal and updates a bounded distribution over non-nominal failure groups. It leaves the environment support, observations, rewards, actor--critic architecture, action interface and PPO objective unchanged. We evaluate matched UTR and DRTP policies at a fixed 10M-step endpoint using two independent five-seed cohorts, with the training seed as the independent unit. Across the completed cohorts, DRTP produced higher mean perturbed return than UTR (A: 216.66 versus 177.02; B: 210.34 versus 187.18), while the worst seed was also higher in both cohorts (A: 191.49 versus 79.75; B: 172.03 versus [UTR placeholder]). Under frozen held-out structural shifts, the cohort-level DRTP--UTR mean deltas were +22.77 and +11.96. We additionally report a matched PLR-style external comparison and a frozen six-UAV cross-scale study **[PLR_RESULT_PLACEHOLDER; 6UAV_RESULT_PLACEHOLDER]**. The evidence supports a bounded claim: topology-aware reset allocation can improve cohort-level robustness within the evaluated fault interface; it does not establish universal per-seed dominance or deployment readiness.

## 1. Introduction

Heterogeneous UAV teams coordinate under asymmetric sensing, communication and task responsibilities. In this setting, a node or link disruption is not merely a local perturbation: it alters the information path through which distinct roles coordinate. Robust decision policies must therefore operate under a family of topology conditions rather than one nominal communication graph.

Multi-agent reinforcement learning provides a natural route to learn such coordination policies, but its outcome is determined jointly by the policy update rule and by the distribution of training episodes. Uniform sampling over a finite set of fault conditions is a clear matched baseline, yet it spends the same exposure on conditions with very different current learning status. Generic replay-prioritization methods motivate adapting a training distribution according to learning signal, but they do not by themselves specify how topology failures should be structured, anchored to nominal operation, or constrained within an interpretable UAV fault interface [Jiang et al., 2021].

This paper asks a focused question: **can a policy become more robust to a frozen family of topology failures when training exposure is reallocated according to group-level, nominal-referenced difficulty, while all policy-side and environment-side mechanisms are held fixed?** We answer it using Dynamic Robust Topology Prioritization (DRTP). Rather than adding a new policy input, auxiliary reward or PPO term, DRTP is a sampler outside the policy. At reset, it selects one of the already-defined topology conditions. Half of resets remain nominal; the remaining probability mass is distributed across six non-nominal failure groups. The group distribution is updated from completed episode returns, clipped to an interpretable bounded simplex, and persisted in the runtime state.

The design deliberately separates a training-distribution intervention from a policy-architecture intervention. UTR and DRTP therefore share the same heterogeneous role graph policy, critic, observations, rewards, masks, actions, update budget and fixed endpoint evaluation. This makes the causal contrast narrow: the difference is how often the already-valid topology conditions are encountered during training.

Our evidence is organized around replication rather than a single favorable run. The primary results use two independently trained, fresh five-seed cohorts at a fixed 10M-step endpoint; results are analyzed separately by cohort. A frozen structural and parameter-shift evaluation tests transfer beyond the training condition mixture. The final paper will add a matched PLR-style comparator and a cross-scale six-UAV experiment after their pre-registered runs finish. We make no claim that every seed or every safety metric improves.

Our contributions are:

1. A topology-semantic reset sampler that performs bounded, nominal-referenced allocation across a frozen UAV failure taxonomy without modifying PPO, the policy interface, rewards or transitions.
2. A matched evaluation protocol based on fixed 10M endpoints, fresh A/B cohorts, seed-level independence and evaluation tapes inaccessible during training.
3. Cohort-level robustness and held-out evidence for Original DRTP versus UTR, together with an external-prioritization and cross-scale evidence plan whose final results are reported without pooling the primary cohorts.

## 2. Related Work

### Multi-agent learning under communication imperfections

Communication reliability is a central concern in decentralized multi-agent control. Existing work has studied joint communication and policy learning under noisy channels and distributed learning frameworks for UAV swarm control [Zhang et al., 2021; Chen et al., 2021]. DRTP is complementary: it neither learns a communication protocol nor changes a message encoder. Its intervention operates at training reset selection over a specified topology-failure interface.

### Adaptive training distributions and prioritized replay

Prioritized Level Replay samples environments according to estimated learning potential rather than uniformly sampling a fixed set of levels [Jiang et al., 2021]. DRTP shares the high-level premise that training exposure can be adaptive, but differs in the object being prioritized. Its allocation is over an explicit hierarchy of UAV topology-failure groups, has a fixed nominal mass, uses group-level nominal-referenced difficulty, and enforces per-group bounds. The matched PLR-style study is included specifically to test whether these topology-aware constraints provide value beyond generic priority-driven allocation **[PLR_RESULT_PLACEHOLDER]**.

### Robust UAV coordination

UAV coordination work has explored distributed control, swarm decision-making and communication-aware control. Our scope is narrower than real-world deployment: the contribution is a simulation-based learning mechanism for a defined family of intermittent topology disruptions. The six-UAV study evaluates transfer to a larger team under a frozen cross-scale protocol rather than asserting unrestricted scalability **[6UAV_RESULT_PLACEHOLDER]**.

## 3. Problem Formulation

Consider a heterogeneous team of UAV agents with role-dependent observations and a communication graph. At each reset, the environment instantiates one condition \(c\) from a frozen set \(\mathcal C\). The condition set contains a nominal group \(N\) and six non-nominal topology-failure groups \(\mathcal F=\{F0,TE,TL,DS,DL,CP\}\). Each non-nominal group contains a finite set of fixed failure onset and duration combinations. The transition, reward and action interfaces are invariant across UTR and DRTP.

Let \(\pi_\theta\) denote the shared training policy and \(J_c(\pi_\theta)\) the completed episode return under condition \(c\). UTR fixes the reset distribution to a nominal mass of 0.50 and a uniform conditional distribution over \(\mathcal F\). The objective of the policy learner is unchanged between methods; the only intervention is the distribution from which reset condition \(c\) is selected.

## 4. Dynamic Robust Topology Prioritization

DRTP maintains \(q_t\in\Delta^{|\mathcal F|}\), the conditional distribution over non-nominal groups. At each reset, it samples \(N\) with probability 0.50 and otherwise samples a group from \(q_t\), then samples a member condition uniformly within that group. Initialization is UTR: \(q_0(g)=1/6\).

Every 32 PPO updates after a 128-update warm-up, DRTP forms an EMA of completed returns for each group. Once all group estimates exist, it computes the clipped nominal-referenced deficit

\[
d_g=\min\left(2,\max\left(0,\frac{\bar J_N-\bar J_g}{\max(|\bar J_N|,10^{-8})}\right)\right).
\]

It then applies a centered exponentiated update, smooths the candidate with the previous allocation, and projects it onto \(\{q:\sum_gq_g=1,\ 0.05\le q_g\le0.35\}\). These bounds guarantee that no group is removed and no group can dominate the non-nominal allocation. The update consumes only completed training-episode returns; it is not evaluated against the held-out endpoint tape.

### What DRTP does not change

DRTP adds no policy parameters. It does not modify agent observations, role embeddings, graph message passing, action masks, rewards, transitions, PPO clipping, critic targets or checkpoint selection. All of these are exactly matched to UTR. This boundary is important: any measured difference is attributable to reset-side exposure allocation within the frozen condition support.

## 5. Experimental Protocol

### Matched training and cohorts

Every main trajectory uses 4 parallel environments, 64 rollout steps and 39,063 updates, yielding 10,000,128 environment steps. UTR and DRTP share the same model configuration and 10M endpoint. Training has no early stopping, checkpoint promotion, seed replacement or online access to the fixed evaluation tape.

Two independent fresh cohorts, A and B, each contain five matched training seeds. The training seed is the independent unit. Primary results are reported separately for A and B; a pooled ten-seed result, if shown at all, is descriptive and never replaces a cohort-level conclusion.

### Outcomes and evaluation

The principal outcome is perturbed return over the frozen endpoint conditions. We report mean, median, worst seed, paired seed-wise deltas, nominal return, timeout and collision. Lower-tail outcomes are presented alongside the mean because robustness cannot be represented by a mean alone. Conversely, a broader raw range caused by a higher upper tail is not automatically treated as a negative finding; interpretation considers the full outcome profile.

### Held-out and comparator studies

Structural and parameter-shift tapes are frozen prior to evaluation. The PLR-style comparator uses a matched A/B protocol and has no permission to inspect final results during its training. The 6-UAV protocol uses fresh cross-scale seeds and the same UTR-versus-DRTP contrast. All reports will preserve the registered method identity and endpoint, regardless of whether a result is favorable.

## 6. Results

### 6.1 Repeated main-cohort robustness benefit

In cohort A, DRTP achieved a perturbed-return mean of 216.66 versus 177.02 for UTR; the DRTP worst seed was 191.49 versus 79.75 for UTR. In cohort B, DRTP achieved 210.34 versus 187.18 for UTR, with a DRTP worst seed of 172.03. Table 1 reports the remaining seed-wise and safety fields. The appropriate conclusion is cohort-level: both fresh cohorts show a positive mean DRTP--UTR contrast at the fixed endpoint. It is not a claim of all-seed dominance.

### 6.2 Held-out topology robustness

Under the frozen structural held-out protocol, the cohort-level DRTP--UTR mean return deltas were +22.77 in A and +11.96 in B; worst-seed deltas were +32.48 and +20.03, respectively. Parameter-shift mean deltas were +51.71 in A and +17.48 in B. Full condition-wise outcomes and timeout/collision fields are reported in Table 2 and the Supplementary Material.

### 6.3 External prioritization comparison

**[PLR_RESULT_PLACEHOLDER]** Insert only the completed A/B matched PLR-style outcomes, with the same metrics and no primary pooled analysis. The interpretation must answer whether topology-semantic, bounded nominal-anchored allocation offers evidence beyond generic priority-based replay.

### 6.4 Cross-scale transfer

**[6UAV_RESULT_PLACEHOLDER]** Insert the frozen six-UAV UTR-versus-DRTP result. The text should limit the claim to the evaluated larger-team protocol and should not generalize to arbitrary swarm sizes.

### 6.5 Computational overhead

**[RUNTIME_RESULT_PLACEHOLDER]** Report matched wall-clock ratio, parameter counts and memory measures using Table 5. Because DRTP is reset-side and has no actor/critic additions, policy parameters are unchanged; measured runtime is nevertheless required.

## 7. Reproducibility and Transparency

All maintained artifacts include configuration hashes, run manifests, sampler manifests, checkpoint hashes and evaluation manifests. The sampler runtime state persists \(q\), group EMAs, active windows and adaptation count. We release per-seed tables and the fixed condition definitions. Historical development cohorts are retained and labelled as historical/development evidence rather than merged into the confirmatory A/B analysis.

## 8. Limitations

DRTP is evaluated in a simulation benchmark with a specific heterogeneous-UAV interface and a finite taxonomy of topology failures. The results do not establish real-flight readiness, universal safety improvement, superiority on every seed, or effectiveness under every possible communication model. The mechanism reallocates the exposure of existing conditions rather than generating new failures. These limits delimit the contribution; they do not change the primary question tested by the matched A/B endpoint protocol.

## 9. Conclusion

DRTP provides an interpretable way to adapt training exposure to topology-failure groups while holding the policy learner and environment interfaces fixed. The completed fresh cohorts show repeated cohort-level robustness gains versus matched UTR, and the frozen held-out results support transfer within the tested structural and parameter shifts. Final PLR-style and six-UAV results will determine the permissible external-comparator and cross-scale claims. The central result remains bounded: adaptive, topology-semantic reset allocation can improve robustness in the evaluated heterogeneous UAV setting without altering PPO, rewards or the policy architecture.

## Reference anchors to complete in the bibliography

- Jiang, M., Grefenstette, E., and Rocktäschel, T. *Prioritized Level Replay*. ICML, 2021. Official record: https://proceedings.mlr.press/v139/jiang21b.html
- Zhang, et al. *Effective Communications: Joint Learning and Communication Framework for Multi-Agent Reinforcement Learning Over Noisy Channels*. IEEE JSAC, 2021. https://ieeexplore.ieee.org/document/9466501/
- Chen, et al. *Distributed Reinforcement Learning for Flexible and Efficient UAV Swarm Control*. IEEE TCCN, 2021. https://ieeexplore.ieee.org/document/9366781/

