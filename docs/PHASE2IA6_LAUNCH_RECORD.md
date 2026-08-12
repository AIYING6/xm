# Phase 2IA6 task-feasibility launch record

**Status:** frozen before feasibility outputs.  
**Protocol:** `PHASE2IA6-TF-V1`

The following is the complete authorized invocation. It runs 600 deterministic
fixed-controller episodes, with no neural policy, checkpoint, optimizer, or
training update:

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/run_phase2ia6_task_feasibility.py `
  --execute `
  --out-dir results/development/phase2ia6_task_feasibility `
  --episodes 100
```

The executor writes to a fresh namespace and refuses overwrite. The follow-up
is an independently implemented Gate F trace reconstruction. A Gate F pass
does not authorize training; a Gate F fail closes the current task formulation
without a Role-Gate efficacy conclusion.
