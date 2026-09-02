# Telemetry retention contract

Tier 1 permanently stores episode/update summaries, outcomes, failure ID, sampling probability, PPO statistics and topology summary. Tier 2 permanently stores fixed high-frequency windows around failure/path loss/switch/fresh support/recovery. Tier 3 stores full step trajectories only for a pre-hashed diagnostic registry, never selected after observing results. Every artifact has schema, manifest, compression and checksum.
