# DRTP final external-comparator contract

**Status:** `CONTRACT_ONLY_NO_EXTERNAL_TRAINING`.

The designated external comparator is a faithful, independent PLR-style topology-condition replay implementation, based on Jiang et al. (ICML 2021). It is a sampling-level comparator, not a replacement actor or a retrospective ablation. The original repository is CC-BY-NC-4.0, so no upstream source will be copied.

| Fairness dimension | Frozen rule |
|---|---|
| Support | Same nominal + six topology-condition members |
| Environment / failures / reward / actor information | Identical to UTR and DRTP |
| PPO / model / budget | Identical; 10,000,128 environment steps per trajectory |
| Seeds / endpoint tapes / episodes | Fresh matched cohorts; same fixed endpoint tapes and counts |
| Tuning | One published-rule mapping; no outcome-driven sweep |
| Reporting | Parameter count and wall-clock cost alongside outcome metrics |

PLR can be reported only as an external adaptive task-sampling comparator. It does not establish that DRTP is a direct implementation of PLR or that either method solves universal robustness.
