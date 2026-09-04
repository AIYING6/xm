# TATG-MAPPO C4.5 — first-update same-rollout audit

This directory holds the maintained C4.5 source-audit result. The audit uses
one short real 3D fixed-UTR rollout and exactly one actor-only ordinary clipped
PPO update per frozen variant:

- CETM candidate;
- capacity-matched generic current-snapshot GRU control;
- zero-residual CETM control.

It excludes critic updates, evaluation, performance comparisons, checkpoint
selection, cloud execution and fresh-seed training. A passed mechanical audit
only permits a separately preregistered fresh-seed pilot contract.
