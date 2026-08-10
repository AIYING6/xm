# L1 heterogeneous reliable-communication development report

Verdict: `L1_HETEROGENEOUS_RELIABLE_COMM_NO_GO__COORDINATION_BOTTLENECK`

This is a development-only learnability gate. It is not formal performance
evidence and does not authorize L2, N3, or any new method design.

## Protocol

L1 added only the frozen heterogeneous team (Scout, Relay, Attacker) to the
TLI2 L0 interface. Communication was reliable (`dropout=0`, `delay=0`), with
no relay failure or packet impairment. The aligned physical reward,
continuous turn/climb action, Bernoulli `engage_commit`, N0 mission physics,
four-step hold, and 180-step endpoint were unchanged. Vanilla no-graph MAPPO
was trained for 60 updates with seeds 8201 and 8202; evaluation used 32 fixed
development episodes.

## Results

| mode | geometry entry | neutralized by 180 | mean RMTN180 | collision |
|---|---:|---:|---:|---:|
| random | 14/32 (43.75%) | 1/32 (3.125%) | 176.16 | 0% |
| scripted | 32/32 (100%) | 32/32 (100%) | 52.88 | 0% |
| oracle | 32/32 (100%) | 32/32 (100%) | 52.41 | 0% |
| MAPPO seed 8201 | 0/32 | 0/32 | 180.00 | 0% |
| MAPPO seed 8202 | 0/32 | 0/32 | 180.00 | 6.25% |

The first evaluation attempt exposed an evaluator-only oracle conversion bug
(legacy 3DOF actions were mapped to guidance by the wrong index). That output
was retained separately and not used. After correction, scripted and oracle
both passed 32/32, confirming that the L1 task and mission evaluator are
physically reachable and correctly decoded.

## Interpretation

L0 continuous action established a small but reproducible single-interceptor
learning signal. With the Scout and Relay restored, both learning seeds lost
all geometry entry and neutralization despite reliable communication. The
current evidence therefore localizes the next bottleneck to heterogeneous
multi-agent coordination/credit assignment, not communication impairment or
mission physics.

No packet loss, delay, relay failure, additional training, hyperparameter
tuning, L2, N3, formal training, or paper claim is authorized by this report.
