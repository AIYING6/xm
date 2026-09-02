# RNG and reproducibility specification

Freeze independent reproducible streams: `seed_init`, `seed_env`, `seed_action`, `seed_minibatch`, `seed_task`, `seed_failure`, `seed_comm`, `seed_topology`, and `seed_eval`. Record stream derivation, environment/config hash, code commit, hardware/software versions, topology/failure list hashes, checkpoint hash and evaluation-tape hash in every manifest. Save enough runtime state to resume exactly, including optimizer, sampler, RNG streams and message/cache state.
