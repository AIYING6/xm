# P07 Direct-Neighbour Novelty Red Team

**Final status:** `P07_NO_GO__B0_CLOSED__NO_ALGORITHM_PROBLEM_FOUND`

**Authorized scope respected:** direct-neighbour literature red-team only.  No
code, environment change, phenomenon audit, method design, pilot, or training
was performed.

## Question tested

P07 proposed the following possible research problem:

> A decentralized policy should remain competent when its *legally available
> execution information structure* changes across communication range, packet
> loss, and delay while the physical dynamics remain fixed.

The required standard was not that this phenomenon exists—our strict contract
already makes it exist—but that it is an algorithmic problem **distinct from**
ordinary communication robustness, dynamic-topology communication learning,
belief/reconstruction under partial observation, and robust MARL.

## Verdict

**P07 fails the distinct-problem gate.**  In the present platform, every
information-structure change is induced by an existing communication/observation
mechanism: visibility range, packet delivery failure, cache validity, or message
age.  It does not introduce a further, naturally occurring change in the
factorization of the decision problem that survives after those mechanisms are
named.

Calling the execution set "legal information" is essential for experimental
correctness: it prevents privileged target truth, pending payload, expired cache,
and critic information from entering an actor.  It is **not**, by itself, a new
learning objective or a distinct intervention variable.  Any proposed solution
to P07 would therefore fall into one of the already occupied method families
below.

| Proposed interpretation of P07 | Direct neighbour family | Why it is not distinct on this platform |
| --- | --- | --- |
| Remain effective when messages are delayed/lost/unavailable | Imperfect-communication and communication-robust MARL | The platform intervention is exactly range/loss/delay; renaming the recipient's resulting observation set does not create a separate phenomenon. |
| Adapt when reachable senders/neighbours change | Dynamic communication topology / learned communication structure | Range and delivery determine the neighbour graph already.  No additional non-topological structure change was identified. |
| Infer what is missing from intermittent evidence | Belief, history, reconstruction, predictive-state learning | Reconstructing unavailable state is precisely the closed memory/belief family, even if the missingness is described through a legal contract. |
| Be robust across observation functions/conditions | Robust/generalization MARL | This reduces to robustness/generalization across the same communication-condition family; no separate uncertainty model or intervention is present. |
| Exploit explicit information structures | Information-structure RL / decentralized control | Recent theory already treats time-varying dependencies and agent-specific available information as information structures, rather than leaving an unoccupied problem class. |

## Direct-neighbour findings

1. **Information structure is already a formal RL object, not a new label.**
   Altabaa and Yang formulate partially-observable sequential teams/games with
   explicit information structures, including agent-specific observables and
   time-varying causal dependencies.  This directly covers the conceptual move
   from a fixed observation vector to an execution-time information structure.
   Their contribution is theoretical/statistical, but it removes the claim that
   P07 has identified a previously unnamed learning problem.

2. **Communication constrained by delay, delivery, and topology remains a
   communication problem.**  VIL2C explicitly studies value-aware low-latency
   communication under delayed reception.  Dynamic directed-topology MARL and
   partial-observation communication work already optimize who communicates,
   what is received, and how policies respond when communication availability
   changes.  P07 adds no naturally different execution primitive beyond the
   platform's range/loss/delay channel.

3. **Robustness does not rescue distinctness.**  Robust MARL can focus on
   dynamics uncertainty rather than communication, but that difference is not a
   gap in P07's favour: the platform contains no independent uncertainty source
   other than the same communication availability process.  A P07 method would
   still be evaluated as communication-condition robustness/generalization.

4. **The strict actor contract is a validity requirement, not a mechanism.**
   The contract makes the benchmark scientifically usable and should remain a
   hard constraint for future work.  It cannot be promoted to a method claim
   merely because earlier project versions violated it.

## Required kill conditions and their outcomes

| Required condition for B1 entry | Outcome |
| --- | --- |
| A phenomenon beyond range/loss/delay communication degradation | **Fail** — none was identified naturally in the current platform. |
| A mechanism not reducible to topology learning, communication robustness, or belief/reconstruction | **Fail** — all candidate responses reduce to one of these families. |
| An independent, pre-method observable intervention for a P07-specific phenomenon | **Fail** — all observable interventions are the existing channel conditions. |
| A defensible literature gap after direct-neighbour comparison | **Fail**. |

## Consequence

B0 terminates with **zero** surviving algorithm-problem candidates.  P07 may
not enter `B1_P07_PHENOMENON_IDENTIFIABILITY_AUDIT`; doing so would use a new
name to reopen communication robustness, dynamic topology, or belief
reconstruction after those families were explicitly closed.

The current UAV platform remains a valid research infrastructure: strict
recipient-specific information, heterogeneous roles, physical neutralization,
and range/loss/delay communication are retained as audited assets.  It does not
currently contain a sufficiently distinct, defensible algorithmic problem for a
new method-paper line.

## Literature anchors

- Altabaa and Yang, *On the Role of Information Structure in Reinforcement
  Learning for Partially-Observable Sequential Teams and Games*, NeurIPS 2024,
  [official paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/0cbbdfb0a4098af8dc7a497a5e59aff7-Paper-Conference.pdf).
- Li et al., *Principled Learning-to-Communicate in Cooperative MARL: An
  Information-Structure Perspective*, CoCoMARL 2025,
  [OpenReview record](https://openreview.net/forum?id=5x8GmU4R3D).
- Shi et al., *Breaking the Curse of Multiagency in Robust Multi-Agent
  Reinforcement Learning*, ICML 2025,
  [PMLR](https://proceedings.mlr.press/v267/shi25c.html).
- VIL2C, *Value-of-Information Aware Low-Latency Communication for Multi-Agent
  Reinforcement Learning*, AAAI 2026,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/40234).
- Zhang et al., dynamic directed graph communication for multi-agent
  reinforcement learning, AAAI 2025,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/34507).

## Closed boundary

No P07 method, phenomenon audit, code, or training is authorized.  Reopening
algorithm discovery on this platform requires a newly scoped, independently
motivated research problem—not another B0 candidate or a renamed member of the
closed communication/memory/robustness families.
