# M0 — Q2 Paper Positioning

## Paper-level contribution bundle

The paper must not be sold as “SAM for UAVs.” Its defensible Q2 package is:

1. a legally constrained heterogeneous UAV relay-node failure problem in which failure triggers communication-path/topology reconfiguration rather than an artificial blackout;
2. a paired nominal/F0/OOD evaluation protocol that measures topology-robust coordination, safety, path switching, and task-support behaviour;
3. a mature **topology-conditioned flat-policy optimisation adaptation** applied to a fixed, legality-preserving UTR distribution;
4. exact-architecture UTR comparison, fixed final checkpoints, multi-seed outcomes, OOD timing/duration/compound conditions, and safety analysis;
5. a direct ablation: UTR versus TC-SAM-UTR under identical exposure, parameters, PPO, training budget, and evaluation tape.

## Claims allowed if future evidence supports them

- The adaptation improves robustness to the frozen relay-failure topology perturbation distribution and its OOD variants.
- The method adds no privileged execution information and no inference-time overhead.
- The gain is attributable to optimisation geometry beyond topology exposure, conditional on an exactly matched UTR control.
- Improvements are development evidence unless and until independently confirmed on a separately frozen held-out protocol.

## Claims prohibited

- “We invented sharpness-aware optimisation.”
- “SAM guarantees graph robustness” or “the actor is provably Lipschitz.”
- “Relay failure necessarily causes information loss” or “the method restores lost information.”
- Any causal claim about sharpness unless supported by later pre-registered mechanism evidence.
- Any result based on selected checkpoints, excluded seeds, altered failure semantics, or actor-side failure oracle.

## Full-paper plausibility test

If TC-SAM-UTR later produces stable roughly 10–15% F0/OOD gains in at least four of five paired development seeds, with retained nominal performance, no safety worsening, and a clear UTR ablation, the complete problem–method–evaluation bundle is credible for a solid Q2 application/AI journal. A much larger effect is not required. If it only improves nominal return or one selected OOD condition, it is not sufficient.
