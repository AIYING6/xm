# 5. Experimental Setup

## 5.1 Contracts and strata

The clean T1 UTR reference uses five 1M seeds (2201–2205). DRTP development uses seeds 1901 and 1902 at the frozen 3M endpoint. Held-out confirmation uses seeds 2001–2003 at the frozen 10M endpoint. These strata are reported separately because their budgets, tapes, and purposes differ. No canonical seeds are used in this paper-convergence stage.

## 5.2 Baselines and fairness

UTR and DRTP share the SG backbone, PPO, reward, S2 environment, seven groups, nominal anchor, seed policy, final-checkpoint rule, and evaluation aggregation. Their only intended method difference is fixed versus adaptive group weighting. Legacy EA-RG recovery and Gate1 tables are excluded because their estimands and contracts differ.

## 5.3 Mandatory main-paper ablation

The primary ablation is `UTR-SG-MAPPO vs DRTP-SG-MAPPO`. It is a causal design comparison, not a supplementary-only baseline: the two methods have identical SG architecture and parameter count (116,728), PPO and critic, seven topology-condition groups, 50% nominal anchor, training budget, and evaluation protocol. The only intended difference is uniform perturbation weighting versus adaptive DRTP weighting. Every seed is retained, including weak or reversed outcomes, and the interpretation uses paired effect sizes, win counts, medians, and worst degradation; no universal-benefit or seed-stability claim is permitted.

## 5.4 Metrics

Primary metrics are `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and timeout. Secondary metrics are nominal score, collision, constraint violation, exposure, survival to onset, risk-set trigger validity, path switching, task-support availability, and maneuver/control burden. Training seed is the independent statistical unit. All planned episodes remain in unconditional return and safety summaries.

## 5.5 Statistical reporting

Every seed is shown. We report paired DRTP−UTR differences, win count, mean, median, standard deviation, IQR/MAD, worst degradation, and descriptive seed-level intervals where defensible. Five seeds are not treated as a basis for universal or seed-stable claims.
