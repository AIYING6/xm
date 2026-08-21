# T6 Family D — Transition-Local Adaptation

## Proxy

For each failure-family episode, the analysis selects the first recorded binary support-quality transition. Adaptation latency is the first change of recorded attacker action in the following fixed 12-step window. Settling is whether the next fixed three actions after that change are equal. One first transition is retained per episode; no post-hoc threshold is selected.

## Result

| Group | Adaptation latency (lower better) | Settled fraction (higher better) |
|---|---:|---:|
| GOOD | 8.73 | 0.500 |
| WEAK | 2.00 | 0.815 |

Per seed `(latency, settled, transitions)`: 2201 `(2.00, 0.00, 900)`, 2202 `(10.03, 1.00, 900)`, 2203 `(1.00, 0.64, 900)`, 2204 `(7.43, 0.00, 900)`, and 2205 `(3.00, 0.99, 900)`.

The frozen rule required GOOD to be both faster and more settled. It is worse on both aggregate quantities. Therefore **Family D FAIL**.

## Consequence

There is no support for a method claim centered on rapid transition reaction, transition settling, or action-lag regularization. A/C must not be mischaracterized as faster local adaptation.
