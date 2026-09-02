# Information-boundary table

| Information | Actor at execution | Central critic during training | Trainer bookkeeping | Evaluation-only |
|---|---:|---:|---:|---:|
| own role/state and legal local sensing | yes | yes | yes | no |
| received timestamped/provenance-tagged messages | yes | yes | yes | no |
| support-link state observable locally | only if sensed/communicated | yes | yes | no |
| full topology mask / all agents' states | no | yes | yes | no |
| failure class, group id, curriculum probability | no | no unless inferable from allowed state | yes | no |
| seed, RNG streams, episode identifiers | no | no | yes | no |
| formal/held-out tape, aggregate scores, future labels | no | no | no | yes |

Actor messages require source, age, route/provenance and validity flags. The future environment must apply static failure masks before packet creation, cache update and graph construction; pruning an already-built adjacency is not adequate.
