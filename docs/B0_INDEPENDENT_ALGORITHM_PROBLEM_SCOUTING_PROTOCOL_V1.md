# B0 — Independent Algorithm-Problem Scouting Protocol

**Status:** `B0_INDEPENDENT_ALGORITHM_PROBLEM_SCOUTING__LITERATURE_FIRST__NO_CODE__NO_TRAINING`

## Purpose

The audited 3DOF heterogeneous-UAV platform is retained as experimental
infrastructure, not as the source of a predetermined algorithm claim.  B0
searches for an independently defensible MARL/POMDP/heterogeneous-robotics
*scientific problem* first, then asks whether the existing platform naturally
instantiates it.

No candidate method, environment change, pilot, or training is authorized in
B0.

## Assets that may be reused later

- recipient-specific actor information contract;
- local sensing, delivered-packet, cache, age, confidence, and provenance
  mechanics;
- heterogeneous Scout/Relay/Attacker roles and continuous guidance interface;
- 3DOF dynamics and the independent `NEUTRALIZED` physical endpoint;
- current MAPPO implementation, logging, frozen episode semantics, and
  provenance infrastructure.

Reusing these assets never makes an algorithmic claim valid by itself.

## Closed families

The following cannot be reintroduced by a new name:

- recurrent memory, belief reconstruction, stage/progress latent variables,
  future prediction, or world models;
- action projection or guidance correction;
- local, dual, distillation, or conditional-projection critics;
- simple provenance/multi-relation graphs;
- ordinary value-of-information communication, message scheduling, bandwidth
  allocation, or latency adaptation;
- relay-failure recovery; and
- direct L4 attack-range-acquisition patches.

## Required five-gate screen

Every candidate must pass each gate before a phenomenon audit is allowed.

| Gate | Required evidence | Immediate kill condition |
| --- | --- | --- |
| G1 — independent problem | A precise failure/limitation stated without naming a neural module | Problem is merely a restatement of an L4 metric or desired result |
| G2 — natural instantiation | The existing platform already contains the causal variable, or only needs a scientifically motivated light extension | Requires hidden truth, an `if method` shortcut, a hand-made breakpoint, or a new mission story solely to help the method |
| G3 — execution legality | All proposed actor inputs/actions are derivable from the frozen recipient-specific contract | The mechanism needs privileged truth, recipient receipt knowledge, evaluator labels, or critic state at execution |
| G4 — literature separation | Direct 2024–2026 neighbours and older canonical methods leave a named mathematical/algorithmic gap | Novelty is only a new module combination, renaming, or application transfer |
| G5 — identifiable test | A strong, information- and capacity-matched comparator plus a pre-result mechanism endpoint exist | Full method has extra information, extra training privilege, or only final success as evidence |

## Literature-first search axes

B0 must search and red-team, rather than assume, the following axes:

1. **Dynamic decentralized dependencies:** policies and credit/coordination
   mechanisms when the set of decision-relevant neighbours changes online.
2. **Execution-information-structure shifts:** learning under changes in what
   each actor can legally know, distinct from generic domain randomization and
   generic memory reconstruction.
3. **Heterogeneous cooperative control:** role-specific action semantics,
   optimization interference, and control coupling, excluding already closed
   simple role-head/parameter-sharing fixes.
4. **Partial-observation learning theory/practice:** identify remaining gaps
   only after excluding belief, reconstruction, privileged/local critic, and
   information-value communication families.

The search must explicitly include competing results, not just papers whose
abstracts appear favourable.  Examples of close existing families already
requiring red-team treatment include dynamic-dependency Dec-MDP formulations,
partial-observation reconstruction, dual critics, dynamic communication
topology learning, and VoI-aware latency allocation.

## B0 workflow

```text
literature map (2024–2026 + canonical antecedents)
        ↓
candidate problem statement without method vocabulary
        ↓
G1–G5 screen and direct-neighbour table
        ↓
retain at most three candidates
        ↓
read-only, method-independent phenomenon audit
        ↓
only a passing candidate may enter method design
```

The phenomenon audit must use existing rollouts/checkpoints or a
method-independent scripted evaluation.  It cannot depend on a proposed
algorithm winning.

## Required B0 deliverable

The final B0 report will contain at most three candidates.  For each it will
state:

- the problem and why it generalizes beyond UAVs;
- causal variable already present in, or minimally and naturally motivated for,
  the platform;
- actor-contract legality analysis;
- direct-neighbour literature table and specific distinction;
- matched-comparator design;
- read-only audit and kill condition.

Valid exits are only:

- `B0_SHORTLIST_FROZEN__READY_FOR_PHENOMENON_AUDIT`;
- `B0_PARTIAL__ONE_CANDIDATE_REQUIRES_EXTERNAL_TASK_REFORMULATION`; or
- `B0_NO_GO__NO_DEFENSIBLE_ALGORITHM_PROBLEM_FOUND`.

Neither B0 nor a partial outcome authorizes code, training, a new algorithm
module, or a claim that the current platform has become a publication method
benchmark.

## Initial literature guardrails

The following papers establish why naïve candidate families have a high novelty
burden:

- Deweese and Qu formalize decentralized systems with dynamically varying
  dependencies in a Locally Interdependent Multi-Agent MDP framework (ICML
  2024, [PMLR](https://proceedings.mlr.press/v235/deweese24a.html)).
- MA²E learns masked reconstruction to mitigate partial observability (ICLR
  2025, [official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33301bb40020a56ef56b8b5081e5c4d5-Abstract-Conference.html)).
- Dual Critic RL already combines privileged and partial-observation critics
  (NeurIPS 2024, [official proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d399b67fa017f0f7670102c88507720c-Abstract-Conference.html)).
- Dynamic directed topology learning is already proposed for bridging training
  and decentralized execution (AAAI 2025,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/34507)).
- VIL2C explicitly targets value-of-information-aware latency control (AAAI
  2026, [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/40234)).

These works do not prove that no new problem exists; they prevent B0 from
misclassifying standard variants as new.
