# Scalability engineering readiness

The current 3DOF environment explicitly requires `num_blue == len(blue_types)` and ships three blue type definitions. This is a hard-coded canonical-task boundary. No 4-agent or 5-agent training is authorized. Shape compatibility for a future scalable environment is unresolved and must be tested separately before any scalability claim.
