# Phase S2 Failure Semantics Freeze

Relay 1 fails at environment step 44 for 80 steps. This is a topology
perturbation, not an information blackout. Communication edges
`A[1,0]`, `A[0,1]`, `A[2,1]`, and `A[1,2]` are unavailable while the failure is
active. The direct `Scout→Attacker` edge `A[2,0]` remains governed by ordinary
range/LOS/dropout rules.

The failed Relay cannot sense, transmit, or receive during the active interval.
Existing cached information follows the frozen age/confidence and delivery
semantics. There is no artificial cache purge and no forced direct-link
disablement. After the interval, Relay behavior reactivates under ordinary
environment rules.

Episodes terminating before step 44 are reported as pre-failure terminal
episodes. They are not silently removed from the primary planned-pair
estimand; mechanism summaries condition on exposed episodes and report the
exposure rate separately.
