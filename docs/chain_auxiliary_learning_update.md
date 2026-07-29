# Chain Auxiliary Learning Update

Last updated: 2026-07-28

## Motivation

The dev-1M results show that EA-RG-MAPPO is stronger than HAPPO and often
stronger than MAPPO/no-graph, but its advantage over Single-Graph MAPPO is not
stable enough for the final paper claim.

The likely weakness is not only scenario difficulty. In the 3DOF task, the
existing intent head is disabled because there is no target-intent supervision.
Therefore the actor graph encoder receives no explicit auxiliary signal to
represent kill-chain recovery states.

## Implemented Change

Added an optional actor-side kill-chain auxiliary head to
`algorithms/ri_gmappo/simple_ri_gmappo.py`.

The auxiliary head predicts five graph-observable chain-state labels:

- `perception_active`;
- `communication_connected`;
- `task_support_active`;
- `attack_window_active`;
- `fresh_message_available`.

The labels are built from the current actor graph observation:

- `relation_adj`;
- `node_feat`;
- `edge_feat`.

The auxiliary loss does not use held-out test outcomes, episode success labels,
or global attack-hold progress. It is a training-only representation signal.

## Interface

New training argument:

```text
--chain-aux-coef
--chain-aux-warmup-updates
```

Default value is `0.0`, so existing training commands keep their original
behavior unless the coefficient is explicitly enabled.

New training-log fields:

- `chain_aux_loss`;
- `chain_aux_acc`.
- `chain_aux_effective_coef`.

New paper config:

```text
configs/paper/ea_rg_mappo_chain_aux.yaml
```

The command generator now passes `--chain-aux-coef` only to RI-GMAPPO/MAPPO-family
training scripts, not to HAPPO.

## Verification

Completed checks:

- `scripts/train_ri_gmappo.py --help` exposes `--chain-aux-coef`;
- `scripts/train_ri_gmappo.py --help` exposes `--chain-aux-warmup-updates`;
- 1-update 3DOF EA-RG-MAPPO chain-aux smoke passed;
- 1-update warm-up smoke passed with `chain_aux_effective_coef=0.0`;
- Gate 1 actor information-boundary tests passed: `24 passed`.

Smoke output directory:

```text
results/paper_config_runs/smoke/ea_rg_mappo_chain_aux_smoke/
```

## Required Experiments

This change must not be claimed as a final improvement until it is compared
fairly against the original EA-RG-MAPPO under the same protocol.

Minimum next experiments:

1. EA-RG-MAPPO original, 1M, seeds 0/1/2.
2. EA-RG-MAPPO + Chain Auxiliary, 1M, seeds 0/1/2. The current candidate is
   `chain_aux_coef=0.02` with `chain_aux_warmup_updates=20`.
3. Same validation checkpoint selection and held-out test.
4. Report whether the auxiliary head improves:
   - mean recovery rate;
   - worst-seed recovery rate;
   - recovery time;
   - training stability.

If the auxiliary version does not improve EA over Single-Graph MAPPO, the final
paper claim must remain conservative.
