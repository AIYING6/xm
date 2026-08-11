# M1-R acquisition-mechanism redesign qualification v1

**Final status:** `M1R_NO_GO__NO_DEFENSIBLE_METHOD_NOVELTY`

## Scope

M1-R examined one replacement hypothesis before code: whether **action-conditioned acquisition-progress prediction** can be a defensible main-method mechanism for the evidence-to-attack-range acquisition problem identified from the frozen L4 checkpoints. It was literature and mechanism design work only: no candidate implementation, pilot, training, or reward/task modification was performed.

The question was deliberately stronger than whether an identical implementation exists. It was whether the proposed mechanism would be structurally distinct from existing future-state prediction, reachability/time-to-go guidance, or prediction-augmented policy learning.

## Candidate considered

The candidate would encode only legal actor history and predict whether current continuous guidance is likely to reduce the deficit to attack-range acquisition within a short future horizon. That prediction would then condition or regularize the policy. It would not expose evaluator geometry, target truth, `last_detected_target`, or a communication side channel to the actor.

This preserves the M0 legal-information boundary but changes neither the fact that the prediction is an action-conditioned forecast nor the fact that it is intended to guide policy improvement.

## Focused novelty findings

| Neighbouring family | Original/primary evidence | Consequence |
| --- | --- | --- |
| Action-conditioned prediction for navigation | Composable Action-Conditioned Predictors learns event cues backed up through action-conditioned prediction and uses them for robot navigation. | Predicting a future event under candidate actions is established, including navigation use. |
| Action-conditioned auxiliary predictive representation | Random deep action-conditioned predictions are explicitly proposed as auxiliary tasks for control representation learning. | “Predict progress as an auxiliary signal” is not a standalone algorithmic gap. |
| Predictive world models coupled to on-policy navigation | NavThinker couples an action-conditioned world model with on-policy RL and fuses future-aware signals into navigation control. | Action-conditioned future features guiding continuous navigation are direct modern prior art. |
| Time-to-go / impact-time guidance | Learning-based impact-time guidance estimates time-to-go and uses learned correction for guidance; later UAV guidance work continues this prediction-correction line. | Predicting approach/interception progress for control has established guidance-law antecedents. |
| Multi-agent action-conditioned dynamics | Multi-agent world-model work includes action-conditioned dynamics branches for cooperative learning. | MARL does not create a novelty gap merely by adding multiple actors. |

Primary sources checked: [Composable Action-Conditioned Predictors (CoRL 2018)](https://proceedings.mlr.press/v87/kahn18a.html), [Random Deep Action-conditional Predictions (NeurIPS 2021)](https://proceedings.neurips.cc/paper_files/paper/2021/file/c71df24045cfddab4a963d3ac9bdc9a3-Paper.pdf), [A Learning-Based Computational Impact Time Guidance](https://arxiv.org/abs/2103.05196), [Value Decomposition with a Disentangled World Model](https://arxiv.org/abs/2309.04615), and [NavThinker](https://arxiv.org/abs/2603.15359).

## Why the candidate does not clear M1-R

The candidate's intended chain,

```text
legal history + current action -> short-horizon acquisition prediction
                               -> policy conditioning or auxiliary loss
```

is a special-purpose instance of established action-conditioned future prediction and prediction-guided control. Restricting its raw inputs to legal, expiring communication evidence is scientifically necessary for this project, but it is an execution-information contract rather than by itself a new learning principle. Relabelling the target as `acquisition progress`, choosing attack range as its event, or applying it to multi-UAV coordination does not create enough structural difference to support a strong algorithmic novelty claim.

The evidence-derived task problem remains valid: legal target evidence often does not turn into attack-range acquisition. What M1-R rejects is only the proposed first solution as a headline method. A positive performance result could not repair that novelty deficit; it would remain ambiguous between a conventional predictive auxiliary/control benefit and a new mechanism.

## Preserved scientific assets

- strict recipient-specific actor contract with no global target-information bypass;
- independent physical `NEUTRALIZED` mission terminal outcome;
- role-specific-head, continuous-guidance baseline that demonstrates learnability;
- corrected-contract range/loss/delay L4 task;
- cross-checkpoint failure localization showing `NO_ATTACK_RANGE_ACQUISITION` as the dominant observed failure mode;
- a fair comparator discipline established in M1.

These assets may support a future benchmark, task-design, or diagnostic contribution. They do not justify training the rejected M1-R predictor.

## Hard stop and permitted next decision

`M1R_NO_GO__NO_DEFENSIBLE_METHOD_NOVELTY`

No implementation, pilot, training, auxiliary-loss tuning, history-window search, or parameter-budget search is authorized for this candidate.

The only evidence-honest next decision is one of:

1. **Reposition the project** around the rigorous task/actor-information protocol, controlled learnability ladder, and failure-localization findings; or
2. **Propose a new mechanism only after a new pre-implementation hypothesis identifies a structural gap not reducible to recurrent history, generic conditioning, predictive auxiliary learning, action-conditioned forecasting, time-to-go guidance, or conventional world-model planning.**

If such a gap cannot be specified before any performance is viewed, the algorithm-innovation line must remain closed rather than cycling through renamed predictive modules.
