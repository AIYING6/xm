# Task-relevant reachability audit

The frozen nominal legal target-information graph contains `Scout→Relay, Relay→Attacker`. Its Scout→Attacker reachability is `True`, shortest legal path length is `2`, and the number of frozen primary paths is `1`.

A candidate that masks `Scout→Relay` or `Relay→Attacker` produces zero nominal legal primary paths. The other four physical one-way channels do not change this frozen primary reachability. Thus a simple policy-free severity based on primary-path loss is well-defined, but it has only two values here: `0` (no primary-path change) and `1` (complete cut). It cannot form a multi-level recoverable ladder.
