# NP1 multi-candidate responsibility physical qualification

Status: `NP1_PARTIAL__MULTI_CANDIDATE_CONSTRUCT_VALID_BUT_PHYSICAL_ORDERING_UNSTABLE`

This no-training qualification evaluated the frozen G1/G2/G3 scenarios under
R0 (no loss), R1 (Relay takeover), and R2 (Attacker takeover), using the same
3DOF dynamics, sensing, communication/cache semantics, and automatic physical
neutralization endpoint.

## Results

* The no-loss R0 baseline was stable in all three scenarios (4/4 seeds each).
* Both takeover assignments were physically executable in the tested scenes.
* The observed physical preferred ordering was `G1: R2, G2: R1, G3: R1`,
  whereas the pre-registered NP0C ordering was `G1: R1, G2: R2, G3: R1`.
* Therefore the multi-candidate construct survives physically, but the
  abstract cost ordering did not transfer unchanged to 3DOF execution.

## Verdict

`NP1_PARTIAL__MULTI_CANDIDATE_CONSTRUCT_VALID_BUT_PHYSICAL_ORDERING_UNSTABLE`

This is not a basis for CTRR or RL training.  The task has two legal takeover
options and a stable nominal baseline, but the intended scenario ordering must
be treated as unconfirmed.  Any continuation would require one explicitly
pre-registered physical cost definition and a fresh qualification; no
post-hoc reassignment of which role is “better” is allowed.

Artifacts:

* `results/np1_multi_candidate_responsibility_physical_qualification/NP1_PHYSICAL_QUALIFICATION_REPORT.json`
* `results/np1_multi_candidate_responsibility_physical_qualification/NP1_PHYSICAL_QUALIFICATION_MANIFEST.json`
* `scripts/run_np1_multi_candidate_responsibility_physical_qualification.py`

