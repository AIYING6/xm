# B-line P1 future solver requirements freeze

No solver is implemented or selected by this document.

If a later gate authorizes solver work, the method must satisfy all of the following:

1. It receives legal present observations plus legally reconstructed history only; it cannot receive future topology, future failures, evaluation outcomes, hidden RNG state, or privileged node-failure flags.
2. It represents both the current physical graph \(G_t^P\) and validity service graph \(G_t^V\). Replacing \(G_t^V\) with a scalar AoI/freshness penalty fails this requirement.
3. It treats the native freshness rule as a hard action/service feasibility constraint, not a tunable reward coefficient.
4. For a fixed admissible input history, it is deterministic and produces either a feasible action/plan or an explicit infeasibility certificate.
5. It uses only decision variables native to the declared target interface. It cannot silently introduce relay routing, activation, switching or deadline variables.
6. Before performance experiments, it must state a checkable structural property — for example feasibility preservation, finite termination, approximation quality under stated assumptions, or equivalence to a declared time-expanded formulation.
7. A generic greedy age rule, a shortest-path wrapper, or a renamed AoI penalty is not sufficient to meet the requested high-ceiling contribution.

## Deliberately unresolved items

The following are not frozen as native in the current six-UAV environment: relay reassignment, route selection, service activation, make-before-break transitions, switching costs, and any new communication deadline. They require a later expressiveness decision; they cannot be smuggled into a solver under the P1 contract.
