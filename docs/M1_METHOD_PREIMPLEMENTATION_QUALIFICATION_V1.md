# M1 method pre-implementation qualification v1

**Final status:** `M1_PARTIAL__METHOD_NOVELTY_REDESIGN_REQUIRED`

## Scope and decision

M1 was restricted to implementation-free qualification of the M0 stage-aware acquisition candidate. It did not add a method actor, train a policy, inspect a new pilot, change the task, or modify the frozen reward. The question was whether the candidate is sufficiently legal, fairly comparable, and distinct from prior work to justify a minimal implementation.

The result is **partial rather than pass**. The proposed information and comparator contracts are feasible as specifications, but the candidate architecture as currently frozen is not a defensible headline algorithmic novelty: legal recurrent target history and latent/stage-conditioned control both have clear prior-art families. No M2 implementation is authorized until the contribution is redesigned or explicitly repositioned away from an architecture-novelty claim.

## 1. Existing-boundary regression

The current corrected-contract baseline passed the relevant implementation regressions at the M1 source state:

| Check | Result | Meaning |
| --- | --- | --- |
| Actor-boundary suite | 14/14 PASS | Existing actor paths exclude unavailable teammate truth, pending/dropped payload, critic state, and cache-bypassing relay truth. |
| Target-information contract suite | 4/4 PASS | Existing target fields are sourced from legal sensing or delivered/cache-valid evidence rather than the global target side channel. |
| Continuous-policy interface suite | 8/8 PASS | The present continuous-guidance/commit action contract has finite, consistent distribution and PPO-interface checks. |
| Role-specific-head smoke check | PASS | The current L1--L4 baseline preserves role-specific policy-output semantics. |

These are baseline assurances, not evidence that a future recurrent candidate already passes. The candidate has no code yet, so its target-memory runtime behavior cannot honestly be marked as tested.

## 2. Recurrent-memory legality qualification

The M0 contract is internally compatible with the strict recipient-specific boundary only if the future implementation obeys all of the following semantic rules:

1. Target memory updates only from currently legal local sensing or delivered/cache-valid target evidence and its legal availability/age/confidence/provenance metadata.
2. With neither source present, the target-memory output **and stored target-memory state** reset before the next action. A GRU/LSTM hidden state may not become an indefinite cache.
3. Pending, dropped, expired, or globally stored target content may not affect target memory, progress latent, masks, action distribution, deterministic action, or gradients.
4. Target-free self history may contain only the recipient's self state, role, and own executed previous action. It may not become a route for target, teammate, critic, or evaluator information.
5. Recurrent state is private to each recipient and vectorized environment instance and resets at episode termination; no pooling, graph residual, or cross-agent state sharing is permitted.

Therefore the **contract is feasible but unimplemented**. A minimal implementation would first have to pass the M0 deterministic counterfactuals plus explicit state-reset, cross-recipient isolation, and old/new PPO-log-prob tests. Any failure is `M1_NO_GO__METHOD_CONTRACT_OR_COMPARATOR_INVALID`, not a training issue.

## 3. Full--B1 fairness qualification

The primary comparison is frozen in [M1 Full--B1 capacity and information-parity protocol](M1_FULL_B1_CAPACITY_PARITY_PROTOCOL_V1.md). It requires identical legal raw actor fields, history semantics, action interface, reward, task, budget, and evaluation protocol. `B1` receives the same legal target and self histories as Full and must be actor-parameter matched within 0.5%; it differs only by direct fusion rather than a progress-conditioned control modulation.

This is an acceptable **conditional** comparator design. It becomes valid only after a future static manifest verifies the exact parameter counts, raw-source hashes, resets, action masks, and gradients. It does not itself rescue the candidate's novelty position.

## 4. Focused novelty audit

The audit tested the candidate against four established method families rather than looking only for an identical three-module combination.

| Prior-art family | Verified precedent | Consequence for the candidate |
| --- | --- | --- |
| Recurrent MARL under partial observability and limited communication | R-MADDPG explicitly uses recurrent multi-agent actor--critic structure to address partial observability and limited communication. | A legal recurrent actor/history encoder is not a standalone innovation. |
| Attention/recurrent history in stochastic partial observability | Attention-based recurrent MARL uses history-aware recurrence under stochastic partial observation; recurrent MAPPO is a known comparator family. | “Uses temporal memory under intermittent observation” is already established. |
| UAV target tracking/pursuit with observation histories | UAV target-tracking work uses sequence models to process observation histories under delayed/interrupted observations; recent multi-UAV pursuit work uses role-based MARL. | Target-history encoding in a UAV pursuit setting is not enough by itself. |
| Temporal abstraction, phases, and option-like control | Learning Abstract Options and broad hierarchical/phase-conditioned policy literature establish latent temporal abstractions and stage-dependent control. | An unsupervised progress latent plus conditioned control is not independently novel without a substantially sharper mechanism. |

Primary sources checked: [R-MADDPG (ICML 2020)](https://arxiv.org/abs/2002.06684), [Attention-Based Recurrence for MARL (ICML 2023)](https://proceedings.mlr.press/v202/phan23a/phan23a.pdf), [UAV target tracking with observation sequences (Information Sciences, 2024)](https://www.sciencedirect.com/science/article/pii/S0950705124002399), [multi-UAV pursuit with role-based MARL](https://arxiv.org/abs/2303.01799), and [Learning Abstract Options (NeurIPS 2018)](https://proceedings.neurips.cc/paper/2018/hash/cdf28f8b7d14ab02d12a2329d71e4079-Abstract.html).

This is not a claim that no publishable contribution can exist in this task. It is a negative qualification finding: the present Full definition is a direct composition of familiar tools, and an eventual positive result could plausibly be attributed to a familiar recurrent/conditioning capacity rather than a new algorithmic principle.

## 5. M1 verdict and permitted next decision

`M1_PARTIAL__METHOD_NOVELTY_REDESIGN_REQUIRED`

The project has a valid, evidence-derived problem statement -- legal evidence often fails to become attack-range acquisition -- and a feasible actor-contract specification. It does **not** yet have a sufficiently differentiated main-method claim.

Before code or training, the author must choose one of two evidence-honest routes:

1. **Method-hypothesis redesign:** identify a falsifiable mechanism that is materially more specific than “legal memory plus stage conditioning,” define its matched comparator and kill condition, then repeat M1 novelty qualification. This must occur without looking at candidate performance.
2. **Contribution repositioning:** treat the strict-information mission benchmark, controlled learnability ladder, and failure-localization protocol as the central contribution; do not present the current Full architecture as a new algorithm.

Not permitted after this verdict: implementation of the current candidate, development pilot, new training, capacity tuning, reward changes, or retroactive novelty claims based on future performance.
