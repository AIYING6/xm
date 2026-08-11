# NP0C multi-candidate responsibility-decision redesign

Status: `NP0C_PASS__MULTI_CANDIDATE_RESPONSIBILITY_DECISION_CONSTRUCT_ESTABLISHED__READY_FOR_NP1`

NP0C is a no-training construct calibration.  It replaces the unique Relay
replacement with two post-transition sensing candidates: Relay and Attacker.
The frozen capability matrix gives both `S=1` after Scout sensing loss, while
their other responsibilities and geometry-dependent opportunity costs differ.

## Scenario audit

Three method-independent geometry scenarios were evaluated using only relative
positions, capability-status metadata, and kinematic speeds:

* G1 prefers Relay takeover;
* G2 prefers Attacker takeover;
* G3 prefers Relay takeover because the relay-support detour is cheaper.

Both candidates are feasible in every scenario, the preferred candidate varies,
and neither fixed candidate dominates the other.  Both takeovers have a real
geometric opportunity cost.  No scenario label or evaluator/global truth is an
actor input.

The no-loss nominal physical baseline remains the NP0B oracle result (4/4
neutralized on the frozen geometry); NP0C itself does not train or run a new
policy comparison.

## Verdict

The responsibility-decision construct now passes the NP0C gate.  The next
authorized stage is a new NP1 physical paired qualification of G1--G3, still
without CTRR and without RL training.  That NP1 must verify that both takeover
assignments are physically realizable and that the preferred choice is
observable from legal recipient information.

Artifacts:

* `results/np0c_multi_candidate_responsibility_redesign/NP0C_CONSTRUCT_REPORT.json`
* `results/np0c_multi_candidate_responsibility_redesign/NP0C_CONSTRUCT_MANIFEST.json`
* `scripts/run_np0c_multi_candidate_responsibility_redesign.py`

