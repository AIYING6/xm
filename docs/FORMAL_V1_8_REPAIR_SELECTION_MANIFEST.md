# FORMAL_V1_8_REPAIR_SELECTION_MANIFEST

**Status: checkpoint selection completed from training-time immutable artifacts only.**
No confirmatory held-out evaluation was accessed.

| method | seed | selected update | checkpoint SHA256 | RMST80 | establishment | censoring | RMST220 |
|---|---:|---:|---|---:|---:|---:|---:|
| corrected_ea_rg | 0 | 300 | `edd4383b843c55892a230dae35f913e413d4ff2e17eb7b140d2c3de655182c24` | 80 | 0.1 | 0.9 | 208.35 |
| corrected_ea_rg | 1 | 1 | `ecb9a9b7ca32238d7b1b437314f076a146e7825260c8284e45ec2f40614bc144` | 80 | 0 | 1 | 220 |
| corrected_ea_rg | 2 | 270 | `68e41177e278581c50937c2bea59a3f4e4e6c8b3cf20d2c12d67bab69c74c40b` | 80 | 0.1 | 0.9 | 214.1 |
| corrected_wider_single_graph | 0 | 230 | `8e68459043718b67da72850d08419367e6c6dd14d994ae2e5186adba512ea18e` | 80 | 0.7 | 0.3 | 172.5 |
| corrected_wider_single_graph | 1 | 240 | `58cd1a49bcfa762e5eb5b09aad1f22e0f4d401f4f83ff17912d95006bdb25328` | 80 | 0.2 | 0.8 | 204.75 |
| corrected_wider_single_graph | 2 | 90 | `fa4544c2048424b89ecee580d136932e18375f43de7001cfa328343a23eaf0c8` | 79.8 | 0.05 | 0.95 | 212.8 |
| matched_information_nongraph | 0 | 1 | `0a76d954b95729970a7fdff33a86262211e0661d370237ba391f779b9e960fc4` | 80 | 0 | 1 | 220 |
| matched_information_nongraph | 1 | 300 | `3a1efe42e3dfdccdac65ad7cd93f4a6b2f38f524a290969c72567a2f2149b3e9` | 79.7 | 0.25 | 0.75 | 197.35 |
| matched_information_nongraph | 2 | 280 | `2c9bbb89968adb37efa10c502b662881ededc70a5efc0f75f8cef41df87bf33d` | 71.85 | 0.3 | 0.7 | 169.85 |

Each selected artifact was SHA256-verified against its append-only run manifest;
method, seed, update, and protocol provenance were verified before applying the
frozen selector: lower RMST80, higher establishment probability, lower censoring,
lower RMST220, then earlier update on exact ties.

```json
[
  {
    "censoring_rate": 0.9,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\ea_rg_seed0\\actor_critic_update_0300.pt",
    "checkpoint_sha256": "edd4383b843c55892a230dae35f913e413d4ff2e17eb7b140d2c3de655182c24",
    "establishment_probability": 0.1,
    "method": "corrected_ea_rg",
    "rmst220": 208.35,
    "rmst80": 80.0,
    "seed": 0,
    "selected_update": 300
  },
  {
    "censoring_rate": 1.0,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\ea_rg_seed1\\actor_critic_update_0001.pt",
    "checkpoint_sha256": "ecb9a9b7ca32238d7b1b437314f076a146e7825260c8284e45ec2f40614bc144",
    "establishment_probability": 0.0,
    "method": "corrected_ea_rg",
    "rmst220": 220.0,
    "rmst80": 80.0,
    "seed": 1,
    "selected_update": 1
  },
  {
    "censoring_rate": 0.9,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\ea_rg_seed2\\actor_critic_update_0270.pt",
    "checkpoint_sha256": "68e41177e278581c50937c2bea59a3f4e4e6c8b3cf20d2c12d67bab69c74c40b",
    "establishment_probability": 0.1,
    "method": "corrected_ea_rg",
    "rmst220": 214.1,
    "rmst80": 80.0,
    "seed": 2,
    "selected_update": 270
  },
  {
    "censoring_rate": 0.30000000000000004,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\single_seed0\\actor_critic_update_0230.pt",
    "checkpoint_sha256": "8e68459043718b67da72850d08419367e6c6dd14d994ae2e5186adba512ea18e",
    "establishment_probability": 0.7,
    "method": "corrected_wider_single_graph",
    "rmst220": 172.50000000000003,
    "rmst80": 80.0,
    "seed": 0,
    "selected_update": 230
  },
  {
    "censoring_rate": 0.8,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\single_seed1\\actor_critic_update_0240.pt",
    "checkpoint_sha256": "58cd1a49bcfa762e5eb5b09aad1f22e0f4d401f4f83ff17912d95006bdb25328",
    "establishment_probability": 0.2,
    "method": "corrected_wider_single_graph",
    "rmst220": 204.74999999999997,
    "rmst80": 80.0,
    "seed": 1,
    "selected_update": 240
  },
  {
    "censoring_rate": 0.95,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\single_seed2\\actor_critic_update_0090.pt",
    "checkpoint_sha256": "fa4544c2048424b89ecee580d136932e18375f43de7001cfa328343a23eaf0c8",
    "establishment_probability": 0.05,
    "method": "corrected_wider_single_graph",
    "rmst220": 212.79999999999998,
    "rmst80": 79.8,
    "seed": 2,
    "selected_update": 90
  },
  {
    "censoring_rate": 1.0,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\matched_nongraph_seed0\\actor_critic_update_0001.pt",
    "checkpoint_sha256": "0a76d954b95729970a7fdff33a86262211e0661d370237ba391f779b9e960fc4",
    "establishment_probability": 0.0,
    "method": "matched_information_nongraph",
    "rmst220": 220.0,
    "rmst80": 80.0,
    "seed": 0,
    "selected_update": 1
  },
  {
    "censoring_rate": 0.75,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\matched_nongraph_seed1\\actor_critic_update_0300.pt",
    "checkpoint_sha256": "3a1efe42e3dfdccdac65ad7cd93f4a6b2f38f524a290969c72567a2f2149b3e9",
    "establishment_probability": 0.25,
    "method": "matched_information_nongraph",
    "rmst220": 197.34999999999997,
    "rmst80": 79.7,
    "seed": 1,
    "selected_update": 300
  },
  {
    "censoring_rate": 0.7,
    "checkpoint_path": "D:\\Code\\Codex\\ri_gmappo_uav_scientific_reframe_v1_7\\results\\formal_v1_8_repair\\matched_nongraph_seed2\\actor_critic_update_0280.pt",
    "checkpoint_sha256": "2c9bbb89968adb37efa10c502b662881ededc70a5efc0f75f8cef41df87bf33d",
    "establishment_probability": 0.3,
    "method": "matched_information_nongraph",
    "rmst220": 169.84999999999997,
    "rmst80": 71.85,
    "seed": 2,
    "selected_update": 280
  }
]
```
