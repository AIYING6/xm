# NP1 dynamic-capability task identifiability calibration

Status: `NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR`

Protocol: `NP1_DYNAMIC_CAPABILITY_TASK_IDENTIFIABILITY_CALIBRATION_V1`

## Scope

This is a no-training, adapter-level calibration for the new project defined
in the NP0 charter.  It uses a new `DynamicCapabilityAdapter` and does not
modify the legacy environment or reuse any old performance result as evidence.
The only capability transition is an in-episode loss of Scout sensing at step
18.  The learning action is guidance only; attacker neutralization commit is
automatic in this calibration adapter.

## Results

The deterministic calibration used seeds 9101--9104, horizon 120, and a
12-step cache-validity threshold.

* Before the transition, Scout had lawful target evidence in all four runs.
* After the transition, Scout target observation/cache was removed in all four
  runs (`scout_has_target=false`).
* A delivered Scout sender-status packet reached Relay in all four runs and
  reported `detected_by=0` with zero target confidence after the loss.
* The transition therefore changes an actual legal information source; it is
  not merely a capability flag.
* A deterministic expiry probe confirms that a stored Relay cache is not
  considered fresh after the 12-step age limit, rather than being silently
  refreshed from global target truth.
* A transparent reallocated controller neutralized in 4/4 runs, but the
  frozen nominal controller also neutralized in 4/4 runs.

## Verdict

`NP1_PARTIAL__CAPABILITY_TRANSITION_VALID_BUT_REALLOCATION_NECESSITY_UNCLEAR`

The physical/legal capability transition is identified, but the current
calibration does not establish that nominal responsibility becomes infeasible
while an alternative responsibility allocation is needed.  This is a hard
stop for CTRR design: no algorithm, training, or additional failure timing is
authorized from this result.  A future NP1 revision would need a pre-registered
task geometry where Scout's continuing sensing is necessary for nominal control
and a lawful alternative role can compensate after the transition.

Artifacts:

* `results/np1_dynamic_capability_calibration/NP1_CALIBRATION_REPORT.json`
* `results/np1_dynamic_capability_calibration/NP1_CALIBRATION_MANIFEST.json`
* `scripts/run_np1_dynamic_capability_calibration.py`
