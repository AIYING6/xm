# Safety and metric contract

At N UAVs, `C_t = sum_{i<j} 1[d_ij < d_safe] / choose(N,2)` and `C_pair = mean_t C_t`; also report `C_any`, the episode any-collision indicator. Timeout is an unmet all-objective deadline under the scale's frozen physical time budget. Task-path availability is the fraction of Scout--Terminal pairs with a fresh legal route; residual redundancy is current route count divided by nominal route count, averaged over pairs. All-pairs radio closure is never the main communication metric.
