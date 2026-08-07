# Efficiency Results Lock — v1.5.0

- lock tag: `formal-efficiency-results-lock-v1.5.0`
- locked at: 2026-08-07 12:11:06 (audit generation time)
- status: **FROZEN — do not re-run, re-profile, or re-tune without a new pre-registered protocol**

## Protocol freeze

- protocol: `FORMAL_EFFICIENCY_PROTOCOL_V1_5` (docs/FORMAL_EFFICIENCY_PROTOCOL_V1_5.md)
- protocol tag: `efficiency-protocol-freeze-v1.5.0`

## Efficiency eval ops

- ops tag: `efficiency-eval-ops-v1.5.0`
- entrypoints:
  - `_operator_scripts/run_efficiency_v1_5.py` (formal profiling, phase 3)
  - `_operator_scripts/run_efficiency_smoke_v1_5.py` (phase-2 smoke)
  - `_operator_scripts/efficiency_profiler.py` (timing / memory / comm helpers)
- frozen budgets: warmup=200, measure=1000, repeats=10, batch sizes=1,8;
  e2e 8 envs x 128 steps; comm 3 episodes x 200 steps (fixed pseudo-random action
  trajectory, rng_seed=20260807); training memory = exactly 1 PPO update.

## Hardware snapshot

| field | value |
|---|---|
| gpu | NVIDIA GeForce GTX 1650 Ti |
| gpu_memory_total | 4096 MiB |
| driver | 580.97 |
| cuda | 12.4 |
| torch | 2.4.1+cu124 |
| precision | FP32 eager (tf32 matmul off, tf32 cudnn on) |
| compile | false |
| cpu | Intel64 Family 6 Model 165 Stepping 2 |
| platform | Windows-10-10.0.22631-SP0 |

## 5 locked checkpoints

| method | checkpoint sha256 | params | tensors | KB |
|---|---|---|---|---|
| full_ea_rg | B9FECBE9ACC3A7CB7306F80338DA8116E54D86A71292A3AA188D6378EF75A82A | 117302 | 74 | 489.8 |
| w_o_role_pair_gate | B9FBB2E91D628DAA8467A177BA5D77D8AD0D3A1C3CA8A8CB99011AC12A6D28FF | 117302 | 74 | 489.8 |
| mappo | C99A5718F4C09FC22054E3900F7199A9AE4A3A6060A24C45FBAEFC73C66EE0F0 | 15708 | 12 | 66.2 |
| happo | 1219F17D520131D6567D653A207CEDA445E9EE5010E50A6E3288356B1741AC0E | 107313 | 84 | 450.1 |
| param_matched_single | C7CDEB2F29D33C403CE88F6DF922558FEF51CCE36B77907C9EFAACD6FEBF7D87 | 84694 | 34 | 343.7 |

## Raw latency SHA

`efficiency_evidence_manifest.json` -> `raw_latency_sample_sha256` (per method, per batch):

| method | batch 1 | batch 8 |
|---|---|---|
| full_ea_rg | d9dce2ca8b44a9a6 | a6c07eb6a6f5a469 |
| w_o_role_pair_gate | 7815e180f1f935dc | 9fe005240f6659db |
| mappo | 621560bbec9847f4 | f23e1484e670cb8a |
| happo | 5efad430e0e2dfb6 | d607b4df96566e6e |
| param_matched_single | c8dc7a85c30daece | b3c6009485ddbe22 |

## Communication profiling SHA

`efficiency_outputs_sha256.txt`:

- efficiency_communication.csv: `D1B4481458452F17FBB6E1D023E40DE098D57243BDD630F921C8FD2E17785B5B`

RPG on/off message invariance: Full == w_o_role_pair_gate exactly
(candidate 4.735/step, physical 1.735/step, in-flight 3.428/step, payload 24.0
scalars/step incl. meta 37.7). Communication cost is decoupled from policy
behavior by construction (shared fixed-action trajectory).

## Overall

- OVERALL: **PASS**
- problems: none
- 8 audit artifacts + this lock note written atomically at 12:11:06;
  full artifact SHA list in `efficiency_outputs_sha256.txt`.

## Interpretive guardrail (paper)

Efficiency results do NOT support "Full is computationally cheaper". Full is
slower per joint decision (12.05 ms @batch1 vs HAPPO 8.58 / param-matched 4.54 /
MAPPO 2.12), lower e2e throughput (242 vs 332/311/275 env-steps/s) and highest
training peak memory (71.9 MB). Its advantage is task-level (fewer env steps to
complete, faster recovery) — i.e. algorithmic/task efficiency, not computational
efficiency. The paper MUST distinguish these two notions explicitly.
