# DRTP reliability evidence synthesis

## Decision

The evidence does not support another unconditional DRTP/EGTR training variant. It supports preserving EGTR as an **upside candidate** while making UTR the **default deployable baseline**. The proposed method is **Paired-Validation Fallback EGTR (PVF-EGTR)**.

PVF-EGTR trains one matched UTR checkpoint and one matched frozen EGTR checkpoint. It promotes EGTR only when two independent, preregistered selector tapes both demonstrate a practically meaningful paired benefit without nominal, worst-group, collision, timeout, or constraint failure. Every other outcome deterministically deploys UTR.

## What the completed experiments establish

1. Original DRTP has real upside but not repeatable reliability. The formal 2301–2305 cohort produced a mean paired gain of `+54.999` over UTR with `5/5` positive seeds; the independent 2401–2405 cohort reversed to `-35.370` with only `2/5` positive seeds.
2. Local restrictions and online rescue signals did not generalize. Trust-region anchoring, KLR, PP, CV, ensemble, group-weighted PPO, and selective intervention either reversed across cohorts or failed their own frozen reliability gates.
3. Rich telemetry did not reveal a repeated precursor. SR-DRTP, C2/M3, and the EGTR outcome decomposition found no training-only signal that consistently distinguished helpful from harmful interventions across both cohorts.
4. EGTR nevertheless contains a repeatable structural improvement. In the fresh 10M experiment, EGTR improved Original DRTP in all ten matched seeds. The improvement was `+51.302` on average in Cohort A and `+77.070` in Cohort B.
5. EGTR is not an unconditional UTR replacement. Its paired gain over UTR was positive for `2/5` seeds in Cohort A and `4/5` in Cohort B; Cohort A mean was approximately `-0.386`, while Cohort B mean was `+33.570`.
6. The oracle policy `max(UTR, EGTR)` would have had a mean gain of approximately `+29.571`, median gain `+16.738`, minimum gain `0`, and positive gain on `6/10` seeds. This is only a non-deployable ceiling because it uses final outcomes, but it proves that a useful selection problem exists.

## Consequence

The unresolved problem is no longer “how should EGTR be tuned?” It is “can a clean, paired validation protocol identify when the already frozen EGTR checkpoint is worth deploying?” This formulation directly matches the observed data and does not depend on a nonexistent universal failure precursor.

## Literature grounding

- Deep-RL results require seed-level uncertainty and independent replication rather than treating episodes as independent evidence: Henderson et al., [Deep Reinforcement Learning That Matters](https://ojs.aaai.org/index.php/AAAI/article/view/11694).
- Baseline-constrained policy improvement motivates retaining a trusted baseline when evidence for a candidate is insufficient, although its tabular/off-policy guarantees do not transfer to this on-policy multi-agent setting: Laroche et al., [SPIBB](https://proceedings.mlr.press/v97/laroche19a.html); Sharma et al., [Decision-Point Guided Safe Policy Improvement](https://proceedings.mlr.press/v258/sharma25a.html).
- Safe improvement in factored multi-agent systems supports treating baseline preservation as a first-class design objective, but again does not provide a theorem for this implementation: Bianchi et al., [Scalable Safe Policy Improvement for Factored Multi-Agent MDPs](https://proceedings.mlr.press/v235/bianchi24b.html).

## Claim boundary

PVF-EGTR is currently a design, not a validated algorithm. Its fallback semantics bound *which checkpoint is deployed*; they do not mathematically guarantee that the selector cannot make a false promotion. That question must be answered prospectively with independent training seeds and tapes.

