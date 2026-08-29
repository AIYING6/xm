# S0 delta and evaluation-margin freeze

Status: `S0_NUMERICAL_FREEZE_COMPLETE`

## Label-free sampler rule

- Valid post-projection movement samples: `12781`.
- `delta_q_l1 = pooled P90 = 0.0251330003814`.
- P50/P75/P95/max: `0.00976856534681` / `0.0165324374431` / `0.0326631618815` / `0.215587033258`.
- Inclusion uses only original-DRTP sampler provenance; no good/bad, formal/independent outcome label is read by the selection rule.

## Endpoint variation rule

- Primary robust endpoint: `J_pert_mean = mean(J_f0, J_timing, J_duration, J_compound)`.
- Same-checkpoint cross-tape paired differences: `100` from `10` checkpoints.
- `epsilon_J = P90(|J_tape_a - J_tape_b|) = 7.87491983792`.
- This bounds observed tape variation; it does not erase or pool training-cohort differences.

## Frozen practical margins

- Practical downside-improvement margin: `7.87491983792` J units (strictly greater than this margin at the relevant gate).
- S2 uniform anchor: `0.20`; adaptive mass: `0.80`.

## Offline movement replay

- Recorded original movements above the P90 cap: `10.00%` by construction.
- Forced-target TR replay activation: `15.98%`; prior clipping can make later recorded targets farther from the candidate state.
- The replay is a deterministic movement audit on recorded targets only; it does not simulate counterfactual policy learning or claim repair.

## Inputs and reproducibility


- Audit script SHA256: `5060da588cd707c04f22d454b1505b6b1cc12b0199bfcda5c4231297f26b461b`.
- Full source/member hashes and exclusion status: `s0_sampler_source_inventory.csv`.
- Movement rows: `s0_q_update_movements.csv`; same-checkpoint tape cells: `s0_evaluation_tape_cells.csv`.

No training, evaluator rerun, parameter sweep, or algorithm-selection result was executed in S0.
