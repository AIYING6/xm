# Topology structural-score audit

**Status:** policy-free schedule quantities are reproducible; a group-discriminative topology score is **not** established.

All six failure groups set `failed_blue_agent = 1`, i.e. delete the same Relay role. Removing that role from the static Scout–Relay–Attacker support graph removes the same role-compatible edges in every group. The only policy-independent quantity that differs in the frozen group contract is failure timing/duration.

| Group | Frozen members | Mean duration | Scheduled Relay-unavailable fraction | Static deletion |
| --- | --- | --- | --- | --- |
| F0 | f0 | 80.0 | 0.307692 | identical |
| TE | te_28_80, te_36_80 | 80.0 | 0.307692 | identical |
| TL | tl_52_80, tl_60_80 | 80.0 | 0.307692 | identical |
| DS | ds_44_40, ds_44_60 | 50.0 | 0.192308 | identical |
| DL | dl_44_100, dl_44_120 | 110.0 | 0.423077 | identical |
| CP | cp_28_120, cp_60_120 | 120.0 | 0.461538 | identical |

Actual communication reachability is state-dependent (inter-agent distance and stochastic communication dropout). Active support additionally depends on target information and local attack-window state. These quantities cannot be used as a fixed prior here: evaluating them would require a trajectory and hence policy/RNG-dependent rollout.

The hash of the policy-free schedule calculation is `aed4593590aa6398b9ab01796b78ec560f46275e131008c8d2cbc46d8fa01950`.
