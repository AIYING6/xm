# Phase 2IA6 feasibility executor audit

The executor is a fixed-controller probe, not a learning/evaluation script.
Before launch, `scripts/test_phase2ia6_task_feasibility.py` and
`scripts/audit_phase2ia6_task_feasibility_executor.py` must pass.

The audit verifies that it has no checkpoint loader, optimizer, or training
path; uses only the frozen two-controller/three-seed matrix; requires explicit
`--execute`; refuses overwrite; emits raw episodes and timestep traces; and
that the legal-observation controller does not reference any simulator target
truth attribute. Its only external state is the current legal observation.

Passing this audit permits the feasibility probe only. It does not authorize
training, canonical experimentation, recovery analysis, or Role-Gate choice.
