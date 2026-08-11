# B0 — Candidate Scientific-Problem Screen (Round 1)

**Status:** `B0_SCOUTING_IN_PROGRESS__NO_CANDIDATE_PASSED_TO_PHENOMENON_AUDIT`

This is a literature-first screen, not a method proposal.  A candidate is
retained only when the *problem* is independently meaningful, naturally occurs
in the audited platform, respects the execution information contract, and has
an identifiable gap relative to direct literature neighbours.

## Round-1 candidate pool and disposition

| ID | Problem, without method vocabulary | Platform fit | Closest direct family | Disposition |
| --- | --- | --- | --- | --- |
| P01 | Privileged centralized training signals disagree with what a decentralized actor can distinguish | Observed in A0 | local advantage, dual critic, asymmetric actor-critic | **NO-GO** — A0 found the phenomenon but not a distinct solution |
| P02 | Intermittent evidence prevents a policy from retaining an adequate target information state | Natural | belief state, reconstruction, world model, MI/history learning | **NO-GO** — closed memory/belief family |
| P03 | A team needs to infer/maintain group consensus despite limited observations | Partly natural | implicit consensus, common-information MARL | **NO-GO** — would reopen communication/common-knowledge families and need new primitives |
| P04 | Dynamic communication topology makes some neighbours decision-relevant only intermittently | Natural at a graph level | dynamic directed topology learning, scalable topology design, EA-RG-v2 | **NO-GO** — direct graph/topology family is closed; no multi-evidence mechanism exists in this task |
| P05 | Delayed/lost messages should be prioritized by their decision value | Natural | VoI scheduling, progressive reception, active communication | **NO-GO** — explicitly closed ordinary VoI communication family |
| P06 | Heterogeneous roles suffer training interference under a shared policy | Observed historically | adaptive parameter sharing, learnable masks, role-specific heads | **NO-GO** — current transparent role-specialized baseline already repairs this; no new problem remains |
| P07 | A decentralized policy should remain competent when its legal observation function changes across range/loss/delay conditions, while physical dynamics are fixed | Natural: the contract and L1–L4 ladder already define such shifts | robust/generalization MARL and communication robustness | **PARTIAL** — phenomenon is testable without task changes, but literature separation and a non-generic algorithmic gap are unproven |
| P08 | A team must make mission progress without violating physical constraints when evidence is unavailable or stale | Potentially natural | decentralized shielding/safe POMDP/MARL | **PARTIAL** — terminal constraints exist, but the current L4 evidence has not shown an information-driven safety trade-off |
| P09 | Agents need to coordinate based on what delivery of a target claim can be *certified* across recipients, rather than solely on evidence content | Incomplete: provenance exists, acknowledgement does not | common-information/implicit-consensus communication | **PARTIAL** — needs an independently motivated acknowledgement protocol; cannot be inferred from current actor inputs |
| P10 | Credit should be assigned across agents making decisions on asynchronous schedules | Not natural: current agents act synchronously | asynchronous credit-assignment and asynchronous actor-critic | **NO-GO** — would require a new decision-time model rather than a light platform use |
| P11 | Offline joint-action distribution shift impairs heterogeneous coordination | Not natural: current research pipeline is online/on-policy | offline MARL conservative/Q-learning variants | **NO-GO** — requires a distinct offline-data problem and does not follow from the platform |
| P12 | Agents should actively choose sensing actions before acting | Not natural: sensing is currently environmental, not an action | active perception / information seeking | **NO-GO** — requires a new sensing-action task formulation; not a light extension |

## Why none is a PASS yet

P07–P09 are not method candidates.  They are the only remaining *problem
statements* that do not immediately violate the B0 exclusions, but each misses
at least one mandatory gate:

### P07 — execution-information-structure shift

The existing L1–L4 ladder naturally changes availability, dropout, and delay
while preserving the physical task.  A read-only cross-condition evaluation is
therefore feasible.  However, "robustness/generalization across observation
functions" is not yet a sufficiently specific algorithmic gap.  B0 must first
separate it from generic robust MARL, domain generalization, and communication
robustness.  No phenomenon audit is authorized until that separation exists.

### P08 — information-limited safety/missions

The simulator has collision and constraint terminal outcomes, but the current
L4 evidence does not show that mission failures are caused by an unavoidable
safety-versus-progress decision under legal uncertainty.  A method targeting
safety now would therefore be a problem invented from available simulator
flags, not one established by the task.

### P09 — certifiable delivery states

Packet provenance can establish *what a recipient has received*.  It cannot,
under the current contract, establish that another actor received the same
packet.  Adding recipient acknowledgements would be a new execution
communication protocol and must not be slipped into a method implementation.

## Literature red-team anchors

The first screen used the following direct neighbours as exclusion anchors:

- [Dual Critic Reinforcement Learning under Partial Observability (NeurIPS
  2024)](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d399b67fa017f0f7670102c88507720c-Abstract-Conference.html)
  makes critic-based responses to privileged versus partial observation a close
  family.
- [MA²E (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33301bb40020a56ef56b8b5081e5c4d5-Abstract-Conference.html)
  and [MI-based asymmetric learning (CoRL
  2025)](https://proceedings.mlr.press/v270/nguyen25b.html) make reconstruction,
  inference, and information-seeking responses to partial observability close
  families.
- [Locally Interdependent Multi-Agent MDP (ICML
  2024)](https://proceedings.mlr.press/v235/deweese24a.html) directly treats
  dynamically varying decentralized dependencies.
- [Dynamic directed graph communication (AAAI
  2025)](https://ojs.aaai.org/index.php/AAAI/article/view/34507) and
  [ExpoComm (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3514dbacaebf0f38b25adfe59ed81a8a-Abstract-Conference.html)
  substantially raise the novelty burden for topology/communication proposals.
- [Implicit consensus generation (AAAI
  2025)](https://ojs.aaai.org/index.php/AAAI/article/view/34490) and
  [VIL2C (AAAI 2026)](https://ojs.aaai.org/index.php/AAAI/article/view/40234)
  make generic consensus and value-aware latency communication unsuitable.
- [Asynchronous Credit Assignment Framework](https://arxiv.org/abs/2408.03692)
  and [Partial Action Replacement for offline MARL (AAAI
  2026)](https://ojs.aaai.org/index.php/AAAI/article/view/39402) exclude
  respectively a superficial asynchronous-credit and offline-shift reframing.

## Next permitted operation

B0 remains literature-first.  The next operation is a **direct-neighbour
novelty audit for P07–P09 only**.  It may result in zero surviving candidates.
It may not introduce an algorithm module, alter a task interface, or run a
phenomenon audit yet.
