# Consistency Audit v1.5 — paper_latex_3d_en vs locked evidence

- audited: 2026-08-07
- scope: mechanism_fact / experiment_claim / number_scope / contribution_level
- severity: P0=factual error vs locked evidence, P1=overclaim, P2=term imprecision, P3=style
- rule: P0/P1 must be zeroed before any body rewrite; P2/P3 handled during section rewrites.
- numbers authority: `canonical_results_v1_5.csv` (built from locked assets only).

## Critical structural finding

`05_experiments.tex` (and the abstract/conclusion/discussion) still describe the OLD 
v1.4 fixed-budget fx60 package (5 seeds, update-60 checkpoints, 88.6%/53.2%/21.8%, 
500 matched episodes, dropout030_relay_failure). These numbers conflict with the locked 
v1.5 chain and are P0. The experiments chapter must be rebuilt around RQ1–RQ6 with 
canonical tables (table1_held_out / table2_ablation / table3_robustness / 
table4_efficiency) and the Pareto figures.

## main.tex
- **[L24] [P0] mechanism_fact**
  - ORIG: `constructs separate perception, communication, and dynamic task-support relations`
  - REPL: `constructs separate perception, communication, and task-support relations (task-support is a static task-dependent relation mask, not a dynamic gate)`
  - EVIDENCE: TASK_SUPPORT_MECHANISM_PROTOCOL Addendum C: no post-failure activation increase; pre 0.141→early 0.092
- **[L24] [P0] experiment_claim**
  - ORIG: `improves post-failure kill-chain recovery over no-graph and single-graph baselines under a five-seed fixed-budget evaluation. The full method achieves an 88.6% …`
  - REPL: `achieves near-saturated recovery reliability (0.971±0.021) while reducing post-failure recovery latency by ~38%/34%/59% vs MAPPO/HAPPO/param-matched (3 training…`
  - EVIDENCE: canonical_results_v1_5 table1_held_out (locked)
- **[L24] [P0] experiment_claim**
  - ORIG: `Mechanism ablations show that removing role-pair-conditioned message gating significantly degrades recovery`
  - REPL: `Ablations show Gate Prior is a strong contributor (recovery 0.972→0.772 without it); Task-Support contributes empirically (0.972→0.892); role-pair modulation sh…`
  - EVIDENCE: canonical table2_ablation (locked)
- **[L24] [P0] experiment_claim**
  - ORIG: `removing task-support relations lowers mean recovery with stronger seed-level heterogeneity`
  - REPL: `removing task-support relations lowers held-out recovery (0.972→0.892) and increases recovery latency (10.8→15.0)`
  - EVIDENCE: canonical table2_ablation (locked)
- **[L24] [P1] mechanism_fact**
  - ORIG: `performs role-pair-conditioned message propagation under centralized training and decentralized execution`
  - REPL: `applies state-dependent edge-feature-modulated attention over multi-relation graphs (a static role-pair modulation is retained as an auxiliary component)`
  - EVIDENCE: RPG REMOVE/simplify verdict (robustness/efficiency locks)
- **[L15] [P2] contribution_level**
  - ORIG: `\title{Multi-Relation Role Graph Reinforcement Learning for Heterogeneous UAV Kill-Chain Recovery under Limited Communication and Intermittent Sensing}`
  - REPL: `\title{Task-Graph-Driven Multi-Relation Coordination for Fast Post-Failure Recovery in Multi-UAV Semantic Search}`
  - EVIDENCE: PAPER_RESTRUCTURE_MAP §1; RPG is auxiliary, task-graph is the core narrative
## 01_introduction.tex
- **[L9] [P0] experiment_claim**
  - ORIG: `the multi-relation policy restores the kill chain more reliably than no-graph and single-graph baselines under a five-seed fixed-budget evaluation`
  - REPL: `the multi-relation policy reaches near-saturated recovery reliability (0.971±0.021, 3 seeds) and restores the kill chain substantially faster than MAPPO/HAPPO/p…`
  - EVIDENCE: canonical table1_held_out
