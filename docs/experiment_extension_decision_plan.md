# Experiment Extension Decision Plan

Generated: 2026-07-16T21:04:17

Purpose:

```text
Prioritize optional next experiments after the current EA-RG-MAPPO-S evidence chain.
The plan separates paper-strengthening experiments from future-system extensions so the current manuscript does not expand beyond what is feasible.
```

## Summary

```text
options = 7
blocked = 1
deferred = 3
ready = 3
```

## Recommended Order

```text
1. First choose target journal and template route.
2. If the target is practical Q2 (Drones/Aerospace/JIRS), prioritize template/PDF migration before expensive new experiments.
3. If adviser/reviewer asks for stronger evidence, choose between E1 five-seed extension and E2 real LAG reset probe.
4. Treat full 6DOF training and missile/radar/human-UAV teaming as later projects, not current-paper requirements.
```

## Options

| ID | Priority | Status | Experiment | Purpose | Dependency | Cost | Decision rule | Paper use |
|---|---|---|---|---|---|---|---|---|
| E1 | high | ready | Five-seed final 300-episode evaluation extension | Increase statistical credibility if the target venue or adviser asks for stronger seed evidence. | Requires two additional trained/evaluable seeds per method, or a deliberate decision to evaluate only available checkpoints if training already exists. | High: 2 extra seeds x 3 methods x 4 radii x 300 episodes, plus checkpoint management if new training is required. | Run only if reviewer/adviser requests stronger statistics, or if targeting a stricter venue than Drones/Aerospace/JIRS. | Strengthens main-result confidence; does not change the core innovation. |
| E2 | high | blocked | Real LAG/JSBSim reset-one-step role-graph probe | Convert the current LAG-like adapter smoke test into a real JSBSim interface validation. | Requires LAG envs/JSBSim/data and missing import path fixes before real env reset. | Medium once dependencies exist: one-step/reset probe plus 100-step graph-stat CSV. | Do this before any claim about 6DOF validation or before starting LAG training. | Supports migration-readiness evidence; still not enough for a full 6DOF performance claim. |
| E3 | medium | deferred | Retrained edge-feature structural ablation | Separate the effect of edge features from evaluation-time feature masking. | Requires retraining no-edge/partial-edge variants under matching budget. | High: new training runs and final evaluations; risk of consuming time without changing main conclusion. | Run only if reviewers question whether evaluation-time masking is sufficient for mechanism analysis. | Could upgrade mechanism evidence from diagnostic to stronger ablation, but is not necessary for the current core claim. |
| E4 | medium | ready | Longer communication-dropout evaluation | Increase robustness diagnostic confidence under degraded communication links. | Requires only existing checkpoints and evaluation script. | Medium: can extend from 50 to 100 or 300 episodes per seed at radii 4 and 8. | Run if dropout robustness becomes a central claim rather than appendix support. | Strengthens appendix robustness; avoid replacing the 300-episode main table. |
| E5 | low | deferred | Full 6DOF LAG training with EA-RG-MAPPO-S | Evaluate whether the finite-communication role graph method transfers beyond the 2D pursuit environment. | Requires E2 success, MultiDiscrete action head adaptation, JSBSim training stability, and new metrics. | Very high: environment debugging, action-head redesign, slow training, and new baselines. | Start only after the current 2D paper is submitted or if the first target journal requires stronger realism. | Potential second paper or major revision; should not be forced into the current manuscript prematurely. |
| E6 | low | deferred | Missile/radar/human-UAV cooperative system extension | Move from cooperative pursuit to a richer air-combat system model. | Requires 6DOF environment, sensor/weapon models, human/leader policy abstraction, and new safety constraints. | Very high: essentially a new system-level research project. | Do not start until E5 has a stable baseline and a clear second-paper question. | Future-work roadmap only; never use as current validation evidence. |
| E7 | medium | ready | Journal-template migration experiment-free pass | Convert the current evidence-backed English manuscript into the selected journal template. | Requires target journal decision and full LaTeX toolchain for PDF compilation. | Medium: formatting, declarations, figure/table placement, bibliography style. | Do before running expensive new experiments unless a target venue explicitly requires more realism/statistics. | Turns the current work into a submission package without changing experimental claims. |

## Boundary

```text
Rules, masks, and engineering constraints may support experiments but should not be written as the main innovation.
Do not start missile/radar/human-UAV extensions until a real 6DOF baseline is stable.
Do not claim LAG/JSBSim validation until a real reset/step probe and evaluation output exist.
```
