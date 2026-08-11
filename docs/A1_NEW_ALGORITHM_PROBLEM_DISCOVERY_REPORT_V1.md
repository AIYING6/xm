# A1 — New Algorithm Problem Discovery: Red-Team Shortlist

**Status:** `A1_NO_GO__NO_DEFENSIBLE_ALGORITHM_PROBLEM_IDENTIFIED_IN_CURRENT_PLATFORM`

**Scope:** literature- and evidence-led problem discovery only.  No algorithm
implementation, no new training, no alteration of the L4 benchmark, and no
reuse of v1.6/v1.9 performance results as evidence.

## 1. Decision rule

A candidate could proceed to a read-only phenomenon audit only if all of the
following were true before any method was named:

1. the problem occurs naturally in the strict recipient-specific L4 platform;
2. its execution-time inputs can remain legal under the actor contract;
3. its nearest existing solution is not already an equivalent algorithmic
   family; and
4. it admits a strong, information-matched comparator.

Novelty here means a structural or optimization distinction, not merely that no
paper has the identical module combination.

## 2. Evidence base and exclusions

The following prior lines remain permanently excluded from A1:

- v1.6 recovery claims and checkpoints;
- PCRF-R2, GRU/stage conditioning, acquisition-progress prediction, EV-RAP,
  and EA-RG-v2;
- an unmodified local-advantage/conditional-expectation projection of a
  centralized advantage (A0); and
- a method that changes message bandwidth, latency allocation, active message
  scheduling, or relay-failure timing to manufacture an effect.

The A0 audit established a real mismatch: changing only training-only global
target information while preserving the actor input produced TD-advantage sign
flips in 58.4% and 62.5% of selected strict-L4 states.  This satisfies an
*existence* test, but is not by itself evidence that a centralized critic harms
the actor, nor does it establish a new algorithm.

## 3. Candidate screening

| Candidate scientific problem | Natural in current platform? | Closest direct neighbours | A1 decision |
| --- | --- | --- | --- |
| C1. Information-compatible CTDE advantage: remove the privileged component of a centralized advantage before actor update | Yes; A0 directly observes critic/actor mismatch | ROLA/local advantage; dual-critic POMDP methods; asymmetric actor-critic theory | **REJECT** — the direct conditional/local-advantage construction is not distinct enough |
| C2. Legal history/belief/uncertainty representation for intermittent target evidence | Yes; packet/cache age and legal history exist | belief-state MARL, masked reconstruction, mutual-information asymmetric learning, memory-learning diagnostics | **REJECT** — a history/belief encoder or uncertainty auxiliary task would be a close combination of existing families |
| C3. Recipient-certifiable delivery state: coordinate differently when an agent can distinguish evidence it received from evidence it can certify another role received | Not currently; packet provenance exists, but receipt acknowledgement/common knowledge is not part of the frozen execution protocol | common-knowledge coordination and communication-protocol learning | **REJECT for current platform** — an acknowledgement protocol would change the task communication interface and would need an independent problem formulation |

### C1: information-compatible CTDE advantage

The intended estimator, \(\mathbb{E}[A^{central}\mid I_i^{legal},a_i]\), is
mathematically a conditional/local advantage construction.  Local Advantage
Networks already introduce local advantage critics for Dec-POMDP agents, while
Dual Critic RL explicitly combines privileged and partial-observation critics.
The relevant current theoretical literature also gives asymmetric critics a
qualified justification rather than a blanket indictment.  A new residual,
projection, or distillation penalty would therefore need a substantially new
mathematical object; none was identified in this screening.

**Outcome:** A0 remains useful diagnostic evidence, but C1 must not proceed to
implementation as an allegedly new policy-optimization method.

### C2: legal history/belief/uncertainty

The platform naturally contains delayed, dropped, cache-valid evidence.  Yet
the obvious response—learn a legal belief/history representation and use its
uncertainty for policy learning—is already occupied by several close lines:
learned cooperative belief states, masked reconstruction under partial
observability, mutual-information asymmetric learning, and auxiliary memory
learning diagnostics.  Relabelling a GRU, reconstruction loss, or predicted
target uncertainty would not create a defensible central contribution.

