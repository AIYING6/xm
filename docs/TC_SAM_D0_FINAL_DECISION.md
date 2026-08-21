# TC-SAM-D0 Final Decision

## Decision

**A — TC_SAM_TECHNICAL_GO**

## Basis

The exact standard-SAM actor-only formulation is frozen with `rho=0.05` and `delta=1e-12`. All required pre-training audits pass:

- UTR/TC-SAM parameter counts are exactly 116,728;
- `rho=0` reproduces the UTR update within the frozen tolerance;
- nonzero perturbation has the requested norm and is exactly restored;
- the first pass does not advance Adam state and both SAM passes use the same logged minibatch;
- actor-boundary and inference-identity regressions pass;
- synthetic finite-value and checkpoint-continuation checks pass;
- no DRTP adaptive state enters the method; and
- measured optimizer overhead is technically acceptable with unchanged environment samples and zero inference overhead.

## Scope of this decision

This is an implementation-quality decision only. It does not prove improved robustness, seed stability, flatness, or publication readiness. It authorizes only a **separately requested** paired five-seed development experiment under `TC_SAM_D0_FUTURE_TRAINING_CONTRACT.md`.

## Stop record

D0 created no tape and started no MARL training, rollout, evaluator rerun, development seed, held-out seed, or canonical seed. Work stops here pending explicit author authorization.