- **[L15] [P0] experiment_claim**
  - ORIG: `\item We provide a five-seed fixed-budget evidence chain showing improved relay-failure recovery over no-graph and single-graph baselines, supported by seed-awa…`
  - REPL: `\item We provide a locked three-seed evidence chain (10,800-episode held-out, 10,500-episode robustness, efficiency profiling) showing near-saturated recovery r…`
  - EVIDENCE: locked evidence chain (held-out/robustness/efficiency/gate-prior locks)
- **[L13] [P2] contribution_level**
  - ORIG: `\item We propose a multi-relation role graph policy with perception, communication, task-support relations, and role-pair-conditioned message propagation for de…`
  - REPL: `\item We propose a task-graph-driven multi-relation graph policy (perception/communication/task-support relations with state-dependent edge-feature-modulated at…`
  - EVIDENCE: PAPER_RESTRUCTURE_MAP §14 (contribution 1)
## 04_method.tex
- **[L13] [P1] contribution_level**
  - ORIG: `Role-pair-conditioned message propagation is used so that messages can depend on sender role, receiver role, and relation type. This is the key distinction from…`
  - REPL: `State-dependent edge-feature-modulated attention over separate relation channels is used so messages depend on relation type and edge features; role-pair modula…`
  - EVIDENCE: RPG REMOVE/simplify; edge-feature modulation is the claimed mechanism
- **[L28] [P1] contribution_level**
  - ORIG: `\caption{Multi-relation role graph. Perception, communication, task-support, and attack-window relations have different semantics, while role-pair-conditioned m…`
  - REPL: `\caption{Multi-relation task graph. Perception, communication, and task-support relations have different semantics and are processed by state-dependent, edge-fe…`
  - EVIDENCE: TASK_SUPPORT protocol: task-support is a relational mask over delivered communication, not an independent channel
## 05_experiments.tex
- **[L7] [P0] number_scope**
  - ORIG: `fixed-budget checkpoint rule ... 60 safety-continuation PPO updates ... actor_critic_update_0060.pt ... five training seeds and 100 matched test episodes per se…`
  - REPL: `replace with the locked protocol: 3 training seeds × 977 PPO updates, held-out base_seed 745669, 2 scenarios × 4 windows × 100 episodes/seed (10,800-episode hel…`
  - EVIDENCE: held-out/robustness/efficiency protocols (frozen)
- **[L13] [P0] number_scope**
  - ORIG: `The full multi-relation method achieves an 88.6% post-failure recovery rate, compared with 53.2% ... 21.8% ... tracking from 47.5% to 77.6% ...`
  - REPL: `replace with canonical table1_held_out numbers (Full recovery 0.9706±0.0213, t_rec 10.8±0.6; vs MAPPO/HAPPO/param_matched 17.4/16.3/26.2)`
  - EVIDENCE: canonical_results_v1_5 table1_held_out
- **[L17] [P0] number_scope**
  - ORIG: `The seed-aware bootstrap indicates ... 35.4 percentage points ... [1.2, 73.0] ... 66.8 ... [28.6, 93.8] ... single-graph baseline has a 2.8% mean collision rate`
  - REPL: `delete (old bootstrap); report locked 3-seed mean ± SD and Wilson95 lower bound from canonical table1_held_out`
  - EVIDENCE: canonical_results_v1_5
- **[L23] [P0] number_scope**
  - ORIG: `early-failure setting ... 88.2% ... 46.6% ... 23.2% ... 41.6 pp ... [4.4, 78.6]`
  - REPL: `replace with locked robustness numbers (R00–R09 degradation, ΔRecovery/Δt_rec/worst-seed) from canonical table3_robustness`
  - EVIDENCE: canonical table3_robustness
- **[L35] [P0] experiment_claim**
  - ORIG: `This supports role-pair-conditioned message gating as the cleanest current mechanism contribution.`
  - REPL: `Delete. Locked evidence shows role-pair modulation provides no consistent independent gain (recovery 0.990 without it); do not claim it as a mechanism contribut…`
  - EVIDENCE: robustness RPG verdict REMOVE/simplify; canonical table2_ablation
