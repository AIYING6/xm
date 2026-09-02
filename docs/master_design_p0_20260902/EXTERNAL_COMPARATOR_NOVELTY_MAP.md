# External comparator and novelty map

The following mapping is a design audit, not an implementation claim. URLs are primary sources where available. Freeze one feasible curriculum/prioritized comparator and one feasible robust/group comparator before the first main-scale training.

| Work | problem / task distribution | update signal | policy-dependent | static/adaptive | topology-aware | MARL/UAV | failure type | complexity | fair mapping |
|---|---|---|---:|---|---:|---|---|---|---|
| Jiang et al., PLR (ICML 2021) | prioritize replayed levels | learning potential | yes | adaptive | no | RL / no | level difficulty | medium | yes: failure-mask replay |
| Portelas et al., teacher-curriculum survey | curriculum task selection | competence/progress | often | mixed | no | RL / no | task variation | medium | conceptual only |
| Klink et al., SPDL (ICLR 2021) | self-paced task distribution | performance/KL constraint | yes | adaptive | no | RL / no | domain parameters | high | partial |
| Mehta et al., ADR (CoRL 2020) | active domain randomization | policy boundary | yes | adaptive | no | RL / no | domain shift | high | partial |
| Dennis et al., PAIRED (NeurIPS 2020) | adversarial environment generation | regret | yes | adaptive | no | RL / no | generated levels | high | no: changes task generator |
| Rajeswaran et al., EPOpt (arXiv 2016) | robust domain distribution | worst percentile | yes | robust | no | RL / no | model variation | medium | yes: failure-group CVaR |
| Xu et al., GDR-RL (ICLR 2023) | group distributional robustness | group return | yes | robust | no | RL / no | group shift | medium | yes: frozen failure groups |
| Lowe et al., M3DDPG (AAAI 2019) | adversarial multi-agent robustness | adversary | yes | adaptive | no | MARL / no | adversarial policy | high | partial |
| Kim et al., ADMAC (AAAI 2024) | robust communication MARL | communication adaptation | yes | adaptive | yes | MARL / no | attacks/noise | high | partial |
| Li et al., Mis-Spoke or Mis-Lead (2021) | communication robustness | attacked messages | yes | static | yes | MARL / no | communication corruption | high | partial |
| Zhang et al., Certifiably Robust Policy Learning (2022) | robust decentralized communication | certificate/loss | yes | robust | yes | MARL / no | message attack | high | partial |
| MA3C (2023) | resilient communication | curriculum/communication state | yes | adaptive | yes | MARL / no | link disruption | high | partial |
| ExpoComm (ICLR 2025) | communication-efficient MARL | information budget | yes | adaptive | graph-aware | MARL / no | bandwidth | high | no: different objective |
| ETRI resilient UAV network (TNSM 2026) | UAV network resilience | routing/network control | mixed | mixed | yes | UAV | network failures | high | conceptual |
| UAV network restoration MARL (Ad Hoc Networks 2025) | restoration scheduling | task reward | yes | adaptive | yes | UAV | node/link outage | high | conceptual |

## Frozen mapping decision

**External curriculum/prioritized:** PLR-style failure-mask prioritization, adapted only after an offline mapping proof that its replay/update cadence does not grant extra data or privileged actor information.  
**External robust/group comparator:** EPOpt/CVaR-style or GDR-RL-style frozen failure-group objective; choose exactly one after interface audit.  
**Not fair as drop-in:** PAIRED, full ADR, most communication-defense methods and UAV network restoration papers alter the generator, adversary, network-control objective or information channel.

Sources: [PLR](https://proceedings.mlr.press/v139/jiang21b.html), [GDR-RL](https://proceedings.mlr.press/v206/xu23d.html), [SPDL](https://arxiv.org/abs/2004.11812), [ADR](https://arxiv.org/abs/2002.07911), [PAIRED](https://arxiv.org/abs/2012.02096), [EPOpt](https://arxiv.org/abs/1610.01283), [ADMAC](https://ojs.aaai.org/index.php/AAAI/article/view/29708), [Mis-Spoke](https://arxiv.org/abs/2108.03803), [Robust communication](https://arxiv.org/abs/2206.10158), [MA3C](https://arxiv.org/abs/2305.05116), [ExpoComm](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3514dbacaebf0f38b25adfe59ed81a8a-Abstract-Conference.html), [UAV restoration](https://doi.org/10.1016/j.adhoc.2025.103785).
