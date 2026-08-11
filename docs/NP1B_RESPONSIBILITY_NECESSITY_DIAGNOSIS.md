# NP1B responsibility-necessity diagnosis

Status: `NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR`

This is a read-only replay under the same NP1 calibration conditions.  No
algorithm, training, task physics, or transition timing was changed.

## Findings

Across seeds 9101--9104:

* Scout had legal target evidence before step 18 and none immediately after
  the sensing-loss transition.
* The delivered Scout status packet reported `detected_by=0` and zero target
  confidence.
* After the transition, the Attacker and Relay each retained legal target
  information for 13 post-loss steps through already-delivered/cache-valid
  evidence.
* The frozen-responsibility controller neutralized 4/4 episodes.
* The transparent reallocated controller also neutralized 4/4 episodes.

## Verdict

The capability transition is real, but the current task timing makes Scout's
continued sensing non-essential: the team already has enough lawful evidence
to complete the mission without changing responsibility.  This does not
justify CTRR design.  The next allowed action, if the project continues, is a
pre-registered task-geometry/timing calibration that makes nominal fixed
responsibility fail while a lawful alternative responsibility remains
feasible.  No training or method implementation is authorized before that
condition is established.

Artifacts:

* `results/np1_dynamic_capability_calibration/NP1B_RESPONSIBILITY_NECESSITY_REPORT.json`
* `results/np1_dynamic_capability_calibration/NP1B_RESPONSIBILITY_NECESSITY_MANIFEST.json`
* `scripts/run_np1b_responsibility_necessity_diagnosis.py`

