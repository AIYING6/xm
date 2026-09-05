# DRTP Stabilization final freeze

**Status:** `V1_STRONG_FREEZE_CANDIDATE`
**Final method:** Global-Anchored EGTR-SG-MAPPO, `alpha = 0.75`.

The frozen sampler applies the existing EGTR evidence, bounded-simplex and
local L1 trust-region path, then uses

`q_final = 0.25 q_UTR + 0.75 q_EGTR`.

Because the pre-anchor EGTR path has `||q_EGTR,t+1 - q_EGTR,t||_1 <= 0.10`,
the final path has `||q_final,t+1 - q_final,t||_1 <= 0.075`. No additional
temporal smoother, adaptive alpha, exposure budget, new gate or PPO change is
permitted.

The complete machine-readable contract is
`configs/drtp_stabilization_final_freeze.json`. It freezes the architecture,
PPO configuration, environment, reward, failure semantics, 10M budget,
endpoint-only rule and a new five-seed confirmatory cohort. The final method
is implemented by the Global-Anchored sampler introduced in commit
`e115e2b5`; confirmation infrastructure records its own source provenance at
preflight time.

Development used only seeds `76011--76013` and tape identifiers
`760000--760099`; neither may enter confirmation. The frozen development
evidence extract is at
`configs/drtp_stabilization_final_development_evidence.json`. It records the
completed endpoint findings but is not an input to training or evaluation.

The confirmatory comparison is UTR, Original DRTP, EGTR and the frozen final
method across seeds `78011--78015`, each from scratch for 39,063 updates
(10,000,128 environment steps). Results are reported as
`CONFIRMATION_STRONG`, `CONFIRMATION_MIXED_BUT_PUBLISHABLE`, or
`CONFIRMATION_WEAK`; no result triggers an automatic algorithm change.
