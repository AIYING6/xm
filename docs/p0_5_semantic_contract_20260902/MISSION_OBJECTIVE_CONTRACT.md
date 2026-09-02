# Mission-objective contract

At a scale with `K = n_terminal` objectives, each objective has a spatially distinct target state and progress `p_k in [0,1]`. A Scout can acquire at most one fresh objective token per interval; a Terminal can advance at most one objective per interval. Any Scout may acquire any objective and any Terminal may execute any outstanding objective, provided it holds fresh, legal relay-forwarded support. This is workload redundancy rather than hidden specialization.

Mission success requires completion of all K objectives before the fixed physical deadline with valid support at each terminal completion. The deadline is selected by future scripted physical-feasibility tests, not learner score. Small/main/large therefore have 1/2/3 objectives respectively; this is the same capacity rule, not three hand-written tasks.
