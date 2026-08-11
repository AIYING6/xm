# C0 Applied-Algorithm Novelty Recalibration Protocol

**Status:** `C0_APPLIED_ALGORITHM_NOVELTY_RECALIBRATION_AUTHORIZED__NO_CODE__NO_TRAINING`

## Why this gate exists

Earlier M1 and B0 decisions used a deliberately high bar: a candidate needed to
identify a distinct, broadly reusable MARL problem class that did not sit close
to any mature method family.  That bar was appropriate for a general-purpose
MARL/learning-theory contribution, but it is not the only defensible standard
for the actual intended venue class: a high-quality applied AI, robotics, or UAV
algorithm journal.

This protocol does **not** retroactively convert a rejected mechanism into a
novel one.  It changes the qualification question to the following venue-fit
standard:

> Does the complete acquisition-oriented framework contain a clear, task-driven,
> structurally differentiated mechanism for a real constrained-information UAV
> problem, with a fair comparator and falsifiable mechanism evidence, rather
> than a renamed or capacity-expanded version of a direct neighbour?

The strict information contract, physical `NEUTRALIZED` endpoint, and L4 failure
localization remain validity infrastructure.  They are not being relabelled as
algorithmic novelty.

## Candidate reopened for *positioning only*

The only candidate that may be reconsidered is the M0 acquisition-oriented
policy line from [M0 stage-aware acquisition method design](M0_STAGE_AWARE_ACQUISITION_METHOD_DESIGN_V1.md):

```text
legal target evidence/history
  -> acquisition-progress representation
  -> role-aware, acquisition-conditioned hybrid control
```

It is not permitted to revive a generic "GRU + stage embedding" claim.  Any
future Full method must retain the original M0 constraints:

- target history is updated only by legal local sensing or delivered,
  cache-valid evidence and resets when no legal target source remains;
- no global target state, `last_detected_target`, critic input, evaluator range,
  future observation, graph truth, or hidden communication payload enters the
  actor;
- physical mission semantics, aligned reward, continuous guidance, role-specific
  heads, non-attacker commit mask, range/loss/delay task, and horizon remain
  fixed;
- `B1` receives the same legal raw fields and history window, same hybrid action
  interface, and matched actor capacity.  Full may differ only by the explicit
  acquisition-progress/control coupling;
- the claim is rejected if Full does not improve the prespecified
  evidence-conditioned acquisition endpoints relative to B1.

## C0 corpus and procedure

Within two working days, collect and screen **15–20 papers published or
available in 2024–2026**.  The corpus must prioritize applied journals and
conferences that plausibly represent the intended submission tier, rather than
only general MARL venues.  Include direct UAV/multi-robot pursuit under partial
observation/communication and the closest general MARL architecture papers.

For every included paper, record:

| Field | Required record |
| --- | --- |
| Bibliographic metadata | title, venue, year, DOI/official URL |
| Actual problem | the operational limitation being addressed, not its title |
| Algorithmic unit | modules and how they interact |
| Information boundary | local/privileged/communication assumptions |
| Evaluation basis | task, baselines, ablations, and endpoint |
| Relation to M0 | same problem, same mechanism, partial overlap, or non-neighbour |

The review must include explicit direct-neighbour searches for:

1. heterogeneous UAV/multi-robot pursuit with partial or intermittent target
   observations;
2. task-progress, phase, or acquisition-conditioned control;
3. legal/provenance- and age-aware target-evidence histories;
4. recurrent/temporal MARL used as an acquisition-control mechanism; and
5. hybrid continuous-guidance plus commit actions for pursuit/neutralization.

## Recalibrated pass criteria

C0 is a **pass only if all** conditions hold:

1. **Real problem:** the evidence-to-acquisition failure remains a naturally
   observed, cross-checkpoint task problem under the strict actor contract.
2. **Structural distinction:** no direct 2024–2026 application neighbour has
   the same causal arrangement of legal evidence expiry, explicit
   acquisition-progress representation, and acquisition-conditioned role-aware
   control for the same constrained-information pursuit problem.
3. **No information or capacity confound:** Full--B1 input/history/action/reward
   equivalence and capacity parity remain implementable and testable.
4. **Mechanism falsifiability:** the frozen mechanism endpoints can disconfirm
   the framework even if final neutralization improves.
5. **Contribution proportionality:** the intended paper claims an applied
   acquisition-oriented MARL framework, not a new universal solution to
   partial-observation MARL or a new RL-theory family.

The following are insufficient for a pass:

- no paper has exactly the same module names;
- Full contains more components than MAPPO;
- a future pilot happens to improve reward;
- strict information legality alone is presented as a new algorithm.

## Decisions

| C0 outcome | Consequence |
| --- | --- |
| `C0_PASS__M0_APPLIED_ALGORITHM_TRACK_REOPENED` | Author may authorize minimal implementation followed by exactly one two-seed development pilot.  No additional pre-pilot redesign loop is opened. |
| `C0_NO_GO__NEW_PLATFORM_REQUIRED` | The M0 candidate remains closed; this platform may not be used to revive another renamed algorithm family. |

## Literature anchors motivating recalibration

Recent application-facing papers show the relevant *type* of contribution, not
proof that M0 is novel.  HATA combines trait encoding, trait-aware behaviour,
and a regularized training scheme for heterogeneous multi-robot pursuit
([Engineering Applications of Artificial Intelligence, 2025](https://www.sciencedirect.com/science/article/abs/pii/S0952197625020457)).
A 2026 ESWA study combines a pursuit-judgement model, dynamic interaction graph,
and graph-attention MARL for partially observable multi-UAV cooperative pursuit
([official article record](https://www.sciencedirect.com/science/article/abs/pii/S0957417426002472)).
These examples demonstrate that an application algorithm may contribute a
coherent, problem-specific framework; they do not remove the need for M0 to
show a substantive direct-neighbour difference, fair capacity matching, and
mechanistic evidence.

## Frozen prohibitions

Until C0 terminates, do not write method code, run a pilot, tune reward or
PPO, change the task, reopen B0 candidates, or claim M0 novelty.  C0 itself
terminates in one of the two decisions above.
