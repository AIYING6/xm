# C2-M2 telemetry cost preflight contract

This is a technical benchmark, not a scientific experiment.

- One fixed seed (`4991`), two 128-update runs: telemetry off and telemetry on.
- Both runs use fixed-stratified UTR collection, ordinary PPO, disabled evaluation, and identical milestone/runtime checkpoint settings.
- The telemetry-on run enables only the default-off group-credit and failure-aware writers.
- Required equivalence: final actor checkpoint SHA256 and `train_log.csv` SHA256 must match exactly.
- Outputs: wall-clock seconds, directory bytes, telemetry bytes and integrity status only.
- Forbidden: evaluation tapes, best checkpoints, scientific seed claims, parameter tuning, algorithm changes and continuation.

`C2_M2_TELEMETRY_COST_PASS` permits only a separate human decision about a future diagnostic contract. It does not authorize diagnostic training.
