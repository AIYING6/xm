# PAPER-Q2-P1 Ablation Decision

**Decision: `A0 — EXISTING_UTR_VS_DRTP_SUFFICIENT`**  
**Training:** none authorized or started.

UTR and DRTP already isolate the primary method question: whether adaptive topology-group weighting adds value beyond uniform exposure. The contract confirms identical:

- SG architecture and 116,728 parameters;
- PPO, critic, reward, environment, failure semantics and actor boundary;
- seven topology groups and 50% nominal anchor;
- training budget, seed policy, final checkpoint and evaluation aggregation.

The only intended difference is fixed uniform `q_k=1/6` versus bounded adaptive `q`. This is the mandatory causal ablation and is already represented by the historical paired evidence. It must appear in the main paper, not only in supplementary material. The full seed-level record, including weak and reversed seeds, must be retained; the paper must not claim universal benefit or seed-stable superiority.

Fixed non-uniform weighting and nominal-anchor removal are not required to answer the primary reviewer question and would reopen algorithm development. No ablation zoo is justified.
