# M0 — Candidate Comparison and Ranking

## Hard-gate disposition

| Family | Disposition | Reason |
|---|---|---|
| Adaptive scenario reweighting / adversarial curriculum | Reject | Duplicates DRTP-style moving distributions and violates the stability-first rule. |
| Gradient surgery | Reject | Duplicates the closed TCR/SPC family. |
| Exact deletion-local aggregation | Reject | EDR is frozen closed; no EDR-v2 is permitted. |
| Spectral/Lipschitz graph smoothing | Reject | M0 offline evidence directly reverses the simple “weak equals overly sensitive” premise. |
| Local graph adversarial augmentation | Reject | Too close to existing topology exposure, and a legal local adversary is not cleanly separable from simulator semantics. |
| Graph information bottleneck | Reject | Requires a new message/MI objective and overlaps the closed support-utilisation route. |

## Scored viable shortlist

Scores use the M0 weights: stability 5, topology relevance 5, literature 4, Q2 novelty 4, implementation risk 4, compute 3, clean ablation 3, UTR compatibility 4, and catastrophe risk −5. Actor legality is a hard pass/fail gate. Scores are comparative aids, not performance forecasts.

| Rank | Candidate | Stable | Topology | Literature | Q2 | Impl. | Compute | Ablation | UTR compat. | Cat. risk | Weighted score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **TC-SAM-UTR** | 4 | 4 | 5 | 4 | 4 | 3 | 5 | 5 | 1 | **122** |
| 2 | Fixed-schedule SWA/EMA UTR | 4 | 2 | 5 | 2 | 5 | 5 | 3 | 5 | 1 | 103 |
| 3 | Robust communication bottleneck | 3 | 4 | 5 | 3 | 2 | 2 | 3 | 3 | 3 | 79 |

### Rank 1 — TC-SAM-UTR

**Core:** apply an ordinary two-pass SAM update to the frozen PPO objective under the fixed 50% nominal plus conditional-uniform six-group UTR exposure. The architectural graph, policy input, critic, reward, and evaluation all remain unchanged.

**Why it is distinct from UTR:** UTR specifies *which* legal topology conditions are sampled. TC-SAM specifies *which parameter neighbourhood* must maintain a good PPO surrogate under that fixed mixture. It introduces neither new topology data nor an adaptive sampler.

**Reviewer response:**

- MARL: not an unqualified copy—its adaptation is a fixed-exposure topology-OOD policy-optimisation protocol and compares against an exactly matched UTR control.
- Graph: it does not assert graph smoothness; it seeks parameter-flat policies under legal graph reconfiguration.
- UAV: relay-node loss is operationally a changing, legally observed communication graph; flatter trained policies are tested on timing/duration/compound reconfiguration OOD conditions without any execution-time oracle.

### Rank 2 — fixed-schedule SWA/EMA UTR (documentation-only backup)

Mature and low cost, but Q2 novelty is too weak: an averaged policy would primarily be a training-stability baseline. It could not support the planned paper without a much larger gain and is explicitly **not authorised for training**.

### Rank 3 — robust graph information bottleneck (documentation-only backup)

Literature is strong (robust GNN-MARL), but its additional objective, message representation machinery, and unclear separation from prior support-utilisation routes make it too complex and too close to an already closed research direction. It is explicitly **not authorised for training**.

## Selection

`PRIMARY_FINAL_METHOD = TC-SAM-UTR`.

Only Rank 1 may proceed to a separately authorised design/implementation contract. If it later fails a proper paired five-seed development experiment, algorithm development ends; Rank 2 and Rank 3 must not be trained.
