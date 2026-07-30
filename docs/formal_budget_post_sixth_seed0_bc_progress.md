# Formal Budget Post-Sixth BC Progress

Last updated: 2026-07-30

## Purpose

This records the first formal-budget initialization outputs after the
post-sixth-review protocol freeze. These BC checkpoints are formal initialization
artifacts for the later 1M PPO budget study, not final performance evidence.

Output root:

```text
results/paper_config_runs/formal_budget_post_sixth_freeze/
```

## Completed

Seeds `0`, `1`, and `2` BC completed for all five formal method families. The
formal BC stage is now `15/15` complete.

| Seed | Method | Epochs | Final loss | Action acc | Attacker acc | Support acc | Demo success |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | no_graph | 20 | 1.0698 | 0.4915 | 0.4476 | 0.5134 | 0.9083 |
| 0 | single_graph | 20 | 1.0136 | 0.5037 | 0.4620 | 0.5246 | 0.9083 |
| 0 | param_matched_single | 20 | 0.9273 | 0.5167 | 0.4747 | 0.5377 | 0.9083 |
| 0 | ea_rg_mappo_s_gate_prior | 20 | 0.8791 | 0.5088 | 0.4660 | 0.5302 | 0.9083 |
| 0 | happo | 20 | 1.4505 | 0.4868 | 0.4497 | 0.5053 | 0.9083 |
| 1 | no_graph | 20 | 1.0733 | 0.5004 | 0.4347 | 0.5333 | 0.9083 |
| 1 | single_graph | 20 | 1.0569 | 0.4868 | 0.4355 | 0.5125 | 0.9083 |
| 1 | param_matched_single | 20 | 0.8830 | 0.5263 | 0.4687 | 0.5551 | 0.9083 |
| 1 | ea_rg_mappo_s_gate_prior | 20 | 0.9151 | 0.5012 | 0.4741 | 0.5148 | 0.9083 |
| 1 | happo | 20 | 1.4661 | 0.4853 | 0.4300 | 0.5130 | 0.9083 |
| 2 | no_graph | 20 | 1.0316 | 0.5119 | 0.4540 | 0.5408 | 0.9167 |
| 2 | single_graph | 20 | 1.0294 | 0.4898 | 0.4581 | 0.5057 | 0.9167 |
| 2 | param_matched_single | 20 | 0.9236 | 0.5198 | 0.4580 | 0.5508 | 0.9167 |
| 2 | ea_rg_mappo_s_gate_prior | 20 | 0.9528 | 0.5049 | 0.4714 | 0.5216 | 0.9167 |
| 2 | happo | 20 | 1.4719 | 0.4802 | 0.4353 | 0.5027 | 0.9167 |

Expected checkpoint files exist:

- RI-GMAPPO-family methods: `actor_critic_latest.pt` and `actor_critic_best.pt`;
- HAPPO: `happo_bc_latest.pt` and `happo_bc_best.pt`.

## Interpretation

The BC stage is executable under the final zero-mask actor information boundary.
The comparable demo success rate across all five methods confirms that the
formal initialization data protocol is shared.

These metrics should not be interpreted as method performance. They only verify
that seeds `0`, `1`, and `2` initialization are ready for the 1M PPO budget
stage.

## Next

1. Start the 1M PPO budget study, `977` updates, for seeds `0 1 2`.
2. Run suite-level validation checkpoint sweep after 1M completes.
3. Decide whether 2M is necessary before expanding to five formal seeds.
