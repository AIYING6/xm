# DRTP final manuscript scaffold

## One-sentence argument

We show that Dynamic Robust Topology Prioritization reallocates training exposure across frozen topology-failure conditions and yields repeated cohort-level robustness benefits over matched Uniform Topology Replay at a fixed 10M endpoint, with held-out, external-comparator and cross-scale evidence reported under pre-specified protocols.

## Reader sequence

1. **Relevance:** topology failures make heterogeneous UAV coordination fragile.
2. **Novelty:** DRTP adapts only the reset-side exposure distribution while retaining the policy, reward and PPO interfaces.
3. **Trust:** matched UTR control, frozen budget, two independent cohorts and fixed endpoints.
4. **Reuse:** explicit topology groups, sampler state, seed registries and reproducible evaluation contracts.
5. **Meaning:** cohort-level gains are repeated; scope is the evaluated fault interface and endpoints.

## Proposed title direction

**Dynamic Robust Topology Prioritization for Fault-Resilient Heterogeneous UAV Coordination**

## Main-text architecture

### 1. Introduction

- Motivate topology disruptions as a training-distribution problem for heterogeneous multi-UAV policies.
- Identify the gap: uniform exposure can underrepresent the conditions that determine robustness at deployment.
- State the constrained design principle: change topology exposure, not reward, observation, policy architecture or PPO.
- Preview the evidence: independent cohorts, fixed endpoint, OOD, external comparator and six-UAV cross-scale study.

### 2. Problem formulation and DRTP

- Define the heterogeneous-UAV graph, frozen topology-condition groups, and final endpoint.
- Describe UTR as uniform sampling across the same support.
- Define DRTP's nominal anchor and adaptive conditional distribution over non-nominal groups.
- Specify that completed episode return updates sampler evidence; policy objective and environment are unchanged.

### 3. Experimental protocol

- Explain matched training configurations, fresh seeds, 10M budget, and fixed endpoint tapes.
- Make the training seed the independent unit.
- Define perturbed return, nominal return, collision and timeout.
- State that A and B are analyzed separately.

### 4. Results

- Main result: paired A/B UTR-versus-DRTP robustness outcomes.
- Held-out/OOD: condition-level transfer under frozen shifts.
- External comparison: matched PLR-style replay results after completion.
- Cross-scale: six-UAV UTR-versus-DRTP results after completion.

### 5. Discussion

- Interpret the benefit as improved training exposure allocation in the tested fault interface.
- State scope through the evaluated topology groups, environments and endpoint protocol.
- Avoid mechanism claims not directly established by the retained evidence.

## Claim–evidence map

| Claim | Evidence | Status |
|---|---|---|
| Repeated cohort-level robustness benefit over UTR | Two completed fresh 10M cohorts | supported |
| Held-out structural transfer | Frozen OOD endpoint results | supported after final table import |
| Favorable comparison to adaptive replay | Matched PLR A/B endpoint results | pending |
| Cross-scale transfer to six UAVs | Matched 6-UAV endpoint results | pending |

