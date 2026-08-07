# Table 4 — Efficiency (locked, n=1 profile)

| method | params | joint decision ms | joint decisions/s | e2e env-steps/s | train peak mem (MB) |
|---|---|---|---|---|---|
| full_ea_rg | 117302 | 12.05 | 83 | 242.0 | 71.9 |
| w_o_role_pair_gate | 117302 | 9.77 | 102 | 200.5 | 66.2 |
| mappo | 15708 | 2.12 | 472 | 311.0 | 20.9 |
| happo | 107313 | 8.58 | 117 | 274.7 | 24.6 |
| param_matched_single | 84694 | 4.54 | 220 | 331.7 | 38.0 |