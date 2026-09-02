# P0.5 new-environment semantic freeze

**Authorization:** `P0_5_NEW_ENVIRONMENT_SEMANTIC_CONTRACT_FREEZE`  
**Verdict:** `SEMANTIC_CONTRACT_READY`  
**Next step:** not authorized.

This contract defines a new, isolated `redundant_topology_uav` benchmark family. It does not import, patch or execute the legacy 3-UAV environment. No policy, rollout, evaluation, seed, PPO parameter or candidate algorithm was created.

The family has one configuration rule: role counts determine the number of mission objectives, bipartite task-support edges, objective capacity, observation/critic dimensions, reward normalization, collision exposure denominator and failure enumeration. No `if N == 6` task rule is permitted.
