# L5 relay-failure calibration report

## Verdict

`L5_CALIBRATION_BLOCKED__RELAY_NOT_ON_IDENTIFIABLE_INFORMATION_PATH`

No L5 learning run was launched.

## Calibration result

The L4 configuration was held fixed: communication-range scale `0.5`, packet
dropout `0.3`, and message delay 8. Eight method-independent scripted runs
were assessed for persistent Relay failure onsets 20, 40, 60, and 80.
Scripted neutralization remained 8/8 at every onset, with mean termination at
53.75 steps. Onsets 60 and 80 occur after the typical scripted completion and
are therefore invalid candidates. Onsets 20 and 40 activate failure before
completion, but the calibration found:

* instantaneous delivered communication links were already zero before and
  after failure under delayed-delivery semantics;
* no cache-valid Relay-sender packet record was observed for a non-Relay
  recipient, before or after failure;
* consequently, the failure did not remove a measured Relay information path
  in this L4 trajectory population.

## Scientific implication

Introducing a Relay failure now would label an event as a topological/role
failure without evidence that the Relay is functionally carrying information
in the frozen L4 setup. Any resulting performance difference would be
uninterpretable: it could not be attributed to loss of Relay-provided evidence.
This is a calibration/identifiability block, not a negative learning result.

## Next-decision boundary

Do not repair the failure onset, add a new algorithm, or run L5 training.
Continuation requires a separately authorized communication-path audit and,
if justified, a task-protocol change that makes Relay participation observable
and legal before testing Relay failure. That would be a new controlled task
development decision, not the next rung of the present fixed ladder.
