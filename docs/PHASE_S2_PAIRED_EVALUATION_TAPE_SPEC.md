# Phase S2 Paired Evaluation-Tape Contract

Every nominal/failure pair shares a deterministic episode ID, initial state,
target realization, action tape, and exogenous dropout/delay tape whenever the
corresponding process is enabled. The intervention bit is the only intended
condition difference: `failure_off` versus `failure_on`.

Episode IDs are deterministic and derived from the frozen method/seed/cell
namespace; no ID may be reused across methods. Each tape manifest records
protocol ID, commit SHA, config SHA, seed, episode ID, condition, horizon,
action-tape hash, exogenous-tape hash, and exposure status.

Required episode fields are `J`, `success`, `collision`, `timeout`,
`constraint_violation`, `failure_exposed`, and `terminal_step`. Required
timestep fields include communication edge identities, relation masks, path
identity, path length, source/provider, switch indicator, task-support state,
legal-information provenance, reward, and terminal flag.

The primary estimand uses all planned pairs. Mechanism fields are summarized on
exposed pairs only. Later canonical inference is seed-level paired/hierarchical
bootstrap; KM/RMST remain exploratory and cannot become headline evidence.
