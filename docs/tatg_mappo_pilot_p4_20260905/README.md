# TATG-MAPPO pilot P4 — fixed endpoint evaluation

This separately authorized phase evaluates only the completed four-arm pilot
checkpoints at update 3,907 on the frozen development-only tape.

- Source runs: `4 arms × 3 training seeds`, fixed `actor_critic_latest.pt` only.
- Tape: five fixed conditions × 100 episode IDs (`780000–780099`).
- Budget: 6,000 inference episodes.
- Forbidden: training, resumption, optimiser updates, checkpoint promotion,
  milestone selection, held-out/canonical tape input and automatic directional
  gate aggregation.

The raw episode ledger and per-seed-condition table are the only outputs of
P4. The preregistered pilot gate is deliberately a later separate action.
