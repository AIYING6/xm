# B-line P1 formal problem freeze

**Status:** `B_P1_CONDITIONAL`.

## What P0R establishes — and what it does not

Let the current physical snapshot be

\[
\sigma_t^P=(t,p_t,G_t^P,m_t,r,a^{\mathrm{assign}}),
\]

where `p_t` is UAV/objective geometry, `G_t^P` is the current active physical/task topology, `m_t` is mission progress, `r` is role state, and `a^{assign}` is the frozen assignment state. The P0R construction gives two legal histories \(h_F,h_S\) in the unmodified six-UAV `main` environment such that

\[
\sigma_t^P(h_F)=\sigma_t^P(h_S), \qquad
\mathcal A_{\rm native}(h_F)\neq\mathcal A_{\rm native}(h_S).
\]

The only decision-relevant difference is the native routed-cache sensing time. With the existing threshold \(\tau_{\max}=5\), terminal action 1 is legal at cache age 0 and masked at cache age 6. Therefore no policy or deterministic decision map whose input is only \(\sigma_t^P\) can recover both native feasible-action sets.

This is a scoped existence proposition for the current six-UAV environment. It is **not** a universal theorem about all UAV networks, a performance claim, a proof that a particular solver is optimal, or evidence that relay reconfiguration already exists in the current action interface.

## Formal object: physical graph plus information-validity service graph

P1 freezes two distinct state objects.

\[
G_t^P=(V,E_t^P), \qquad
G_t^V=(D\cup K,E_t^V).
\]

`G_t^P` is the current physical/active graph over agents and service routes. `G_t^V` is a terminal–objective service graph: \((d,k)\in E_t^V\) exactly when terminal \(d\) holds a valid native token for objective \(k\). Its edge indicator is

\[
\eta_{d k,t}=\mathbf{1}\{\operatorname{token}_{d k,t}\text{ exists, is valid, and }t-t^{\rm sense}_{d k}\leq\tau_{\max}\}.
\]

This is a feasibility predicate already enforced by the environment’s `_fresh_token` and `support_action_mask`; it is not a newly introduced freshness reward.

## Native decision variables and constraints

The only frozen native variables are:

- \(u_{s k,t}\in\{0,1\}\): scout \(s\) senses objective \(k\), with at most one native objective action per scout per step.
- \(z_{d k,t}\in\{0,1\}\): terminal \(d\) selects native service action \(k\), with at most one terminal action per step.

Their central hard condition is

\[
z_{d k,t}\leq \eta_{d k,t}.
\]

The native masks also prohibit service to completed objectives and impose the already-existing role/action cardinality rules. A feasibility-first future formulation may use mission completion/progress and existing safety semantics only after it states them explicitly; P1 adds neither a reward nor a deadline.

## Information boundary

An eventual deterministic method may use its present legal actor observation, current action mask, and an internal state deterministically reconstructed from its own past legal observations/actions. It may not use future failures, future topology, hidden RNG state, evaluation outcomes, or the environment’s unobserved node-failure flags.

## Conditional boundary

The evidence supports an **information-validity constrained sensing-service assignment** problem. It does not yet support the stronger phrase “constrained relay/routing reconfiguration”: the existing six-UAV interface has no transition-effective relay non-idle action, route selector, activation variable, switching cost, or make-before-break primitive. P1 deliberately does not invent any of these.

Consequently, no solver is selected. Any later solver must remain deterministic, reason over both \(G_t^P\) and \(G_t^V\), return a feasibility/infeasibility certificate, avoid privileged future state, and target a provable structural property. A separate zero-training expressiveness gate is required before a solver can be designed.
