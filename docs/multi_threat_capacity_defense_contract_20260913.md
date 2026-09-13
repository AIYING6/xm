# Capacity-limited multi-threat defense: G0 contract

The task is deliberately a resource-allocation problem, not a reward-shaped
version of the previous dual-capability task.  Two red aircraft attack
different assets.  A blue attacker has exactly one kinetic engagement during
an episode; a blue scout can sustain a focused disruption beam for only one
threat.  An asset breach requires a red aircraft to complete a continuous
target lock.  Thus a safe episode requires one threat to be kinetically
neutralized and the other to be continuously contained through the deadline.

All blue decisions remain the inherited 27-action 3DOF primitive interface.
No route assignment, preferred target, attack authorization, or suppression
button is inserted into observations or actions.  The next gate is a
zero-training transparent-controller audit.  Failure at that gate means no
MAPPO training is permitted.
