# KLR Final Replication: frozen P0 contract

This is a one-time independent replication challenge for the exact historical **Full-Rollback KLR**, not a KLR-v2 proposal. The historical three-seed pilot remains `PILOT_NO_GO`; this contract does not revise that result.

The candidate is Original DRTP plus a post-step actor full rollback at empirical KL `0.02`. On rejection, it restores actor parameters and actor Adam slots, retains the critic step, and stops remaining PPO epochs for that rollout. It does not add a sampler bound, anchor, probe, confidence gate, PPO retuning, network change, or reward change.

If future training is separately authorized, it will run `UTR / Original DRTP / Full-Rollback KLR` on Cohort A seeds 3701--3705 and Cohort B seeds 3706--3710, exactly 499,968 environment steps per trajectory. The cohorts are independent and are never pooled for the decision.

At 0.5M, each cohort must independently retain mean `J_pert_mean` within `epsilon_J = 7.874919837916801`, improve its worst paired seed by at least that frozen downside margin, not increase catastrophic seeds, reduce both range and sample SD, preserve the upper tail, and not worsen safety. One failing cohort permanently closes KLR; no KLR-v2, tuning, rerun, or continuation is authorized.

P0 is zero-training and zero-checkpoint-evaluation only. It cannot authorize cloud training.
