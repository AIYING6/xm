# Reward semantic contract

With K objectives, `p_bar(t) = (1/K) sum_k p_k(t)`, `r_progress = p_bar(t+1)-p_bar(t)`, and `r_complete = newly_completed/K`. The frozen skeleton is `r = w_p*r_progress + w_s*r_complete - w_c*C_pair - w_b*boundary_cost`. Weights are physical design constants to be justified by units/ranges before P1 and may not be tuned from RL performance.

The default is a shared team reward. If role shaping becomes necessary, it is averaged within each role before addition. No direct reward is granted for topology redundancy, number of paths or severity.
