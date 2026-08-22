# G0 Training-Topology Exposure Manifest

**Protocol:** `G0-TOPOLOGY-GENERALIZABLE-MARL-V1`  
**Status:** frozen before G0 evaluation  
**Scope:** SG, UTR-SG-MAPPO, and DRTP-SG-MAPPO historical training contracts.

## Reconstructed training exposure

All relevant training contracts use the frozen three-blue-UAV graph convention
`A[receiver, sender]`, with Scout `0`, Relay `1`, and Attacker `2`. The
physically legal direct Scout-to-Attacker communication edge remains part of
the nominal environment. The only training perturbation was temporary failure
of **Relay 1**; no historical contract trained on a deleted Scout--Attacker
edge, a directed edge deletion, or a Scout failure.

| Group | Members `(onset, duration)` | Structural graph change | Seen in training? |
|---|---|---|---|
| N | nominal | none | yes |
| F0 | `(44, 80)` | Relay-1 incident communication edges unavailable | yes |
| TE | `(28, 80)`, `(36, 80)` | same Relay-1 family | yes |
| TL | `(52, 80)`, `(60, 80)` | same Relay-1 family | yes |
| DS | `(44, 40)`, `(44, 60)` | same Relay-1 family | yes |
| DL | `(44, 100)`, `(44, 120)` | same Relay-1 family | yes |
| CP | `(28, 120)`, `(60, 120)` | same Relay-1 family | yes |

`UTR` sampled these groups with a fixed 50% nominal anchor and conditional
uniform failure exposure. `DRTP` used the same group set but adaptively
weighted the six failure groups. Hence adaptive weighting did not expose DRTP
to a new communication-graph family.

## Explicitly absent from training

- failure of Scout `0` or Attacker `2`;
- static or dynamic deletion of the direct `0→2` / `2→0` communication edge;
- directed/asymmetric communication topology;
- simultaneous Relay failure and direct-edge pruning;
- any graph with variable blue-agent count.

Changing only onset or duration is therefore **parameter OOD**, not unseen
topology evidence. The companion machine-readable record is
`artifacts/g0/topology_manifest.json`.
