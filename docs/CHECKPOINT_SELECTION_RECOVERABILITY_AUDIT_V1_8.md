# CHECKPOINT_SELECTION_RECOVERABILITY_AUDIT_V1_8

**Decision: CHECKPOINT_SELECTION_NOT_RECOVERABLE.** This is a read-only audit; no training, validation rerun, held-out evaluation, architecture/protocol change, or paper edit was performed.

## Frozen selector inputs required

The prespecified selector requires RMST80, establishment probability with censoring, RMST220, and earlier-update tie-break at every validation point. The immutable formal training logs contain only `eval_success_rate`, `eval_timeout_rate`, `eval_avg_steps`, and `eval_avg_distance`; RMST80/RMST220 and censoring-aware event times are absent.

Therefore the counterfactual prespecified winner update cannot be computed from existing logs. Update 300 cannot be accepted as a post-hoc terminal rule.

## Run-level result

| method | seed | prespecified winner update | update300 rank | winner metrics | update300 metrics | category |
|---|---:|---:|---|---|---|---|
| EA-RG | 0 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| EA-RG | 1 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| EA-RG | 2 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| wider single-graph | 0 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| wider single-graph | 1 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| wider single-graph | 2 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| matched non-graph | 0 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| matched non-graph | 1 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |
| matched non-graph | 2 | UNRESOLVED | UNAVAILABLE | UNAVAILABLE | update300 only, not selector-confirmed | C — EARLIER_WINNER_WEIGHT_UNAVAILABLE |

## Artifact provenance

Only final/latest artifacts and the final training state are present. The `actor_critic_update_0300.pt` files were copied after training for validation and are not immutable periodic snapshots. No earlier update artifact is present.

### EA-RG — seed 0
- `actor_critic_best.pt` sha256=`fb2807f5e14c3d42…` size=1661444
- `actor_critic_latest.pt` sha256=`fb8182d40317099c…` size=1661600
- `actor_critic_training_state_latest.pt` sha256=`36c471c68e9e1372…` size=4707619
- `actor_critic_update_0300.pt` sha256=`fb8182d40317099c…` size=1661600
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### EA-RG — seed 1
- `actor_critic_best.pt` sha256=`19c9b15519ea0631…` size=1661444
- `actor_critic_latest.pt` sha256=`f2de2602c7caae4d…` size=1661600
- `actor_critic_training_state_latest.pt` sha256=`4a8586ad537a54ec…` size=4707619
- `actor_critic_update_0300.pt` sha256=`f2de2602c7caae4d…` size=1661600
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### EA-RG — seed 2
- `actor_critic_best.pt` sha256=`184f3e231aba0fef…` size=1661444
- `actor_critic_latest.pt` sha256=`487ede1a310435b2…` size=1661600
- `actor_critic_training_state_latest.pt` sha256=`969b53c9cefabc08…` size=4707619
- `actor_critic_update_0300.pt` sha256=`487ede1a310435b2…` size=1661600
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### wider single-graph — seed 0
- `actor_critic_best.pt` sha256=`4c242172ad158c9e…` size=580140
- `actor_critic_latest.pt` sha256=`09392bebabca8a88…` size=580216
- `actor_critic_training_state_latest.pt` sha256=`4a2347da9160122b…` size=1464131
- `actor_critic_update_0300.pt` sha256=`09392bebabca8a88…` size=580216
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### wider single-graph — seed 1
- `actor_critic_best.pt` sha256=`bc76d2585bc8d87d…` size=580140
- `actor_critic_latest.pt` sha256=`58b1e197790ddf24…` size=580216
- `actor_critic_training_state_latest.pt` sha256=`bad41aa738ad3685…` size=1464131
- `actor_critic_update_0300.pt` sha256=`58b1e197790ddf24…` size=580216
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### wider single-graph — seed 2
- `actor_critic_best.pt` sha256=`98f601b9ce8619c3…` size=580140
- `actor_critic_latest.pt` sha256=`265587d109003622…` size=580216
- `actor_critic_training_state_latest.pt` sha256=`a939ed02b358f203…` size=1464131
- `actor_critic_update_0300.pt` sha256=`265587d109003622…` size=580216
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### matched non-graph — seed 0
- `actor_critic_best.pt` sha256=`3432c9fd9b15450a…` size=696578
- `actor_critic_latest.pt` sha256=`cb693bc86cdcfe94…` size=696642
- `actor_critic_training_state_latest.pt` sha256=`bbd6617d98ee7905…` size=1264474
- `actor_critic_update_0300.pt` sha256=`cb693bc86cdcfe94…` size=696642
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### matched non-graph — seed 1
- `actor_critic_best.pt` sha256=`db2e57b9b15de013…` size=696578
- `actor_critic_latest.pt` sha256=`3301aeffcdf77b89…` size=696642
- `actor_critic_training_state_latest.pt` sha256=`8683f2d1e50ce4ac…` size=1264474
- `actor_critic_update_0300.pt` sha256=`3301aeffcdf77b89…` size=696642
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
### matched non-graph — seed 2
- `actor_critic_best.pt` sha256=`f7fba5f630e5c621…` size=696578
- `actor_critic_latest.pt` sha256=`157ffa00c51cda72…` size=696642
- `actor_critic_training_state_latest.pt` sha256=`eff165ecab73c320…` size=1264474
- `actor_critic_update_0300.pt` sha256=`157ffa00c51cda72…` size=696642
- earlier winner weight: `WINNER_WEIGHT_UNAVAILABLE`
## Overall decision

Because RMST trajectory values are missing, all 9 runs are conservatively classified as category C. The audit cannot determine whether snapshot omission was outcome-neutral.

Protocol-repair proposal (not executed): rerun the same frozen training matrix with `--save-snapshots`, preserve validation endpoint logs including RMST/censoring fields at every 10-update point, then apply the unchanged selector. Do not accept update 300 as a new terminal rule.