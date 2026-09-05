# D0 topic scorecard

Scores measure publication headroom *after* deducting direct nearest-neighbor and solver risks. They are not predicted benchmark results. Any hard-gate failure disqualifies a winner regardless of score.

| Candidate | Novelty /25 | Solver depth /20 | Theory /15 | Determinism /10 | Env cost /10 | Baselines /10 | Strong-Q2 /10 | Total /100 | Hard-gate status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A: service continuity reconfiguration | 3 | 3 | 4 | 10 | 6 | 10 | 2 | **38** | Fail: direct UAV reconfiguration + generic flow/MILP |
| B: version-aware consistency coordination | 9 | 6 | 8 | 10 | 5 | 9 | 5 | **52** | Fail/conditional: direct consistency allocation neighborhood; no separated solver structure |
| C: recovery-aware migration/failback | 4 | 4 | 5 | 10 | 5 | 10 | 3 | **41** | Fail: stateful migration/failback + generic switching control |

## Interpretation

B is *less weak*, not strong enough. Its score reflects a potentially important feasibility distinction—versions may govern whether a joint action is legal—not permission to promote it to a main line. A strong-Q2 deterministic-algorithm paper must clear every hard gate, in particular a non-generic solver and a theorem target that survives direct neighboring work. None does.

All three are clearly outside TG-VM's semantic-map/risk-constrained inspection-planning scope. This separation alone cannot compensate for novelty or solver failure.
