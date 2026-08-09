# P0-A Terminal-Outcome Estimand Freeze

**Status: `P0_A_TERMINAL_OUTCOME_ESTIMAND_FROZEN__P0_A_REPAIR_AUTHORIZED__D2_NOT_AUTHORIZED`.**

## Target event and complete-follow-up outcomes

The target event is the first stable task-chain establishment after relay-failure
onset. For an episode with event time `T_E`, terminal failure before
establishment (`collision`, `constraint_violation`, and any future audited
irreversible mission-terminal outcome) is represented as `T_E = infinity` for
this restricted endpoint. An episode that remains active without establishment
by the restriction horizon also contributes the restriction horizon.

For `tau in {80, 220}`, the primary endpoint is:

`RMTE_tau = E[min(T_E, tau)]`.

Lower RMTE is favorable. Establishment at 20 contributes 20; terminal failure
at 20 and active non-establishment at tau=80 each contribute 80. The historical
name `RMST80/RMST220` may remain in archival paths only; v1.9 repaired reports
must call the endpoint *restricted mean time to establishment* (RMTE).

All simulator episodes are fully observed through establishment, a terminal
outcome, or their fixed horizon. Therefore the establishment curve is the
empirical cumulative incidence, not a Kaplan--Meier curve that censors terminal
failures. If future protocols introduce genuine random/administrative loss to
follow-up before the fixed horizon, they must pre-specify an Aalen--Johansen CIF
implementation before use.

## Frozen outcome decomposition

At each horizon report mutually exclusive proportions:

1. establishment by tau;
2. terminal failure before establishment by tau; and
3. active but not established at tau.

The fixed horizon is a restriction horizon, not a primary "censoring rate".
`eval_censoring_rate` is removed from repaired selector and primary reporting.

## Frozen selector

For a validation update, lower is selected lexicographically by:

1. RMTE80;
2. negative establishment probability at 80 (therefore higher is better);
3. terminal-failure incidence at 80;
4. RMTE220;
5. earlier update.

For a PCRF--single comparison, `Delta RMTE80 = RMTE80_PCRF - RMTE80_Single`;
negative values favor PCRF.

## Requalification rule

The historical D1-R2 run remains an engineering audit trail but cannot qualify
the repaired event-record/selector pipeline. The repair requires deterministic
RMTE/CIF/selector regressions, the existing D0 regressions, and a fresh six-run
D1 engineering requalification using non-evidentiary seeds 9301/9302. D2, F1,
F2, performance claims, mechanism experiments, and OOD remain prohibited.
