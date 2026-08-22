# PAPER-Q2-P1 Scalability Decision

**Decision: `S0 — EXISTING_ARCHITECTURE_NOT_FAIRLY_SCALABLE`**  
**Training/evaluation:** none started.

The environment loops over `num_blue`, but the frozen S2 configuration is explicitly a three-blue-role system and requires `num_blue` to match the `blue_types` list. The shared observation dimension depends on `num_blue`; the role semantics, Relay-failure contract, legal support paths, and task geometry would need a new configuration and a new failure/provenance contract. The critic input dimension also changes with `num_blue`, so the existing 3-UAV checkpoint is not a valid zero-shot 4/5-UAV checkpoint.

Therefore a 4/5-UAV study would require retraining and a separately frozen environment/evaluation contract. It is scientifically meaningful future work, but not a minimal zero-training closure item. The paper scope is explicitly the heterogeneous 3-UAV setting, with scalability stated as a limitation rather than manufactured through an unfair table.
