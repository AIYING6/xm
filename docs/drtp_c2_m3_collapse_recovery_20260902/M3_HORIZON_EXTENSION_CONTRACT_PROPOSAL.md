# M3 horizon-extension contract proposal

**Status:** `PROPOSAL_ONLY / NOT AUTHORIZED`.

The completed fixed-window analysis returned `HORIZON_INSUFFICIENT`: all six
pre-specified transitions reversed sign across the 125k--500k milestones.
This proposal is therefore the only permitted follow-up to the analysis; it
does not launch a continuation.

If separately authorized, the existing 20 C2-M3 trajectories would resume
their exact 500k runtime state to 1M, with no reinitialization, seed change,
new arm, parameter change, or telemetry change. Both existing arms and both
cohorts remain intact. New fixed milestones would be 625k, 750k, 875k and 1M.
The additional budget would be 20 x 0.5M = 10M environment steps.

At 1M, continued transition reversals, no repeated precursor, or a cohort
disagreement would produce `FAILURE_MODE_DISCOVERY_NO_GO` and permanently
close this mechanism-search line. No 3M or 10M extension is permitted by this
proposal.
