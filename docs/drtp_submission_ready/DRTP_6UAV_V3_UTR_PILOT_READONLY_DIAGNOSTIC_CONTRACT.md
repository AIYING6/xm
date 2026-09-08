# V3 UTR pilot read-only diagnosis contract

The V3 UTR learnability pilot returned zero success on nominal and perturbed groups. This contract requires an action-level diagnosis before a DRTP arm or a revised task protocol may be considered.

The diagnostic loads the three frozen final UTR checkpoints only. It runs deterministic inference traces over the nominal and six frozen fault groups, recording action masks, selected actions, fault injection, delivered routes, objective completion and endpoints. It is prohibited from training, selecting checkpoints, changing optimizer state, changing the sampler, or making a UTR--DRTP claim.

The result separates two limited outcomes:

- `V3_PILOT_INTERFACE_BUG_FOUND`: a legal-action invariant failed; repair must target the identified interface defect.
- `V3_PILOT_SPARSE_CREDIT_ASSIGNMENT_LIKELY`: all observed masks/actions are legal but final policies still time out. This supports, but does not prove, that the completion-only reward creates a difficult credit-assignment problem.

Neither label is evidence about DRTP effectiveness or a cross-scale result.
