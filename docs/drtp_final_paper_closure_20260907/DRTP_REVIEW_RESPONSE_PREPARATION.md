# DRTP reviewer-response preparation

This is a pre-submission response bank. It must be updated only with verified final artifacts; it is not a license to add post-hoc analyses.

## 1. Why not use PLR directly?

**Reviewer concern:** DRTP may be a rebranding of prioritized replay.

**Answer:** DRTP and PLR-style replay both adapt training exposure, but they optimize different allocation objects. DRTP allocates among pre-defined topology-failure groups using a nominal-referenced return deficit, preserves a fixed nominal mass, and projects group probabilities to explicit lower and upper bounds. The matched PLR-style comparator uses generic priority-driven replay on the same support. The paper does not claim uniform DRTP-over-PLR superiority: cohort A favors DRTP on return, lower tail and timeout, whereas cohort B favors PLR-style replay on return and dispersion while DRTP has lower timeout.

**Evidence:** Table 4; UTR–DRTP–PLR mechanism map; matched A/B protocol.

**Possible revision:** Move the mechanism map to the main paper if reviewers view it as essential for novelty.

## 2. Is DRTP simply curriculum learning?

**Reviewer concern:** The method looks like a standard curriculum heuristic.

**Answer:** DRTP belongs to the broader family of adaptive training-distribution methods, but its contribution is narrower and domain-structured: allocation is defined over a frozen topology-failure hierarchy, compared against a fixed nominal anchor, and constrained to preserve both nominal exposure and minimum per-failure exposure. It does not change task difficulty by generating conditions, nor alter the policy learner.

**Evidence:** Method Sections 3–4; Algorithm 1; fixed support-set manifest.

**Possible revision:** Add an ablation only if a frozen, protocol-compliant result already exists; otherwise retain the bounded conceptual distinction.

## 3. Why modify only reset-side condition allocation?

**Reviewer concern:** Why not change architecture, rewards, or the PPO objective?

**Answer:** The reset-only design isolates training exposure as the causal variable. UTR and DRTP share the environment, network, critic, reward, action mask, PPO objective, budget and endpoint evaluation; only selection of an existing frozen reset condition differs. This makes the comparison auditable and avoids attributing a result to multiple simultaneous modifications.

**Evidence:** Experimental protocol table and run manifests.

**Possible revision:** Include a compact protocol-difference checklist in the appendix.

## 4. Why does seed variation remain?

**Reviewer concern:** A robust method should remove all seed sensitivity.

**Answer:** The paper does not make that claim. The unit of analysis is the independently trained policy, and the reported evidence is cohort-level: DRTP has higher perturbed-return means than UTR in both fresh cohorts, with improved worst seed in both. Dispersion is reported rather than hidden, including the cohort-specific pattern in B.

**Evidence:** Main results table, paired-seed figure, full per-seed supplement.

**Possible revision:** Add medians, minima, SD and paired deltas to every primary result table.

## 5. Why no real-UAV flight study?

**Reviewer concern:** Simulation may not predict deployment behavior.

**Answer:** This work studies a controlled MARL training-allocation question under an explicitly defined simulated topology-failure interface. It does not claim real-flight readiness. The frozen structural and parameter shifts test transfer within the benchmark, not sim-to-real deployment.

**Evidence:** Limitations section; frozen OOD protocol and manifests.

**Possible revision:** State the simulation boundary once in the abstract and once in Limitations, not repeatedly in Results.

## 6. Why only three UAVs in the completed main study?

**Reviewer concern:** The main task may be too small for swarm claims.

**Answer:** The completed main protocol is a heterogeneous 3-UAV causal testbed that makes role-specific information paths and topology failures directly controllable. Cross-scale generality is not claimed until the frozen 6-UAV UTR-versus-DRTP protocol completes.

**Evidence:** Problem formulation and pending 6-UAV protocol.

**Possible revision:** If 6-UAV results complete, report them as an independent final block, not as a replacement for the causal 3-UAV study.

## 7. How does the method scale computationally?

**Reviewer concern:** Adaptive sampling may add meaningful overhead.

**Answer:** DRTP has no additional actor or critic parameters and updates only a six-group distribution from completed-return windows. Parameter equality does not substitute for runtime evidence; the final paper will report measured wall-clock and memory results under a matched hardware protocol.

**Evidence:** Algorithm 1 and Table 5 placeholder.

**Possible revision:** Fill Table 5 from the final runtime benchmark; do not estimate it from code inspection.

## 8. Why should topology semantics matter?

**Reviewer concern:** A generic difficulty signal may be sufficient.

**Answer:** Topology failures encode role and information-path semantics, including onset, duration and failed-node identity. DRTP preserves these groups during allocation and maintains a nominal anchor and per-group floor. The matched PLR-style result establishes that generic prioritization is competitive, while the completed A/B protocol does not support an unconditional winner declaration.

**Evidence:** Failure-group specification, comparator table, A/B PLR report.

**Possible revision:** Use the mechanism-comparison figure to make the distinction visual.

## 9. What is the theoretical contribution?

**Reviewer concern:** Is there a convergence or optimality guarantee?

**Answer:** The contribution is an auditable constrained training-allocation procedure rather than a new convergence theorem. Its formal properties in this paper are operational: fixed nominal exposure, fixed frozen support, nonzero exposure for every failure group, and a capped probability for each group. The empirical contribution is evaluated under matched A/B endpoint protocols.

**Evidence:** Bounded-simplex definition and Algorithm 1.

**Possible revision:** Do not add theorem-like claims without a proof; state the four operational invariants clearly.

## 10. What are the principal limitations?

**Reviewer concern:** What does the evidence not establish?

**Answer:** The evaluation is simulation-based, uses a finite topology-failure support set, does not establish real-flight performance, does not show every seed or every safety metric improves, and cannot make a cross-scale claim until the 6-UAV study completes. These are the boundaries of the evidence, not contradictory to the core UTR comparison.

**Evidence:** Claim–evidence matrix, main A/B table, OOD table, PLR table and 6-UAV status.

**Possible revision:** Keep this concise in the Limitations section and move detailed seed-level evidence to the supplement.
