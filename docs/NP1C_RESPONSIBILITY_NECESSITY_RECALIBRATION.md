# NP1C responsibility-necessity task recalibration

Status: `NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR`

NP1C was the single authorized no-training calibration.  It changed only the
pre-registered task timing/geometry: Scout sensing loss at step 10, a target
initial position at 2 km, a 12-step cache TTL unchanged from NP1, a bounded
weaving target motion, and a Relay backup radar range of 17.5 km.  No actor
contract, cache rule, mission endpoint, reward, or algorithm was changed.

Results over seeds 9111--9114:

* Relay reacquired local sensing in the reallocated replay, so a lawful backup
  sensing path exists.
* No-loss nominal baseline: 2/4 neutralized.
* Loss + frozen responsibility: 2/4 neutralized.
* Loss + transparent reallocation: 2/4 neutralized.

The no-loss baseline is not uniformly successful and the reallocated replay
does not outperform frozen responsibility.  Therefore this one calibration
does not establish the required causal chain:

`nominal feasible -> fixed responsibility fails -> lawful reallocation recovers`.

Verdict remains `NP1_PARTIAL`; CTRR and training remain unauthorized.  A
future calibration would need a valid no-loss nominal task and a pre-registered
separation between fixed and reallocated responsibility.  If that cannot be
achieved without violating the NP1C kill conditions, close the Scout-sensing
transition line rather than continue tuning it.

Artifacts:

* `results/np1c_responsibility_necessity_recalibration/NP1C_RECALIBRATION_REPORT.json`
* `results/np1c_responsibility_necessity_recalibration/NP1C_RECALIBRATION_MANIFEST.json`
* `scripts/run_np1c_responsibility_necessity_recalibration.py`

