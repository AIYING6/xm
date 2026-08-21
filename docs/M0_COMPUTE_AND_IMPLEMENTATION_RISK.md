# M0 — Compute and Implementation Risk

| Candidate | Actor / parameters | Training change | Expected training multiplier | Inference | Complexity | Major risk |
|---|---|---|---:|---|---|---|
| TC-SAM-UTR | unchanged / 116,728 | two-pass actor-and-critic PPO loss at a norm-bounded parameter perturbation; restore before optimiser step | approximately 2.0× | unchanged | Medium | PPO/SAM interaction must be audited for finite loss, restore exactness, and deterministic continuation. |
| SWA/EMA UTR | unchanged / 116,728 | fixed averaging schedule | ~1.0× | unchanged once averaged | Low | novelty insufficient; averaging must not become checkpoint selection. |
| Graph information bottleneck | new training modules / likely >5% | MI/message regularisers | >1.5× | potentially extra | High | violates clean matched-SG isolation. |

## TC-SAM-UTR code mapping

Expected implementation area is confined to the existing PPO update in `algorithms/ri_gmappo/simple_ri_gmappo.py`:

1. retain the fixed `FixedStratifiedTopologySampler` exactly as UTR;
2. construct the normal PPO loss on the existing sampled batch;
3. calculate the SAM perturbation from the complete trainable parameter gradient;
4. evaluate the identical PPO objective once at the temporary perturbed parameters;
5. restore exact parameters, then apply the optimiser update using the perturbed-objective gradient;
6. save/check the entire existing runtime state; add only SAM's temporary state if any is persistent (normally none).

No environment, reward, failure timing, graph-adjacency rule, actor feature, critic observation, or execution-time computation changes.

## Actor-legality classification

| Item | Classification | Reason |
|---|---|---|
| Existing `obs`, graph node/edge features, relation adjacency | ACTOR_LEGAL_AT_EXECUTION | Frozen S2 legal boundary. |
| SAM parameter perturbation and gradient | TRAINING_ONLY | Exists only during optimisation; never a policy feature. |
| PPO advantages / return / critic target | TRAINING_ONLY / CRITIC_ONLY as currently defined | Existing MAPPO training information; not exposed to execution actor. |
| Failure label, full connectivity, future link/path, simulator truth | FORBIDDEN | Remain absent from actor and SAM calculation. |
| Offline sensitivity outputs | DIAGNOSTIC_ONLY | M0-only audit, never actor input. |

## Risk controls required before any future long run

- parameter count must remain exactly 116,728;
- same fixed seven-group exposure must be byte-for-byte equivalent to UTR;
- temporary perturbation must be restored exactly even on an exception;
- no gradient surgery, no scenario reweighting, no extra actor information;
- unit test: radius zero equals UTR update; restore gives exact pre-perturbation state; one update is finite;
- deterministic save → reload → next-update continuation must remain exact;
- learning-cost contract must budget approximately twice UTR, never silently reduce the number of comparison seeds.
