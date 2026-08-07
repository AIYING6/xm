# Efficiency Phase-3 Formal Audit

- generated: 2026-08-07 12:11:06
- hardware: NVIDIA GeForce GTX 1650 Ti / driver 580.97 / CUDA 12.4 / torch 2.4.1+cu124 / FP32 eager
- methods: 5/5
- OVERALL: PASS

## 4.1 Parameters

- full_ea_rg: 117,302 params, 74 tensors, 489.8 KB, sha B9FECBE9ACC3...
- w_o_role_pair_gate: 117,302 params, 74 tensors, 489.8 KB, sha B9FBB2E91D62...
- mappo: 15,708 params, 12 tensors, 66.2 KB, sha C99A5718F4C0...
- happo: 107,313 params, 84 tensors, 450.1 KB, sha 1219F17D5201...
- param_matched_single: 84,694 params, 34 tensors, 343.7 KB, sha C7CDEB2F29D3...

## 4.2A Architecture-only latency (ms, warmup=200 measure=1000 repeats=10)

- full_ea_rg batch1: mean 12.049 (median 10.675, P95 19.129, P99 30.434) => 83 joint-decisions/s
- full_ea_rg batch8: mean 11.373 (median 10.101, P95 17.445, P99 25.210) => 88 joint-decisions/s
- w_o_role_pair_gate batch1: mean 9.771 (median 9.098, P95 13.488, P99 15.093) => 102 joint-decisions/s
- w_o_role_pair_gate batch8: mean 10.566 (median 9.729, P95 15.134, P99 18.825) => 95 joint-decisions/s
- mappo batch1: mean 2.118 (median 1.744, P95 3.949, P99 6.751) => 472 joint-decisions/s
- mappo batch8: mean 2.079 (median 1.721, P95 3.687, P99 6.123) => 481 joint-decisions/s
- happo batch1: mean 8.583 (median 7.720, P95 13.040, P99 18.045) => 117 joint-decisions/s
- happo batch8: mean 7.895 (median 7.036, P95 11.537, P99 14.829) => 127 joint-decisions/s
- param_matched_single batch1: mean 4.536 (median 4.215, P95 6.847, P99 9.091) => 220 joint-decisions/s
- param_matched_single batch8: mean 3.899 (median 3.577, P95 5.354, P99 6.709) => 256 joint-decisions/s

## 4.3 End-to-end throughput (8 envs x 128)

- full_ea_rg: 242 env-steps/s, 41329 ms / 10k env-steps
- w_o_role_pair_gate: 201 env-steps/s, 49865 ms / 10k env-steps
- mappo: 311 env-steps/s, 32156 ms / 10k env-steps
- happo: 275 env-steps/s, 36397 ms / 10k env-steps
- param_matched_single: 332 env-steps/s, 30151 ms / 10k env-steps

## 4.4 Memory (peak MB)

- inference full_ea_rg batch1: allocated 10.1 / reserved 23.1
- inference full_ea_rg batch8: allocated 10.2 / reserved 23.1
- training full_ea_rg batch: allocated 71.9 / reserved 79.7
- inference w_o_role_pair_gate batch1: allocated 18.6 / reserved 79.7
- inference w_o_role_pair_gate batch8: allocated 18.7 / reserved 50.3
- training w_o_role_pair_gate batch: allocated 66.2 / reserved 73.4
- inference mappo batch1: allocated 18.2 / reserved 73.4
- inference mappo batch8: allocated 18.2 / reserved 54.5
- training mappo batch: allocated 20.9 / reserved 54.5
- inference happo batch1: allocated 18.6 / reserved 54.5
- inference happo batch8: allocated 18.6 / reserved 48.2
- training happo batch: allocated 24.6 / reserved 50.3
- inference param_matched_single batch1: allocated 18.4 / reserved 50.3
- inference param_matched_single batch8: allocated 18.5 / reserved 46.1
- training param_matched_single batch: allocated 38.0 / reserved 54.5

## 4.5 Communication (shared fixed-action trajectory)

Fixed pseudo-random action sequence shared by ALL methods; communication cost is therefore decoupled from policy behavior and the RPG on/off comparison is exact (protocol 4.5/5).

- full_ea_rg: candidate 4.74/step, physical 1.74/step, in-flight msgs 3.43/step
- w_o_role_pair_gate: candidate 4.74/step, physical 1.74/step, in-flight msgs 3.43/step
- mappo: candidate 4.74/step, physical 1.74/step, in-flight msgs 3.43/step
- happo: candidate 4.74/step, physical 1.74/step, in-flight msgs 3.43/step
- param_matched_single: candidate 4.74/step, physical 1.74/step, in-flight msgs 3.43/step

## OVERALL: PASS