**Outcome:** Do not reopen recurrent memory, stage conditioning, prediction,
or latent belief as a new algorithm line.

### C3: recipient-certifiable delivery state

This is the only conceptually different item found by the screen.  In a
drop/delay system, "I possess a cache-valid target claim" and "I can legally
know that the Attacker possesses that claim" are different epistemic states.
However, the present environment has provenance of delivered packets, not a
frozen acknowledgement/receipt protocol.  Supplying a sender with the
recipient's receipt state would add a new execution-time communication
primitive; it cannot be inferred from the actor's existing legal input.

This makes C3 unsuitable as a natural algorithm problem in the *current*
benchmark.  It should not be rescued by silently adding acknowledgement fields
or an `if receiver_received` side channel.  Common-knowledge communication is
also an established MARL direction, increasing its novelty burden.

**Outcome:** Reject within this project.  It may only be reconsidered as a new
task/protocol research question with a separate literature review and a new
communication contract.

## 4. Consequence for the project

No candidate passes all four A1 gates.  In particular, the current L4 platform
does not support a defensible claim that a new neural module, a critic
correction, or a communication mechanism is required.

This is a positive stopping result, not a reason to select a weaker novelty
claim after the fact:

```text
real phenomenon + existing equivalent solution  -> no algorithm claim
interesting idea + absent legal task primitive  -> no current-platform claim
```

Therefore the permitted next action is **not** A1-R1 implementation.  A future
algorithm-paper plan needs an independently motivated research problem whose
task semantics and direct-neighbour novelty can pass this same screen before
any code is written.  The present L4 platform remains valuable as audited
infrastructure and as a testbed, but it does not currently supply such a
problem.

## 5. Sources consulted (primary/official where available)

1. Lyu et al., *On Centralized Critics in Multi-Agent Reinforcement Learning*,
   2024, [arXiv:2408.14597](https://arxiv.org/abs/2408.14597).
2. Lambrechts et al., *A Theoretical Justification for Asymmetric Actor-Critic
   Algorithms*, ICML 2025,
   [PMLR](https://proceedings.mlr.press/v267/lambrechts25a.html).
3. Ma et al., *Local Advantage Actor-Critic for Robust Multi-Agent Deep
   Reinforcement Learning*, [arXiv:2110.08642](https://arxiv.org/abs/2110.08642).
4. Wang et al., *Dual Critic Reinforcement Learning under Partial
   Observability*, NeurIPS 2024,
   [official proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d399b67fa017f0f7670102c88507720c-Abstract-Conference.html).
5. Nisioti et al., *Belief States for Cooperative Multi-Agent Reinforcement
   Learning under Partial Observability*, 2025,
   [arXiv:2504.08417](https://arxiv.org/abs/2504.08417).
6. Nguyen et al., *Leveraging Mutual Information for Asymmetric Learning under
   Partial Observability*, CoRL 2025,
   [PMLR](https://proceedings.mlr.press/v270/nguyen25b.html).
7. Kang et al., *MA²E: Addressing Partial Observability in Multi-Agent
   Reinforcement Learning with Masked Auto-Encoder*, ICLR 2025,
   [OpenReview](https://openreview.net/forum?id=klpdEThT8q).
8. Deweese and Qu, *Locally Interdependent Multi-Agent MDP: Theoretical
   Framework for Decentralized Agents with Dynamic Dependencies*, ICML 2024,
   [PMLR](https://proceedings.mlr.press/v235/deweese24a.html).
9. Zhang et al., *VIL2C: Value-of-Information Aware Low-Latency Communication
   for Multi-Agent Reinforcement Learning*, AAAI 2026,
   [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/40234).

## 6. Freeze statement

`A1_NEW_ALGORITHM_PROBLEM_DISCOVERY` is complete.  It authorizes neither code
nor training.  Any attempt to continue algorithm development in this platform
must first replace this NO-GO with a new, independently qualified problem
statement; it may not simply rename C1–C3.
