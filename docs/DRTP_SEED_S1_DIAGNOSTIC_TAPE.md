# DRTP-SEED-S1 Diagnostic Tape

Status: `FROZEN — DEVELOPMENT DIAGNOSTIC ONLY`

Namespace: `440000–440099`.

The tape is separate from historical 340k/350k/360k/370k/380k/410k/420k/430k namespaces and is not eligible for held-out or canonical evidence. It contains 100 shared episode IDs for each condition:

| Condition | Failure onset | Duration |
|---|---:|---:|
| nominal | — | — |
| F0 | 44 | 80 |
| timing | 28 | 80 |
| duration | 44 | 40 |
| compound | 60 | 120 |

All methods and interventions use the same episode IDs and condition definitions. Relay failure semantics remain the frozen S2 node-failure event. The manifest hash is recorded in `artifacts/drtp_seed_s1/rng_manifest.json` after tape materialization.

