# EDR-Q2 — Final Method Dossier

## Method and equations

**EDR-SG-MAPPO — Edge-Deletion-Resilient Single-Graph MAPPO.**

\[
h_i^\ell=f_\ell([v_i,r_i]),\quad e_{ij}^\ell=\operatorname{LeakyReLU}(a_\ell([h_i^\ell,h_j^\ell])+b_\ell(e_{ij})),
\]
\[
\gamma_{ij}^\ell=\sigma(e_{ij}^\ell),\quad c_i^\ell=\frac{1}{4}\sum_j A_{ij}\gamma_{ij}^\ell h_j^\ell,\quad h_i^{\ell+1}=\tanh(c_i^\ell).
\]

Only the two SG graph aggregations change. Local observation encoder, intent pathway, critic, policy head, PPO, training distribution, reward, failure semantics, and actor boundary remain unchanged. `L=L_PPO`; there is no auxiliary loss.

## Novelty and legality

The bounded novelty is a failure-aligned deletion-local specification, not new general GNN theory. It uses existing local observations, node/edge features, roles, and legal adjacency. Standard PPO trajectories/advantages are training-only. Failure labels, `share_obs`, global paths/states, and future topology are forbidden to the actor.

## Complexity and stability

EDR reuses existing score/payload parameters; target parameter count is exactly **116,728**, matching SG. It replaces softmax by sigmoid plus a fixed scalar reduction, so inference/training memory and FLOPs remain comparable. It adds no adaptive sampler, return feedback, curriculum feedback, gradient surgery, adversarial loss, or prediction target.

## Pre-frozen future controls

- A0: full EDR.
- A1: exact standard softmax SG/UTR.
- A2: edge-local gate with instantaneous-neighbour normalization, if compatible.
- A3: fixed normalization without learned edge gate.

Future evidence must include deletion-locality telemetry, topology/path reconfiguration, timeout, nominal, F0, OOD mean/worst, collision, constraint, and seed dispersion. EDR may claim reduced measured redistribution and, if confirmed, associated robust coordination; it may not claim restoration, invariance, or a robustness guarantee.
