# Design Decisions

## ADR-001: Keep the 2D Environment as a Baseline and Ablation Platform

Status: Accepted

### Decision

Do not replace the existing 2D UAV pursuit environment. Keep it for fast debugging, ablation, and historical evidence, while adding a separate 3DOF environment for stronger paper experiments.

### Reasons

- The 2D chain already has maintained checkpoints, tables, figures, and audits.
- Destroying the 2D baseline would make prior evidence unreproducible.
- A separate 3DOF environment allows staged migration without breaking existing results.

### Consequences

- Training scripts need environment selection.
- Documentation must distinguish 2D evidence from 3DOF learning results.

## ADR-002: Use 3DOF as the Main Training Environment Before JSBSim

Status: Accepted

### Decision

Use a lightweight 3DOF tactical environment for main training and formal comparisons. Use LAG/JSBSim only for future policy replay, feasibility checks, and visualization until the interface is restored and verified.

### Reasons

- Full 6DOF training with all baselines is high risk for a Q2-targeted graduate project.
- 3DOF captures the needed aviation constraints: position, speed, heading, flight-path angle, altitude, turn/climb limits, sensing, communication, and attack windows.
- LAG/JSBSim currently has only graph-adapter tests, not a complete runnable backend.

### Consequences

- Paper claims must say "3DOF constrained cooperative interception", not "full 6DOF air combat validation".
- JSBSim evidence can be added later as supplementary realism, not the main quantitative result.

## ADR-003: Treat Rules, Masks, ELO, and Self-Play as Auxiliary

Status: Accepted

### Decision

Rules, masks, reward shaping, demonstrations, ELO, and red-blue self-play are allowed as training/evaluation support but not as the main innovation.

### Reasons

- The user explicitly required that rules cannot be claimed as the innovation.
- Q2-level claims need a clear learning-method contribution rather than a rule-engine contribution.
- Self-play and ELO increase complexity and should not block the first 3DOF learning result.

### Consequences

- Main contribution wording should focus on multi-relation edge-aware role graph modeling and topology curriculum training.
- ELO/self-play can become an extension after 3DOF supervised baselines and ablations are stable.

## ADR-004: Preserve the Existing Environment Interface

Status: Accepted

### Decision

All maintained environments should expose:

```text
reset() -> obs, share_obs, graph_obs
step(actions) -> obs, share_obs, graph_obs, rewards, dones, infos
```

### Reasons

- Current MAPPO/GAT-MAPPO/EA-RG-MAPPO code depends on this interface.
- Keeping the interface stable reduces migration cost.
- It allows 2D and 3DOF environments to share training/evaluation infrastructure.

### Consequences

- New environment metrics should be returned through `infos`.
- Graph observations must include `node_feat`, `edge_feat`, `adj`, and `role`.

## ADR-005: First 3DOF Scenario is 3v1, Then 4v2

Status: Accepted

### Decision

Use 3v1 heterogeneous cooperative interception as the first trainable 3DOF scenario:

```text
scout UAV + relay UAV + attacker UAV vs high-value target
```

Only after 3v1 is stable, extend to 4v2 with an interceptor and a rule-based escort.

### Reasons

- 4v2 with escort, self-play, communication disruption, and attack windows is too much for the first implementation step.
- 3v1 is enough to validate sensing, relay, attack-window formation, role heterogeneity, and message-age metrics.

### Consequences

- 4v2 is an enhancement experiment, not the first success criterion.
- The immediate training target is a small 3DOF EA-RG-MAPPO-S smoke run.

## ADR-006: Use Multi-Relation Channels With a Union-Graph Residual

Status: Accepted

### Decision

In the 3DOF graph observation, expose separate perception, communication, and
dynamic task-support adjacency matrices. The multi-relation encoder processes
each channel with receiver-sender role-conditioned messages, then fuses them
with a residual union-graph channel.

### Reasons

- A single union graph cannot distinguish whether information is sensed,
  relayed, or supplied as task support.
- Relation-only propagation can be too sparse early in an episode, before the
  kill chain is established.
- The union residual preserves useful global context and keeps a strict
  single-graph ablation available through `graph_encoder=single`.

### Consequences

- The main method uses `graph_encoder=multi_relation`; the previous graph is a
  maintained baseline, not removed code.
- Demonstration initialization and PPO hyperparameters must be matched across
  the two encoders before making a comparative claim.
- The union residual is an information-preservation design choice, not a
  separate paper contribution.

## ADR-007: Treat Zero-Shot Topology Robustness as Scenario Screening

Status: Accepted

### Decision

Use the existing nominally trained 3DOF checkpoints to run zero-shot evaluations
under communication range compression, dropout, delay, radar dropout, and
temporary communication-node failure. Use these results only to select useful
training and evaluation disruptions.

### Reasons

- Running robustness evaluation before retraining is cheap and quickly reveals
  whether a disruption is trivial, saturated, or informative.
- A nominally trained policy is not expected to be optimized for topology
  disruptions, so poor zero-shot performance is a curriculum-design signal.
- The paper claim should compare matched policies after topology-curriculum
  retraining, not rely on a small screening suite.

### Consequences

- `results/intercept_3d_topology_robustness_screen/` is a diagnostic artifact,
  not final paper evidence.
- A robustness claim requires matched retraining, fixed evaluation seeds, and at
  least 30 evaluation episodes per checkpoint-scenario.
