# DRTP manuscript scientific audit

**Scope.** This audit reviews the submitted Chinese draft against the frozen A/B endpoint evidence, frozen OOD evaluation, and completed matched PLR-style comparison. It does not reinterpret development runs or create new performance claims.

## Overall judgment

The central contribution is scientifically defensible: **under the evaluated frozen topology-failure interface, reset-side topology-semantic exposure allocation produced repeated cohort-level perturbed-return gains over matched UTR at the fixed 10M endpoint.** The evidence is strengthened by separate fresh cohorts and by positive structural held-out deltas in both cohorts. The paper should be positioned as an algorithmic training-allocation study, not as a new communication architecture, a universal sampler, or a deployment paper.

## Claim audit

### Claim: DRTP improves robustness over matched UTR in the evaluated task.

**Evidence:** A/B are independent five-seed cohorts at the same fixed 10M endpoint. Perturbed-return means are 216.66 versus 177.02 in A and 210.34 versus 187.18 in B (DRTP versus UTR).

**Risk:** Calling this universal, statistically significant, or seed-wise dominance would exceed the evidence.

**Recommended revision:** Use “repeated cohort-level robustness gains over matched UTR under the evaluated frozen interface.” Report A and B separately in the main text.

### Claim: DRTP improves lower-tail reliability.

**Evidence:** The worst-seed perturbed return is higher for DRTP in A (191.49 versus 79.75) and B (172.03 versus 164.98); A also has substantially lower SD (23.48 versus 64.53).

**Risk:** B has higher DRTP SD than UTR (30.54 versus 21.66). A paper-wide “variance reduction” claim is unsupported.

**Recommended revision:** Describe lower-tail improvement as observed in both cohorts and seed dispersion as cohort-specific. Do not treat raw spread as the headline metric.

### Claim: DRTP transfers beyond the training condition mixture.

**Evidence:** Frozen structural held-out mean deltas are +22.77 (A) and +11.96 (B); parameter-shift mean deltas are +51.71 (A) and +17.48 (B).

**Risk:** “General real-world robustness,” “sim-to-real,” or arbitrary OOD generalization are unsupported.

**Recommended revision:** Limit wording to the evaluated frozen structural and parameter shifts.

### Claim: DRTP is superior to PLR.

**Evidence:** A favors DRTP on perturbed mean, lower tail and timeout. B favors PLR-style replay on perturbed mean, lower tail and dispersion, while DRTP has lower timeout.

**Risk:** A uniform DRTP-over-PLR statement would be contradicted by cohort B.

**Recommended revision:** Present PLR-style as a competitive external comparator. The scientific distinction is mechanism-level: topology semantics, a fixed nominal anchor, and bounded group allocation; empirical ordering is cohort-dependent.

### Claim: DRTP improves safety.

**Evidence:** Timeout is lower for DRTP than UTR in both A and B. Collision is slightly higher in A (0.009 versus 0.003) and equal in B (0.000).

**Risk:** A composite or uniform safety-improvement claim is unsupported.

**Recommended revision:** Report timeout and collision separately. State that DRTP reduced mean timeout in the completed A/B comparison; do not call this a universal safety gain.

### Claim: DRTP scales to larger teams.

**Evidence:** None yet; the 6-UAV formal experiment is pending.

**Risk:** Any cross-scale language in title, abstract, contribution list, Results, or Conclusion would be premature.

**Recommended revision:** Keep a clearly labelled 6-UAV placeholder and remove cross-scale wording from claims until the frozen result is available.

## Reviewer-risk register

| Risk | Status | Manuscript action |
|---|---|---|
| Algorithm appears to be generic curriculum learning | addressable | Explicit UTR/DRTP/PLR mechanism map and reset-only causal contrast. |
| External-comparator claim overreaches | addressed | Report A/B separately; state competitive, cohort-dependent ordering. |
| Seed variation is hidden | addressable | Show paired seed figures and full per-seed supplement; do not pool A/B for inference. |
| Simulation setting is overgeneralized | addressable | Limit every implication to the evaluated interface; no deployment claim. |
| Method is not reproducible | addressable | Specify support set, nominal anchor, EMA, warm-up, update interval, simplex bounds, seeds and endpoint. |
| No component ablation | material but not fatal | Explain DRTP as a compact constrained allocation rule; add a labelled future ablation plan only if no frozen ablation exists. Do not fabricate one. |
| Six-UAV evidence incomplete | pending | Keep it out of title/abstract/conclusion until completed. |
| Runtime overhead unmeasured | pending | Table 5 remains a measured-runtime placeholder; do not infer cost from unchanged parameters. |

## Required edits before submission

1. Replace the initial three-reference anchor list with a verified bibliography and in-text citations.
2. Add the UTR–DRTP–PLR comparison table, an environment/protocol table, and explicit “only difference: reset condition allocation” language.
3. Use a standalone Limitations section rather than distributing limitations as self-criticism across Results.
4. Fill the 6-UAV and runtime blocks only from their frozen aggregation artifacts.
5. Add all per-seed values, condition-wise OOD values, manifests, and exact launch commands to the supplement.
