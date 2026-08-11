# NP1 responsibility-reallocation task qualification

Status: `NP1_PARTIAL__REALLOCATION_VALID_BUT_DECISION_COMPLEXITY_INSUFFICIENT`

This no-training protocol evaluates the NP0B capability-overlap construct with
paired conditions on the same frozen physical task:

* **A:** no loss + nominal assignment `R0`;
* **B:** Scout loss + frozen `R0`;
* **C:** Scout loss + alternative assignment `R1`.

Results over seeds 9131--9134:

* A: 4/4 neutralized;
* B: 3/4 neutralized;
* C: 4/4 neutralized;
* C showed Scout evidence loss, Relay local sensing, and subsequent legal
  evidence restoration in all four runs.

The physical responsibility chain is therefore visible: B has a failure case,
while C restores the task.  However, the post-transition capability matrix has
exactly one agent with sensing capability (`Relay`), so a capability-only rule
`if Scout.S becomes 0, assign S to Relay` uniquely determines the alternative.
The current task does not yet require a nontrivial state-dependent assignment
decision.

## Verdict

`NP1_PARTIAL__REALLOCATION_VALID_BUT_DECISION_COMPLEXITY_INSUFFICIENT`

The task is suitable for studying capability-conditioned switching, but not
yet for claiming a general dynamic responsibility-allocation algorithm.  CTRR
and RL training remain unauthorized.  To proceed, the task would need multiple
feasible substitute agents or competing responsibilities so that geometry and
local state determine which assignment is best; otherwise the correct outcome
is to stop at a rule-based baseline rather than invent an RL method.

Artifacts:

* `results/np1_responsibility_reallocation_task_qualification/NP1_QUALIFICATION_REPORT.json`
* `results/np1_responsibility_reallocation_task_qualification/NP1_QUALIFICATION_MANIFEST.json`
* `scripts/run_np1_responsibility_reallocation_task_qualification.py`

