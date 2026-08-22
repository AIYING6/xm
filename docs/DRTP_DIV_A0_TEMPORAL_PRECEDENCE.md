# DRTP-DIV-A0 — Temporal Precedence

The available chronology is bounded as follows:

1. PPO diagnostics are available throughout 0–10M.
2. Matched-state policy mapping is available at 0.5M intervals on recorded
   actor-legal runtime states.
3. Coordination trajectories are unavailable.
4. External nominal/F0/OOD behavior is evaluated only at final checkpoints.

The weak seeds show lower internal training reward by 0.5–1M, but neither H1
nor H2 supplies a unique precursor, and H3 cannot be timed. Consequently no
causal order `optimization → policy → coordination → performance`, or any
alternative order, is supported by the archive. Figure D is a boundary diagram,
not a causal diagram.

