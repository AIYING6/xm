# C0 Applied-Algorithm Novelty Recalibration Report

**Final status:** `C0_PASS__M0_APPLIED_ALGORITHM_TRACK_REOPENED`

**Scope respected:** literature/positioning only.  No method code, environment
change, training, pilot, or new performance inspection was performed.

## Decision

M0 passes **the applied-algorithm contribution gate**, not a universal-MARL
theory gate.  The defensible future claim is a problem-specific framework for
heterogeneous UAV cooperative neutralization under strict recipient-specific
information, not a claim that recurrent policy learning, latent progress, or
stage conditioning is newly invented.

The surviving framework hypothesis is:

> When legal target evidence is intermittent and expires, an actor should
> preserve its legal evidence history separately from target-free self history,
> infer acquisition progress from those histories, and use that progress to
> modulate hybrid guidance/commit control.  This can improve the conversion of
> legal evidence into physical attack-range acquisition.

The hypothesis is motivated by the pre-method L4 failure localization; it is
not selected because a future method is presumed to win.

## Corpus and screening result

Eighteen 2024–2026 records were screened.  The set intentionally includes
direct UAV/multi-robot pursuit papers and nearby general MARL architecture
papers, rather than only top-tier general-MARL work.

| Group | Screened examples | What it covers | Relation to M0 |
| --- | --- | --- | --- |
| Heterogeneous pursuit | HATA (EAAI 2025); CI-HRL (TNNLS 2025); multi-UAV/multi-USV pursuit (Swarm Evol. Comput. 2026) | trait/capability representation, heterogeneous collaboration, hierarchical target localization | Close on heterogeneous pursuit, but does not establish a legality-expiring evidence to acquisition-control mechanism. |
| Observation-constrained UAV pursuit | limited visual-field pursuit (JAS 2024); online-planning pursuit (2024); perception-enhanced MARL (ESWA 2026); full-planar-motion limited detection (Machines 2026) | local observation, limited detection, graph/perception enhancement, target prediction | Close on incomplete sensing, but uses graph/perception/prediction pathways rather than a matched-history acquisition-progress control test. |
| Temporal/recurrent MARL | MACRPO (Front. Robot. AI 2024); R-MADDPG; FOFE-MMAPPO (EAAI 2026) | recurrent/meta-trajectory or Mamba memory under partial observation | Confirms that legal memory alone is not novel and must be B1-matched. |
| Dynamic interaction representation | TransMARL (Sci. Rep. 2026); dynamic GAT pursuit (ESWA 2026); GERL cooperative pursuit (2026) | dynamic graph/Transformer/GAT under sensing constraints | Close architecture family, but their central intervention is interaction representation, not evidence-expiry-aware acquisition conditioning. |
| Communication/task frameworks | CCTD-MARL (2026); delayed-update HRL for UAV pursuit (TNNLS 2025); asynchronous UAV communication coordination (2026) | delay communication, task/communication coordination, hierarchical policy | Confirms communication delay cannot be M0's headline novelty. |
| Generic progress/phase control | task-progress curriculum MARL (ICML 2025); stage-aware robot reward modeling (2026); goal-conditioned UAV navigation (ICUAS 2026) | progress/stage signals and goal-conditioned control | Confirms progress language alone is insufficient; M0 must couple it to legal evidence expiry and the acquisition endpoint. |

The corpus found direct precedent for every *component* of M0: recurrence or
history, phase/progress concepts, heterogeneous policy specialization, graph or
Transformer interaction modelling, and communication-aware control.  It did
**not** identify an application-neighbour with all of the following causal
structure simultaneously:

1. a recipient-specific target-evidence state that may be updated only by local
   sensing or delivered/cache-valid packets and must reset on evidence expiry;
2. a separate target-free self/action history, preventing unavailable target
   content from persisting as an implicit cache;
3. an acquisition-progress representation that modulates the existing
   continuous-guidance plus attacker-only-commit policy; and
4. a primary comparison against a same-information, same-history,
   capacity-matched direct-fusion B1, assessed first by evidence-to-range
   acquisition rather than only success rate.

That is a sufficiently clear and falsifiable framework difference for the
application target.  It would not be sufficient to claim a new general theory
of partially observable MARL.

## Closest-neighbour boundary

The strongest direct neighbours impose the following wording and design limits.

