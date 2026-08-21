# T7 — Offline Calibration Evidence

## Asset and legality audit

The read-only analysis used the same frozen T1 final 1M UTR-SG checkpoints as
T6: seeds 2201–2205, each with 116,728 parameters, and 3,600 balanced frozen
samples per seed. It constructed no environment, executed no rollout, updated
no optimizer, and used no privileged actor input. The machine-readable output
is `results/development/t7_calibration_premise_run1/t7_calibration_premise.json`.

## Pre-registered calibration hypothesis

If legal support quality `q` were an executable calibration reference, the
counterfactual policy sensitivity `S` should be higher at high than low `q`
after strict recorded-state matching, and the effect should be more pronounced
in GOOD than WEAK policies across F0, timing, and duration. The audit fixed
low `q<=0.40`, high `q>=0.60`, and retained only matched cells with family,
phase, progress, topology label, expected-action-norm bin, and direct-target
visibility equal.

## Five required tests

| Test | Frozen criterion | Outcome |
|---|---|---|
| 1. State-conditional structure | Both GOOD seeds have positive matched high-minus-low gap | PASS |
| 2. Seed ordering | GOOD exceeds WEAK and intermediate is not weak-like | FAIL |
| 3. Cross-condition | GOOD-minus-WEAK positive in F0, timing, duration | FAIL |
| 4. Transition relevance | GOOD early effect no smaller than pre effect | FAIL: no matched pre/early cells |
| 5. Matching feasibility | Every seed has a valid matched comparison | PASS |

## Key quantities

Raw, unmatched high-minus-low sensitivity was positive in all seeds: 2201
`+0.2029`, 2202 `+0.1573`, 2203 `+0.0619`, 2204 `+0.0564`, and 2205
`+0.1300`. This superficial monotonicity is not sufficient.

After fixed matching, the effects are: 2201 `-0.0398` (one cell), 2202
`+0.0383` (seven), 2203 `+0.0533` (four), 2204 `+0.1317` (three), and 2205
`+0.0715` (two). Thus the intermediate seed is negative, both weak seeds are
positive, and the GOOD ordering is not retained.

Condition-level GOOD-minus-WEAK differences are F0 unavailable because no weak
matched comparison exists, timing `-0.0344`, duration `+0.0271`. F0 has two
cells, timing seven, duration eight. The required common direction is absent.

## Interpretation

T6's A/C findings remain valid: GOOD policies show stronger broad support use
and support-state action separation. T7 shows that those findings do **not**
identify a support-quality-to-sensitivity calibration curve. This distinction
prevents turning an exploratory group difference into an arbitrary training
set point. The offline premise is therefore **FAIL**.
