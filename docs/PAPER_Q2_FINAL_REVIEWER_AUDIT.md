# PAPER-Q2 Final Reviewer Audit

## Reviewer 1 — novelty and positioning

**Major concern:** adaptive weighting can look like a standard reweighting heuristic, and there is no external drop-in baseline.
**Evidence-based resolution:** frame the contribution as a bounded problem–method–reliability package: relay-node-induced legal path reconfiguration, a capacity/exposure-matched UTR-versus-DRTP ablation, and full seed-level reliability reporting. The external comparator audit documents why TAPE and M3DDPG are not fair frozen-contract drop-ins.
**Remaining limitation:** novelty is application/method-system integration, not a new robust-RL theorem.

## Reviewer 2 — experimental rigor and validity

**Major concern:** positive averages may conceal a bad seed or invalid failure exposure.
**Evidence-based resolution:** show all five paired seeds, including seed1902 and seed2002; report mean, median, spread, worst delta, safety, survival-to-onset, and risk-set trigger validity. Preserve the historical development NO-GO and held-out FAIL.
**Remaining limitation:** seed stability is not established.

## Reviewer 3 — UAV relevance and generality

**Major concern:** results are simulation-only and limited to three heterogeneous UAV roles.
**Evidence-based resolution:** make the information boundary, legal topology/path mechanism, failure semantics, and evaluation protocol explicit. Do not claim hardware validation, scalability, universal topology generalization, or deployment readiness.
**Remaining limitation:** 4/5-UAV, HIL, and real-flight evidence are absent.

## Cross-review synthesis

The manuscript is defensible only if its title, abstract, results, and conclusion consistently say “higher average/median robustness with explicit seed sensitivity,” retain the adverse seed and mixed safety outcomes, and identify UTR-versus-DRTP as the primary matched ablation. This audit does not authorize another algorithm or experiment.
