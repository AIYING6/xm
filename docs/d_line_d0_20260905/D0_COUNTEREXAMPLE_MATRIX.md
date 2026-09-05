# D0 deterministic counterexample matrix

All three toys were exhaustively compared over their two available slot-0 actions by `scripts/run_d_line_d0_high_quality_deterministic_topic_selection.py`. They are tests of *decision nontriviality*, not evidence that a publishable problem is novel.

| Candidate | State at slot 0 | Competing legal decisions | Hard temporal/resource coupling | Greedy value | Horizon-optimal value | Result |
|---|---|---|---|---:|---:|---|
| A | One relay capacity unit; S1 immediately migratable; S2 has a slot-1 continuity deadline | migrate S1 now / reserve for S2 | Capacity one; S2 becomes infeasible if the reservation is consumed | 6 | 10 | Strictly non-myopic |
| B | Two agents have unequal versions; one broadcast unit; a high-value joint task at slot 1 requires a common version | execute local task / synchronize required version | One broadcast; version mismatch is declared hard infeasibility for the joint action | 4 | 9 | Strictly non-myopic, but semantic contract still absent |
| C | A recovered route exists; one temporary capacity reservation protects a slot-1 service deadline | immediate failback / hold reservation | Capacity one; immediate failback removes only recovery buffer | 5 | 8 | Strictly non-myopic |

## What these toys do and do not establish

They establish a real decision competition for each candidate: no candidate fails merely because “do everything” is optimal. They do **not** clear novelty or solver gates. In particular, A/C are ordinary reconfiguration-with-switching examples, while B requires a new action-feasibility semantics that is not yet native to the repository.

The fixed machine-readable values are in `D0_COUNTEREXAMPLE_TRUTH_TABLE.csv`; no environment interaction, learning, objective fitting, or evaluation tape is used.
