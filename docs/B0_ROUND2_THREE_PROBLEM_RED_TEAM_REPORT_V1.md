# B0 Round 2 — Red-Team Report for the Three Retained Problems

**Status:** `B0_SCOUTING_ROUND2_COMPLETE__P07_PARTIAL__P08_P09_NO_GO__NO_PHENOMENON_AUDIT`

**Authorized scope respected:** literature and platform-fit analysis only.  No
code, training, task change, acknowledgement primitive, or phenomenon audit was
performed.

## Decision summary

| Candidate | Round-2 verdict | Reason |
| --- | --- | --- |
| P07 — robust coordination under execution-information-structure shift | `CANDIDATE_PARTIAL__NOVELTY_OR_PLATFORM_FIT_UNCLEAR` | Natural platform fit and legal actor inputs are plausible; however, the precise gap from robust MARL, imperfect-communication MARL, and dynamic-topology MARL has not yet been established. |
| P08 — safety–mission trade-off under information limitation | `CANDIDATE_NO_GO` | The environment has terminal safety flags but no demonstrated, naturally occurring information-driven safety-versus-mission trade-off.  Starting from a safe-RL method would manufacture the problem. |
| P09 — recipient-certifiable message-delivery coordination | `CANDIDATE_NO_GO` | Recipient-side packet provenance is legal, but cross-recipient receipt certification is not an execution primitive.  Introducing ACKs would be a new communication protocol, violating B0 platform naturalness. |

## P07 — execution-information-structure shift

### Problem statement

Can a decentralized team preserve coherent cooperation when the **legal
information structure available to each actor changes during execution**—for
example through range-limited visibility, random delivery failure, and message
age—while the physical mission and action semantics remain unchanged?

This is intentionally not phrased as "be robust to 30% dropout" and not as a
proposal for a GNN, memory module, or communication scheduler.

### What is natural in the platform

The strict contract already makes the actor's information set a function of:
local sensing, packet delivery, cache validity, age, confidence, and range.
L1–L4 therefore give a natural family of changing legal observation functions
without hidden truth or a new task primitive.  Any actor-facing mechanism would
be restricted to exactly those legal fields.

### Why it is not yet a PASS

The novelty gap is still ambiguous.  Robust MARL already optimizes against
specified dynamics uncertainty; communication MARL already studies limited,
dynamic, and directed information topology; and partial-observation work
already learns representations under changing/incomplete observations.  Merely
calling communication degradation an "information-structure shift" would be a
renaming, not a contribution.

For P07 to pass, the next *literature-only* check must identify a precise gap
that simultaneously excludes:

1. worst-case uncertainty in the transition/dynamics model;
2. ordinary test-time communication robustness or domain randomization;
3. learned communication-topology selection; and
4. belief/reconstruction of unavailable state.

It must also specify a read-only audit that can detect an information-structure
failure without evaluating a proposed method.  Until then P07 may not enter B1.

## P08 — information-limited safety versus task progress

Safe cooperative MARL is already a substantive literature.  More importantly,
the existing platform has not shown that an actor faces a recurring choice
between a legally uncertain safety condition and physically necessary mission
progress.  Current terminal collision/constraint fields alone are insufficient:
they are outcomes, not evidence of a causal decision conflict.

Adding a constraint penalty, Lagrangian, CPO-style update, shield, or safe
filter would therefore select a method first and retrofit a safety story around
it.  That fails G1 and G2.

**Verdict:** close P08.  It can only be reopened under a new independently
motivated safety task with an audited information-dependent conflict.

## P09 — certifiable message delivery

The strict contract supports the proposition "recipient \(i\) has this
delivered, cache-valid packet."  It does not support the proposition "sender
\(j\) can legally know recipient \(i\) received it."  The latter requires an
ACK/receipt/handshake event.  No such event exists in the frozen communication
semantics, and inventing one would change the science question from using an
existing constrained channel to designing a new communication protocol.

Existing consensus and communication work also gives this family a high direct
neighbour burden.  It fails G2 and G3 before novelty can be claimed.

**Verdict:** close P09 for the current platform.

## Literature anchors

- Robust MARL handles worst-case performance under uncertainty sets whose
  emphasis is dynamics/game uncertainty, not automatically the present legal
  observation-function problem: Shi et al., ICML 2025,
  [PMLR](https://proceedings.mlr.press/v267/shi25c.html).
- Safe cooperative MARL already includes function-approximation methods with
  explicit safety constraints: Hsu and Pajic, L4DC 2025,
  [PMLR](https://proceedings.mlr.press/v283/hsu25a.html).
- Dynamic directed communication topology is already an explicit MARL family:
  Zhang et al., AAAI 2025,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/34507).
- Consensus under partial observations and explicit communication is already
  targeted by Li et al., AAAI 2025,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/34490).
- Delayed-message value and latency allocation is already directly addressed by
  VIL2C, AAAI 2026,
  [official proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/40234).
- Partial-observation reconstruction/history learning remains a close family:
  MA²E, ICLR 2025,
  [official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/33301bb40020a56ef56b8b5081e5c4d5-Abstract-Conference.html),
  and Nguyen et al., CoRL 2025,
  [PMLR](https://proceedings.mlr.press/v270/nguyen25b.html).

## Permitted next action

Only P07 remains, and it remains **partial**.  The next action is a
P07-specific direct-neighbour novelty audit, with an explicit comparison against
robust MARL, communication robustness/topology learning, and partial-observation
representation learning.  It is still literature-first and may terminate B0
with no surviving candidate.
