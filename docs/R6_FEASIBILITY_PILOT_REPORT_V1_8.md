# R6 feasibility pilot report v1.8

## Scope

Single-seed, short engineering pilots were run after the R4 boundary repair and
R5 leakage gate. They are not full training, OOD, robustness, held-out, or
statistical experiments.

| Pilot | Encoder | Result |
|---|---|---|
| corrected EA-RG | `multi_relation` | completed without crash/NaN; one short evaluation episode timed out |
| corrected wider single-graph | `single` | completed without crash/NaN; one short evaluation episode timed out |
| matched-information non-graph | `matched_nongraph` | completed without crash/NaN; one short evaluation episode timed out |

The pilots used one environment, two updates, eight rollout steps, hidden width
32, strict bottleneck, dropout 0.3, one-step delay, and a failed-agent window.
The short budget did not produce a stable attack/success event, so no RMST or
success comparison is reported.

## Gate outcome

R5 passed 14/14 actor-boundary tests. R6 found no implementation crash, tensor-
shape failure, optimizer instability, or packet-boundary violation in the three
corrected paths. The logs report `eval_intent_acc=nan` because the optional
intent auxiliary head is disabled; this is not a training NaN. It did not
establish parity of learning curves or superiority. The event absence is a
feasibility limitation, not a reason to tune the protocol post hoc.

## Stop condition and next authorization

R6 is complete. Do not enter Stage 5, rewrite the paper, or treat these pilot
artifacts as formal evidence. Before any scientific comparison, freeze the
training/evaluation matrix, rerun the full corrected baselines under matched
information, and keep all v1.6 results labelled as legacy implemented-policy
evidence.
