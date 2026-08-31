# SR-DRTP P1-A branch-isolation audit

P1-A is a CPU-only technical gate. It must return exactly one of
`P1_BRANCH_ISOLATION_PASS` or `P1_BRANCH_ISOLATION_FAIL`; it is not an
experiment on candidate P1 seeds and cannot establish a risk signal.

The gate verifies that A is an exact Original-DRTP continuation, B changes
only the sampler distribution through the frozen 20% uniform convex anchor,
and C restores only actor parameters and their Adam slots after its next PPO
step while retaining the critic step. PP disagreement remains a training-only
observation and does not feed any control decision in P1-A.

Only after a recorded PASS and a separate human execution authorization may a
future P1 matched-shadow launcher be prepared. A PASS never authorizes
SR-DRTP, a selector, a long run, a parameter search, or any Mainline-A change.
