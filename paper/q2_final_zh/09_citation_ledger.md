# 09 Citation Ledger

This is a verification queue, not a final bibliography. A reference enters the manuscript only after its primary source and metadata have been checked.

| ID | Intended role | Candidate primary source | Current status | Required action |
|---|---|---|---|---|
| R1 | MAPPO/CTDE foundation | Original MAPPO primary paper `[metadata not yet frozen]` | `MISSING_PRIMARY_METADATA` | verify authors, title, venue, year and stable URL/DOI |
| R2 | topology-aware cooperative MARL | TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient, AAAI 2024, https://ojs.aaai.org/index.php/AAAI/article/view/29699 | `CANDIDATE_PRIMARY` | read full paper and verify the exact topology/learner claim |
| R3 | robust MARL under changing agents/opponents | Robust Multi-Agent Reinforcement Learning / M3DDPG, AAAI 2019, https://aima.eecs.berkeley.edu/~russell/papers/aaai19-marl.pdf | `CANDIDATE_PRIMARY` | verify bibliographic metadata and scope wording |
| R4 | distributionally robust RL | Distributionally Robust Q-Learning, ICML 2022, https://proceedings.mlr.press/v162/liu22a.html | `CANDIDATE_PRIMARY` | verify objective and limitation relative to multi-agent CTDE |
| R5 | DRRL theoretical positioning | On the Foundation of Distributionally Robust Reinforcement Learning, https://arxiv.org/abs/2311.09018 | `CANDIDATE_PRIMARY` | verify final publication status and exact theorem scope |
| R6 | UAV communication-network restoration | Fast connectivity restoration of UAV communication networks, https://doi.org/10.1016/j.adhoc.2025.103785 | `CANDIDATE_PRIMARY` | verify authors, volume/pages and whether MARL is central |
| R7 | multi-hop UAV relay communication | Multi-hop UAV relay covert communication, https://doi.org/10.1016/j.cja.2025.103440 | `CANDIDATE_PRIMARY` | verify authors, volume/pages and task objective |

## Missing topic coverage

- a primary graph-attention/GNN reference used to describe the shared encoder;
- a primary MAPPO implementation or algorithm reference;
- one or two recent heterogeneous UAV MARL papers with comparable role-based coordination;
- one recent communication-failure/topology-perturbation UAV study;
- any target-journal-specific closely related paper required for positioning.

## Citation discipline

- cite a paper only for claims supported by that paper;
- do not cite a survey as the source of a primary algorithm when the original is available;
- do not describe TAPE, M3DDPG, or UAV relay methods as empirically inferior because no fair drop-in comparison was run;
- do not claim “first” after a limited search;
- replace every `[R#]` or `[CITATION NEEDED]` before submission.

