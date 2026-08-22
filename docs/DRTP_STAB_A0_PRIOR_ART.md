# DRTP-STAB-A0 Prior-Art Positioning

Adaptive task/context distributions, constrained changes between training
distributions, and risk-aware curricula are established ideas. In particular,
Self-Paced Contextual Reinforcement Learning uses a controlled intermediate
context distribution, while constrained optimal transport has been used to
constrain curriculum distribution changes. Risk-aware curriculum generation
also explicitly reweights difficult or risky tasks.

- Klink et al., *Self-Paced Contextual Reinforcement Learning*, CoRL 2020:
  <https://proceedings.mlr.press/v100/klink20a.html>
- Klink et al., *Curriculum Reinforcement Learning via Constrained Optimal
  Transport*, ICML 2022:
  <https://proceedings.mlr.press/v162/klink22a.html>
- Koprulu et al., *Risk-aware curriculum generation for heavy-tailed task
  distributions*, UAI 2023:
  <https://proceedings.mlr.press/v216/koprulu23b.html>
- van der Hoeven et al., *The Many Faces of Exponential Weights in Online
  Learning*, COLT 2018:
  <https://proceedings.mlr.press/v75/hoeven18a.html>

These sources make an arbitrary EMA, inertial update, or trust region a weak
novelty claim by itself. A future method would need evidence that its bounded
slow-timescale topology adaptation fixes a demonstrated DRTP-specific failure
mechanism. A0 does not supply that evidence, so no stabilization design is
positioned or authorized.
