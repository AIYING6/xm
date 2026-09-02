# P0 final verdict

## `MASTER_DESIGN_REQUIRES_REDESIGN`

The research question and a scalable layered redundant-topology benchmark family are justified. Candidate B (2 Scouts, 2 Relays, 2 terminal UAVs) is the best main-scale design **conditional on** proving non-duplicated roles and task-legal use of its redundant paths.

P0 cannot return READY because the current 3-UAV environment hardcodes three positions/kinematics, a required relay identity, legacy direct-recovery semantics, three-agent failure sampling, and reward terms whose meaning changes with agent count. The new generator, success semantics, role complementarity, normalized metrics, failure-mask ordering and durable compute/storage plan must be frozen before implementation.

**P1 is not authorized. No environment, training, rollout or evaluation was started.**
