# P3-B Halt Decision Memo (2026-08-08)

- status: **P3-B candidate design STOPPED after pre-calibration freeze.**
- decision: do NOT run P3-B calibration, formal evaluation, or protocol freeze
  for the current paper.
- P3-B infrastructure (env parameterized target policies, IC-MPC / full-state
  MPC feasibility oracles, C structural counterfactual metrics, frozen
  calibration rules, legacy-env regression tests) is committed at
  `p3b-ood-precalibration-freeze-v1.0` (`8f60f6a`) and retained for a future
  EA-RG v2 / a dedicated OOD-benchmark study. It is NOT used in the current
  manuscript.

## Why P3-B was started and then stopped

Started: the initial P3-A zero-shot OOD result was Gate C; a design audit was
undertaken to determine whether that Gate C was caused by a benchmark design
flaw rather than a genuine property of the method.

Audit outcomes (all PASS / strengthening P3-A validity):
1. No implementation error in G1/G2/M1/M2/C1/C2/J1 config plumbing or pruning.
2. A qualified full-state MPC oracle (hand-coded, no learning, no access to
   learned results) achieves kinematic feasibility on ALL SEVEN P3-A cells
   (aw=success=1.000), i.e. the saturation is NOT physical infeasibility.
3. An information-constrained MPC (IC-MPC: agents use only legal detection /
   cache / constant-velocity extrapolation, never true-state fallback) also
   passes nominal qualification and shows M1/M2 are achievable under legal
   information constraints.
4. C1/C2 topology pruning is real (p_affected≈0.45), non-trivial (Δp_path>0),
   retains alternate-path opportunity (p_alt≈0.49), and is comparator-neutral.
   The C1/C2 reversal is therefore a REAL weakness of EA-RG, not a bias.

Conclusion from the audit: P3-A is a valid zero-shot stress/transfer suite; its
Gate C reflects genuine distribution-dependent early-recovery generalization,
not a benchmark artifact. The learned-policy saturation on M1/M2/J1 reflects
limited transfer, not physical or information infeasibility.

## Why P3-B is not needed for the current paper

- The scientific question "does EA-RG generalize zero-shot to unseen shifts?"
  is already answered: Gate C (not enough evidence of a stable cross-shift
  early-recovery advantage).
- A calibrated moderate P3-B would only answer the narrower question "how much
  advantage remains at calibrated moderate difficulty", which:
  - does not contradict or overturn Gate C;
  - cannot remove the C1/C2 weakness;
  - would burden the paper with a large benchmark-design apparatus (oracle /
    IC-MPC / bands / structural gate / legacy cells), making the paper look
    like an OOD-benchmark study rather than an EA-RG method paper;
  - risks a "rescue experiment" impression even though the protocol is clean.
- The P3-A audit already resolves the reviewer's main doubt ("did bad OOD
  results come from a broken benchmark?") -> NO.

## Paper strategy after halt

- Keep Gate C.
- Downgrade the weight of OOD in the paper: OOD is reported as boundary /
  limitation evidence, not as a headline claim.
- Main story: EA-RG improves early post-failure recovery under the locked
  nominal held-out distribution.
- Boundary statement: additional zero-shot tests show the advantage is
  distribution-dependent, with partial preservation under geometry shifts and
  degradation under communication-topology and maneuver shifts.

## Frozen provenance (unchanged)

- p3a-ood-protocol-v1.1, p3a-ood-raw-results-lock-v1.0,
  p3a-ood-stats-lock-v1.0 (Gate C), paper-v1.6-p2.5-content-ready.
- p3b-ood-precalibration-freeze-v1.0 (P3-B infra, archived; not used in paper).
