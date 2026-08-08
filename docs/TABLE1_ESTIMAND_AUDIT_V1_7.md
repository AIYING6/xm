# Table 1 estimand audit v1.7

## Scope

This audit changes labels and denominator documentation only. It does not
recompute or discard locked numerical values. The current LaTeX table and
Chinese manuscript table are not identical: the LaTeX table contains internal
ablations and additional columns, whereas the Chinese table is a four-method
main comparison. They must not be silently treated as the same table.

## Column audit

| Metric | Numerator / construction | Denominator / population | Conditioning | Time origin / censoring | Seed aggregation |
|---|---|---|---|---|---|
| Stable-task-chain establishment probability (legacy `Recovery`) | Episodes with `post_failure_chain_recovered=1` / establishment event observed | Failure-exposed Early+Nominal held-out episodes for the method | No event-time conditioning; event can be first establishment without prior chain loss | Failure onset; episodes without event are not counted as events and are handled by the KM analysis when RMST is used | Per-seed rates, then mean ± sample SD across 3 training seeds |
| Success | Episodes with terminal environment `success=1` | All held-out evaluation episodes in the reported protocol, not necessarily the same risk set as the failure-exposed time-to-establishment analysis | No establishment-event conditioning | Environment terminal outcome; no RMST censoring interpretation | Per-seed rates, then mean ± sample SD |
| Conditional mean `t_est` (legacy `t_rec`) | Mean `recovered_only_steps` among episodes with an observed establishment event | Event-positive failure-exposed episodes only | Explicitly conditioned on establishment observed | Failure onset to stable-window start; excludes censored episodes | Per-seed conditional means, then mean ± sample SD |
| RMST80 | \(\int_0^{80}\hat S_{est}(t)dt\) | Failure-exposed Early+Nominal risk population with one event/censor record per episode | No event-positive conditioning | Failure onset; censor at actual available follow-up (`final.step - failure_start_step`) | Seed-level RMST and paired contrasts; hierarchical paired bootstrap over seeds and matched episodes |
| RMST220 | Same restricted-mean construction with \(\tau=220\) | Same locked survival population and censoring rule | No event-positive conditioning | Same as RMST80 | Per-seed RMST, mean ± sample SD where reported; paired seed contrast where locked |
| Wilson95 (where present) | Wilson lower bound for establishment/recovery rate | Same denominator as the corresponding per-episode establishment rate | No time conditioning | Not a censoring estimator | Computed per seed and summarized across seeds |
| Terminal collision / timeout (where present) | Episodes with the terminal status | Usually all evaluation episodes, not the survival risk set | No establishment conditioning | Terminal environment state | Per-seed rate, then mean ± sample SD |

## Required table-note wording

Table 1 must state that establishment probability, Success, and conditional
`t_est` do not share one denominator. The conditional time is descriptive and
cannot replace KM/RMST. RMST80 is the pre-specified early-window comparison
between EA-RG and MAPPO; RMST220 is the full-follow-up restricted mean and is
not a universal-ranking metric.

The old word “Recovery” should be replaced by “Stable-chain establishment” in
the publication-facing table. If a legacy column is retained for provenance,
the table note must say that it is a relabelled locked event, not
post-disruption recovery.

## Denominator reconciliation

1. The apparent 10,800-versus-600 discrepancy is a scope difference, not a
   numerical conflict: 10,800 is the full held-out suite (four scenarios × 100
   episodes × 9 methods × 3 seeds), whereas the primary Early+Nominal survival
   subset contains 200 matched exposures per method and seed, i.e. 600 per
   method across three seeds. The final table and figure captions must state
   this distinction explicitly.
2. `Success` is reported beside failure-exposed establishment metrics but its
   exact evaluation population must be made explicit in the final table source.
3. RMST80/RMST220 are survival estimands from one event-or-censor record per
   episode; they must not be reconstructed from the rounded conditional-time
   column or from the legacy `Recovery` rate.

This audit is **PASS WITH DOCUMENTATION ACTION** for metric definitions. The
remaining action is to make the full-suite versus Early+Nominal subset explicit
in the publication table and figure notes; no author decision is required.
