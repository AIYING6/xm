# T3 — Final Decision

## Decision: D — NO_GO

T3 is complete under its zero-training, existing-assets-only contract. No final method dossier is generated.

## Why

1. The attacker-side future legal-information continuity label is reproducible, actor-legal as a prediction problem, and does not assume relay necessity.
2. Its future value is already highly predictable from current legal observation (leave-one-training-seed-out mean AUC **0.9248**).
3. History does not provide the required mechanism evidence: the best result is `L=4` at **0.9331** AUC, only **+0.0083**, while `L=16` and `L=32` are lower than the instantaneous baseline.
4. Legal graph history is not incrementally useful (`L=16` observation plus graph AUC **0.9187**).
5. Condition/time metadata alone carries substantial predictive structure (AUC **0.8581**), so a broad claim that a learned topology belief is uniquely responsible would be unsafe.
6. Existing work already covers recurrent communication, dynamic graphs, graph-recurrent UAV architectures, and training-time belief supervision. With no distinctive temporal/graph gap in T1, the remaining proposal would be generic SG plus recurrence plus auxiliary prediction.

## Preserved conclusions and prohibitions

- T2 remains M2, not M1; no causal upgrade is permitted.
- S2, the environment, reward, PPO, actor boundary, T1 checkpoints, and T2 comparator contract remain untouched.
- This is not a failure of the task or an invitation to tune a new memory module. It is an evidence-based rejection of this final-method direction.
- Do not implement, train, roll out, construct a new evaluation tape, use held-out/canonical seeds, or reopen DRTP/TCR based on T3.

## Safe next state

The algorithm-design branch is closed pending a **new independently grounded mechanism discovery**. The existing UTR-SG evidence may still support an application/robustness paper backbone, subject to a separate author decision and without claiming an unvalidated final algorithmic innovation.