- **[L37] [P0] experiment_claim**
  - ORIG: `Removing task-support relations also reduces mean recovery from 88.6% to 64.8%, but its seed-aware recovery interval crosses zero. Therefore ... supportive mech…`
  - REPL: `Replace with locked numbers: removing task-support lowers recovery 0.972→0.892 and raises t_rec 10.8→15.0; internal temporal analysis (pre 0.141→early 0.092→pre…`
  - EVIDENCE: task-support-mechanism-results-lock
- **[L43] [P0] experiment_claim**
  - ORIG: `Figure ... shows failure-aligned tracking, connectivity, chain-closure, and recovery-CDF curves ... aggregated over the matched fixed-budget test set`
  - REPL: `Replace with locked case-trajectory figures (task_support case manifest, fixed selection rule) and R00–R09 robustness degradation curves`
  - EVIDENCE: task_support_assets; canonical table3_robustness
- **[L63] [P1] experiment_claim**
  - ORIG: `This additional cost is modest in absolute CPU actor-forward latency for the present 3v1 setting`
  - REPL: `Replace with the honest efficiency framing: Full has higher joint-decision latency (12.05 ms), lower e2e throughput (242 env-steps/s) and highest training peak …`
  - EVIDENCE: efficiency-results-lock-v1.5.0 (canonical table4)
- **[L69] [P2] experiment_claim**
  - ORIG: `three-seed no-curriculum development diagnostic ... 88.9% ... 87.8% ... 2.2 percentage points`
  - REPL: `remove old numbers; keep the statement that topology curriculum is a training protocol, not a primary contribution (no v1.5 claim needed)`
  - EVIDENCE: PAPER_RESTRUCTURE_MAP §12
## 06_discussion.tex
- **[L3] [P0] experiment_claim**
  - ORIG: `The fixed-budget five-seed evaluation strengthens this claim ... improves recovery over both no-graph and single-graph baselines while maintaining zero test col…`
  - REPL: `Replace with locked framing: near-saturated reliability (0.971±0.021) with recovery latency reduced ~38%/34%/59% vs MAPPO/HAPPO/param-matched; the advantage is …`
  - EVIDENCE: canonical table1_held_out
- **[L5] [P0] experiment_claim**
  - ORIG: `The strongest mechanism evidence is the role-pair-conditioned message-gating ablation ... separates in favor of the full method ... task-support relation ablati…`
  - REPL: `Replace with: the strongest mechanism evidence is Gate Prior (cross-seed gate corr 0.962 vs 0.562, AUC 0.545 vs 0.396, worst-seed stability); Task-Support is em…`
  - EVIDENCE: gate-prior-mechanism-results-lock; canonical table2_ablation
- **[L9] [P0] experiment_claim**
  - ORIG: `the current paper-facing package uses a fixed checkpoint at update 60 ... should not be mixed with validation-selected results`
  - REPL: `Replace with: results come from a locked pre-registered protocol (fixed checkpoints update_0700/update_0100 etc., validation-selected 27-checkpoint manifest, he…`
  - EVIDENCE: held-out protocol; 27-checkpoint manifest lock
## 07_conclusion.tex
- **[L5] [P0] experiment_claim**
  - ORIG: `Across five training seeds and 500 matched test episodes, the full multi-relation method achieves 88.6% recovery, compared with 53.2% ... 21.8% ... removing rol…`
  - REPL: `Across 3 training seeds and a 10,800-episode held-out, Full reaches recovery 0.971±0.021 with t_rec 10.8±0.6; ablation shows Gate Prior (0.972→0.772) and Task-S…`
  - EVIDENCE: canonical tables (locked)
- **[L3] [P1] contribution_level**
  - ORIG: `The method separates perception, communication, and task-support relations and uses role-pair-conditioned message propagation under centralized training and dec…`
  - REPL: `The method separates perception, communication, and task-support relations processed by state-dependent edge-feature-modulated attention under centralized train…`
  - EVIDENCE: PAPER_RESTRUCTURE_MAP §14