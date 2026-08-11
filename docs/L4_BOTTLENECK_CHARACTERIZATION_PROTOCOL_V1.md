# L4 bottleneck characterization protocol v1

**Status:** `L4_BOTTLENECK_CHARACTERIZATION_COMPLETE__NO_COMMUNICATION_SPECIFIC_METHOD_PROBLEM_IDENTIFIED`

Relay failure is permanently excluded from publication claims:
`RELAY_FAILURE_LINE_CLOSED__L5_DROPPED_FROM_PUBLICATION_CLAIMS`.

This read-only diagnostic uses only the two frozen L4 corrected-contract
checkpoints (`8901`, `8902`) and the same 32 paired development episode seeds.
It neither trains nor selects checkpoints. Each model/episode pair is evaluated
under five predeclared communication conditions: frozen L4, no delay, no packet
dropout, full range, and ideal communication.

For each episode it records target-evidence arrival, attack-geometry entry and
dwell, commit hold, terminal outcome, and cache age. The goal is to identify
which legal communication restriction the existing L4 policy is most sensitive
to. Results are sensitivity diagnostics only; they are not a training-time
causal comparison and cannot be used to choose a method without separate
authorization.

## Outcome

Across both frozen checkpoints, removing delay, removing dropout, or restoring
range did not materially improve neutralization relative to frozen L4 (mostly
`25.0%` on the 32 paired episodes). Ideal communication advanced mean first
Attacker target evidence from about step 35 to step 20, yet still did not
increase neutralization. This is a checkpoint sensitivity result, not a claim
that communication is unimportant during training. It does show that no single
range/loss/delay sensitivity is sufficiently isolated to justify a new
communication-specific method at this point. No new method or training follows
from this diagnostic without a separate decision.
