# L1 coordination-failure localization

Status: `L1_COORDINATION_FAILURE_LOCALIZATION_COMPLETE`

This is a read-only diagnostic of the already completed L1 development
checkpoints. It is not a new method experiment, formal evidence, or an
authorization to enter L2/N3.

## Diagnostic design

The two L1 checkpoints (training seeds 8201 and 8202) were evaluated on eight
fixed development episode seeds. For each checkpoint we compared:

1. full learned joint action;
2. an attacker-only counterfactual in which Scout and Relay actions were
   replaced by neutral guidance with `engage_commit=0`.

We also measured deterministic first-step action statistics by role. No
training, parameter change, communication impairment, or architecture change
was performed.

## Results

| checkpoint | mode | geometry entry | neutralized | mean RMTN180 |
|---|---|---:|---:|---:|
| seed 8201 | full policy | 0/8 | 0/8 | 180 |
| seed 8201 | attacker-only | 0/8 | 0/8 | 180 |
| seed 8202 | full policy | 0/8 | 0/8 | 180 |
| seed 8202 | attacker-only | 0/8 | 0/8 | 180 |

The attacker-only counterfactual does not improve over the full policy. Thus
there is no evidence that Scout/Relay physical actions alone are blocking an
otherwise successful learned Attacker.

At the first decision step, all three roles had `engage_commit=1` on all eight
states for both checkpoints. Continuous climb commands were also strongly
polarized (absolute means 0.35–0.91 by role/seed). This is consistent with a
joint policy/action-collapse symptom and a role-conditioned credit-assignment
problem, but does not by itself identify the causal mechanism.

## Current scientific conclusion

The localization narrows the L1 failure to the learned multi-agent policy
interface—role conditioning, shared credit assignment, or joint action
optimization remain unresolved. It does **not** implicate packet loss, delay,
relay failure, mission physics, or evaluator correctness. The diagnostic is
therefore a localization result only; it does not justify changing the reward,
action interface, parameter sharing, or architecture.

The project remains frozen at:

`L1_HETEROGENEOUS_RELIABLE_COMM_NO_GO__COORDINATION_BOTTLENECK__NO_L2_NO_N3`
