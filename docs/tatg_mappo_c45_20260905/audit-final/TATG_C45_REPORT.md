# TATG-MAPPO C4.5 first-update same-rollout audit

**Verdict:** `TATG_C45_FIRST_UPDATE_SAME_ROLLOUT_PASS`.

C4.5 collected one short, real fixed-UTR 3D rollout and replayed its complete chronological sequence once for CETM and each frozen capacity-matched control. Each variant took exactly one actor-only ordinary clipped-PPO step. This verifies update mechanics only; it is neither a training run nor a policy-performance comparison.

The CETM candidate's stored pre-update action log-probabilities replayed exactly. All three variants had finite actor loss and gradients, and each changed an active temporal policy-head parameter. The candidate critic took no optimizer step and remained bitwise unchanged. The copied inactive legacy policy head was excluded from each optimizer and was bitwise unchanged. Candidate post-update sequence log-probabilities remained finite.

The rollout is a fixed audit trace. Control old log-probabilities are recomputed from each control's own legal pre-update replay; this is therefore not an on-policy efficacy claim for any control. The audit used 6 environment steps, three isolated audit actor optimizer steps (one per variant), zero formal PPO updates, and zero evaluation episodes.

A pass authorizes only a separately preregistered fresh-seed pilot contract. It does not authorize cloud training, evaluation, a return claim, checkpoint selection, or automatic continuation.
