# DRTP algorithm and comparator specification

## Method overview

DRTP changes only the distribution used to select an already-frozen topology-failure condition at environment reset. The actor, critic, graph interface, action masks, reward, transition rules, PPO objective and final evaluation protocol are shared with UTR. Nominal episodes keep a fixed mass of 0.50. Conditional on a non-nominal reset, UTR samples the six failure groups uniformly; DRTP learns a bounded distribution \(q_t\) over those same six groups.

The frozen groups are F0, TE, TL, DS, DL and CP. Every group contains a pre-defined finite set of onset/duration conditions. DRTP does not create new conditions and does not expose sampler state to the policy.

## Algorithm 1. Dynamic Robust Topology Prioritization

**Input:** fixed topology groups \(\mathcal G=\{N,F0,TE,TL,DS,DL,CP\}\), fixed nominal mass \(m_N=0.5\), UTR conditional distribution \(u_g=1/6\), PPO configuration, training budget.

1. Initialize \(q_0 \leftarrow u\), and initialize a per-group return window and exponential moving average (EMA).
2. At each environment reset, select nominal group \(N\) with probability \(m_N\); otherwise draw failure group \(g\sim q_t\) and uniformly draw one frozen condition within \(g\).
3. Run the unchanged policy and environment to episode completion. Append only the completed episode return to the window of its selected group.
4. Every 32 updates after the 128-update warm-up, update each available group EMA using coefficient \(\kappa=0.20\).
5. When all group EMAs are available, define the non-negative relative difficulty
   \[
   d_g=\min\left(2,\max\left(0,\frac{\bar J_N-\bar J_g}{\max(|\bar J_N|,10^{-8})}\right)\right).
   \]
6. Form a centered exponentiated candidate \(\tilde q_g\propto q_{t,g}\exp(d_g-\bar d)\), smooth it with the previous distribution using \(\beta=0.5\), and project it to the bounded simplex \(\sum_gq_g=1\), \(0.05\le q_g\le0.35\).
7. Use the projected \(q_{t+1}\) for later resets and continue unchanged PPO updates.

The sampler logs its state and completed-return summaries but never adds a reward, observation coordinate or loss term. The policy objective is therefore identical to UTR conditional on the sampled reset distribution.

## Comparator mechanism map

| Property | UTR | PLR-style comparator | Original DRTP |
|---|---|---|---|
| Sampling support | Same frozen topology conditions | Same matched frozen support | Same frozen topology conditions |
| Reset allocation | Uniform over non-nominal groups | Priority-based replay allocation | Group-level bounded allocation \(q_t\) |
| Priority signal | None | Generic replay priority | Nominal-referenced group return deficit |
| Topology semantics | Fixed groups only | Not topology-specific | Explicit failure group and condition hierarchy |
| Nominal exposure | Frozen | Matched protocol | Fixed 0.50 anchor |
| Policy / reward / PPO change | None | None under matched implementation | None |
| Evidence status | Complete | Running | Complete |

The PLR-style column is intentionally described as an external comparator rather than as a claim of equivalence to every implementation of PLR. Final wording must use the completed matched protocol and cite the original PLR work.

