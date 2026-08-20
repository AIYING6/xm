# T5 — Support-Utilization Formalization

## Frozen objective and boundary

T5 formalizes the T4 utilization gap without reopening the closed T3 temporal route or modifying the S2 actor boundary. Let `x_i^t` be agent *i*'s instantaneous decentralized actor input, `z_i^t=f_SG(x_i^t)` the existing SG representation, and `π_i(·|z_i^t)` the action distribution.

The actor-legal local support descriptor considered for design review is

\[
q_i(x)=\left[d_i,\;c_i,\;1-a_i^{\rm inbound},\;1-a_i^{\rm cache},\;\kappa_i^{\rm cache}\right],
\]

where the entries are respectively direct detection, inbound connectivity, normalized inbound-message freshness, normalized cache freshness, and cache confidence. Each is already contained in the attacker local observation. It is not a failure label, topology oracle, path oracle, global state, future state, or critic-only field.

## Utilization is an output response, not representation

For a locally plausible recorded support replacement \(q\mapsto \bar q\), define the finite-difference policy response

\[
R_i(x;q\!\to\!\bar q)=
\pi_i(\cdot\mid x[q\leftarrow\bar q])-\pi_i(\cdot\mid x).
\]

The scalar utilization magnitude is \(U_i=\tfrac12\lVert R_i\rVert_1\). A policy may encode support in \(z_i\) while having \(U_i\approx0\); conversely, a large \(U_i\) says that the decision distribution, not merely an internal latent, changes when available support changes. T4 measured this object offline by unavailable/stale masking and within-stratum recorded-value permutation.

Role-specific utilization would require the response map \(R_i\) to vary meaningfully by Scout, Relay, and Attacker roles. Topology-transition consistency would require the *response difference*, rather than the absolute action or latent, to remain compatible across matched pre/early topology phases:

\[
\operatorname{cos}\!\left(R_i(x_{\rm pre}),R_i(x_{\rm early})\right).
\]

This deliberately does **not** require \(\pi_{\rm pre}=\pi_{\rm early}\) or \(z_{\rm pre}=z_{\rm early}\): topology reconfiguration can legitimately alter actions, paths, and attention.

## Information classification

| Quantity | Classification | Use permitted in a future design review |
|---|---|---|
| `x_i`, legal graph tensors, `q_i(x)` | ACTOR_LEGAL_AT_EXECUTION | actor input / finite-difference source |
| role identity | ACTOR_LEGAL_AT_EXECUTION | role-stratified analysis only if evidence requires it |
| condition family and matched descriptor | TRAINING_ONLY_SUPERVISION | possible batch pairing only; never actor/critic input |
| T4 good/weak rank, phase, future continuity, returns | DIAGNOSTIC_ONLY | falsification and evaluation only |
| failure truth, global path/topology, shortest path, `share_obs`, future state | FORBIDDEN | never actor feature or execution dependency |

## Sole T5 design hypothesis, then falsified

The only candidate examined was **topology-equivariant role-specific support-response coupling**: an action-level constraint on \(R_i\), not a new encoder, FiLM/gate, memory, role embedding, mixture, or classifier. A hypothetical future loss would align response *contrasts* across matched topology contexts while leaving base actions topology-adaptive. It would be parameter-neutral but add response forward passes and a bounded cosine/contrast term.

T5 does not freeze or implement this loss. Its key empirical prerequisite—good policies showing at least weak-level pre-to-early response consistency—fails in the dedicated offline audit. The formalization remains useful as a diagnostic definition only.
