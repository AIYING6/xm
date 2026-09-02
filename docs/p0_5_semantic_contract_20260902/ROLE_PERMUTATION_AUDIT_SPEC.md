# Role-permutation audit specification

Before learner training, test each within-role swap (S1/S2, R1/R2, T1/T2) while simultaneously permuting state rows, legal edges, objective assignments, message provenance and action indices. Actor outputs must permute correspondingly; critic value must be invariant to the matching global permutation. This detects hidden array-index capabilities. Parameter sharing is within role only.