| Neighbour | Verified contribution | Required M0 distinction |
| --- | --- | --- |
| MACRPO | recurrent actor/critic and meta-trajectory integration to address partial observability/cooperation | M0 may not claim recurrence or generic temporal cooperation; its actor history must remain recipient-private and legality-expiring, with no critic meta-trajectory in execution. |
| TransMARL | dynamic interaction graph plus Transformer for observation-constrained roundup | M0 may not add a dynamic graph/Transformer novelty claim.  Its mechanism is acquisition control after legal evidence, not interaction-graph encoding. |
| HATA | trait encoding, trait-aware behaviour, and regularized training for heterogeneous pursuit | M0 retains already validated role-specific heads as a transparent baseline requirement, not its main method contribution. |
| Perception-enhanced multi-UAV MARL | perception judgement, dynamic interaction graph, and GAT under partial observation | M0 may not claim that limited sensing or graph attention is new.  It must preserve physical evidence provenance/expiry and test acquisition as the mechanism. |
| CI-HRL / delayed-update HRL | hierarchical target localization or delayed-update control in UAV pursuit | M0 may not market its latent as a hierarchical subgoal, predictor, or generic delay compensator. |

## Recalibrated contribution statement

If future evidence supports it, the paper may claim:

> An acquisition-oriented heterogeneous MARL framework that uses only
> recipient-legitimate, time-limited target evidence to form an
> evidence-aware acquisition representation and condition hybrid pursuit
> control, evaluated against a history- and capacity-matched policy to isolate
> the acquisition-control mechanism.

It may **not** claim:

- a novel recurrent MARL primitive;
- a universal solution to POMDP/MARL information insufficiency;
- a new communication protocol, belief reconstruction, graph method, or
  theoretically optimal stage abstraction;
- that legal actor information alone is an algorithmic novelty.

## Frozen evidence chain for the reopened track

```text
L4 strict-contract failure localization
        -> evidence present but attack-range acquisition often absent
        -> M0 acquisition-oriented hypothesis
        -> Full vs history-/capacity-matched B1
        -> acquisition incidence, evidence-to-range latency,
           NO_ATTACK_RANGE_ACQUISITION
        -> neutralization and RMTN180
```

For Full to proceed beyond development, it must improve the first three
mechanism endpoints against B1.  A final-neutralization-only gain cannot
establish the mechanism claim.

## Next permitted action

`M2_MINIMAL_ACQUISITION_ORIENTED_IMPLEMENTATION` may now be separately
authorized.  It must implement only the already bounded Full/B1 pair, source
and reset regressions, parameter-parity manifest, and no-training interface
tests.  A two-seed, 60-update development pilot may occur only after M2 passes.
No new M0 modules, reward changes, task changes, or new pre-pilot novelty loops
are authorized.

## Selected primary records

- Kargar and Kyrki, *MACRPO: Multi-agent cooperative recurrent policy
  optimization*, Frontiers in Robotics and AI, 2024,
  [official article](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1394209/full).
- Wu et al., *An adaptive reinforcement learning approach with trait-awareness
  for heterogeneous multi-robot cooperative pursuit*, Engineering Applications
  of Artificial Intelligence, 2025,
  [official article record](https://www.sciencedirect.com/science/article/abs/pii/S0952197625020457).
- Xiang et al., *Decentralized Consensus Inference-Based Hierarchical
  Reinforcement Learning for Multiconstrained UAV Pursuit-Evasion Game*, TNNLS,
  2025, [PubMed record](https://pubmed.ncbi.nlm.nih.gov/40679888/).
- Li et al., *Dynamic-layer transformer-based reinforcement learning for
  observation-constrained multi-agent roundup scenarios*, Scientific Reports,
  2026, [official article](https://www.nature.com/articles/s41598-026-49608-7).
- Xiong et al., *A perception-enhanced multi-agent deep reinforcement learning
  method for multi-UAV cooperative pursuit*, Expert Systems with Applications,
  2026, [official article record](https://www.sciencedirect.com/science/article/pii/S0957417426002472).
- Ma et al., *Hierarchical Reinforcement Learning for UAV-PE Game With
  Alternative Delay Update Method*, TNNLS, 2025,
  [PubMed record](https://pubmed.ncbi.nlm.nih.gov/38381648/).
- Zhao et al., *Learning Progress Driven Multi-Agent Curriculum*, ICML 2025,
  [PMLR](https://proceedings.mlr.press/v267/zhao25o.html).
