# 5. Experimental Setup

## 5.1 Contracts and strata

The clean T1 UTR reference uses five 1M seeds (2201–2205). DRTP development uses seeds 1901 and 1902 at the frozen 3M endpoint. Held-out confirmation uses seeds 2001–2003 at the frozen 10M endpoint. These strata are reported separately because their budgets, tapes, and purposes differ. No canonical seeds are used in this paper-convergence stage.

| Stratum | Methods/seeds | Budget | Purpose | Reporting rule |
|---|---|---:|---|---|
| T1 reference | UTR, 2201–2205 | 1M | clean matched reference | descriptive reference only |
| DRTP development | UTR/DRTP, 1901–1902 | 3M | method-development evidence | retain historical NO-GO |
| DRTP held-out | UTR/DRTP, 2001–2003 | 10M | confirmation evidence | retain held-out FAIL and seed2002 reversal |

Development and held-out rows are never silently pooled. Every reported number should be traceable to method, seed, budget, tape/condition, final-checkpoint rule, and aggregation source.

## 5.2 Baselines and fairness

UTR and DRTP share the SG backbone, PPO, reward, S2 environment, seven groups, nominal anchor, seed policy, final-checkpoint rule, and evaluation aggregation. Their only intended method difference is fixed versus adaptive group weighting. Legacy EA-RG recovery and Gate1 tables are excluded because their estimands and contracts differ.

## 5.3 Mandatory main-paper ablation

The primary ablation is `UTR-SG-MAPPO vs DRTP-SG-MAPPO`. It is a causal design comparison, not a supplementary-only baseline: the two methods have identical SG architecture and parameter count (116,728), PPO and critic, seven topology-condition groups, 50% nominal anchor, training budget, and evaluation protocol. The only intended difference is uniform perturbation weighting versus adaptive DRTP weighting. Every seed is retained, including weak or reversed outcomes, and the interpretation uses paired effect sizes, win counts, medians, and worst degradation; no universal-benefit or seed-stability claim is permitted.

## 5.4 Metrics

Primary metrics are `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and timeout. Secondary metrics are nominal score, collision, constraint violation, exposure, survival to onset, risk-set trigger validity, path switching, task-support availability, and maneuver/control burden. Training seed is the independent statistical unit. All planned episodes remain in unconditional return and safety summaries.

| Metric | Definition | Preferred direction | Interpretation |
|---|---|---|---|
| `J_nominal` | nominal mission score | higher | competence anchor |
| `J_F0` | canonical relay-failure score | higher | in-contract failure robustness |
| `J_OOD_mean` | mean over timing/duration/compound conditions | higher | average perturbation robustness |
| `J_OOD_worst` | worst condition score | higher | tail-condition diagnostic |
| `Delta_J` | `J_nominal-J_failure` | lower | degradation, reported with absolute scores |
| timeout/collision/constraint | episode-level safety/termination rates | lower | safety and mission completion cost |
| survival-to-onset | fraction alive immediately before scheduled onset | higher, interpreted jointly | policy safety before trigger |
| risk-set trigger validity | trigger success conditional on survival to onset | higher | evaluator/trigger validity |
| exposure | failure exposure recorded under the contract | descriptive | never used to delete pre-trigger episodes |

For the conditional trigger-validity metric, the risk set is `R={episodes alive immediately before scheduled onset}` and the estimate is `correctly triggered failures/|R|`. Pre-trigger collision remains in overall returns and safety rates.

## 5.5 Statistical reporting

Every seed is shown. We report paired DRTP−UTR differences, win count, mean, median, standard deviation, IQR/MAD, worst degradation, and descriptive seed-level intervals where defensible. Five seeds are not treated as a basis for universal or seed-stable claims.

The main ablation is paired by training seed. Pooled episodes are used to estimate contract-level descriptive means, not as independent training replicates. Because the available paired sample is small, the manuscript emphasizes effect direction, median, dispersion, worst paired degradation, and absolute safety rather than relying on a single pooled significance test. Any future inferential test must declare its family, pairing unit, and multiplicity correction before reading the result.

## 5.6 Evaluation and reproducibility checklist

Before a number enters a table, the corresponding artifact must have: a frozen tape manifest and hash; complete raw records; final-checkpoint hash; method/seed/budget manifest; exposure and trigger-validity fields; and an aggregation script that refuses missing or duplicate records. This checklist follows the reference manuscript's protocol-before-conclusion principle and is implemented by the repository evidence ledger.
