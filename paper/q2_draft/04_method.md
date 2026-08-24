# 4. Method

## 4.1 Matched Single-Graph backbone

DRTP-SG-MAPPO keeps the existing 116,728-parameter Single-Graph actor/critic and standard PPO settings. It adds no encoder, relation branch, recurrent module, reward term, critic input, or inference-time module. UTR-SG-MAPPO is the capacity- and topology-group-matched comparator.

## 4.2 Topology-perturbation groups

Training episodes are assigned to nominal `N`, canonical failure `F0`, early timing `TE`, late timing `TL`, short duration `DS`, long duration `DL`, or compound `CP`. The nominal exposure is fixed at `p_N=0.50`. For UTR, the remaining six groups have `q_k=1/6`. Each group's scenario members are sampled uniformly.

## 4.3 Bounded adaptive weighting

The conceptual robust objective is

`max_theta [ p_N J_N(theta) + (1-p_N) min_{q in Q} sum_k q_k J_k(theta) ]`,

where `Q={q in Delta^6: 0.05 <= q_k <= 0.35}`. The implementation approximates the inner distribution only through episode-sampling weights. Group returns are accumulated between adaptation boundaries, and the nominal return is the competence anchor. Difficulty is the clipped normalized nominal-minus-group return gap. The candidate update is exponentiated-gradient weighting followed by smoothed projection onto `Q`; the frozen constants are warm-up 128 updates, adaptation interval 32, EMA coefficient 0.20, temperature 1.00, smoothing 0.50, `d_max=2.00`, and `epsilon=1e-8`.

For update `u`, let `Jhat_{k,u}` be the mean completed-episode return observed for group `k` since the preceding adaptation boundary. For an observed group, `EMA_{k,u}=(1-kappa)EMA_{k,u-1}+kappa Jhat_{k,u}`; for an unobserved group the EMA is unchanged. The nominal EMA is updated by the same rule. With `EMA_N,u` and `EMA_k,u` defined this way, the implementation is exactly:

`d_{k,u} = clip((EMA_N,u - EMA_k,u) / max(|EMA_N,u|, epsilon), 0, d_max)`.

The centered exponential proposal is:

`tilde_q_{k,u+1} = q_{k,u} exp(eta (d_{k,u} - mean_j d_{j,u})) / sum_j q_{j,u} exp(eta (d_{j,u} - mean_j d_{j,u}))`.

With smoothing coefficient `beta`, the pre-projection update and bounded simplex projection are:

`x_{u+1} = (1-beta) q_u + beta tilde_q_{u+1}`,

`q_{u+1} = Pi_Q(x_{u+1})`, where `Q={q in Delta^6: 0.05 <= q_k <= 0.35}`. The projection uses the water-filling form `q_k=min(0.35,max(0.05,x_k-lambda))`, with bisection for `lambda` and a final mass-residual assertion. In the frozen implementation, `eta=1.00`, `beta=0.50`, `epsilon=1e-8`, and `d_max=2.00`.

The update is applied only after the 128-update warm-up and then every 32 updates. During warm-up, the six perturbation groups remain uniform. The sampler logs `q`, `EMA`, difficulty, group returns, and realized exposure; none of these quantities is observable by the actor or critic.

## 4.4 What changes and what does not

| Component | UTR-SG-MAPPO | DRTP-SG-MAPPO |
|---|---|---|
| SG actor/critic and parameters | identical, 116,728 | identical, 116,728 |
| PPO, reward, environment, information boundary | unchanged | unchanged |
| Nominal exposure | fixed 0.50 | fixed 0.50 |
| Six perturbation groups | same groups, conditional uniform sampling | same groups, bounded adaptive weights |
| Inference-time computation | unchanged | unchanged |
| Training-only difference | `q_k=1/6` | `q` update above |

This decomposition is the causal comparison used in the main-paper ablation. It supports the narrower statement that the bounded adaptive exposure strategy differs from uniform exposure under the frozen contract; it does not, by itself, prove that every possible non-uniform schedule would be inferior.

## 4.5 Information and inference boundary

Group labels, selected failure timing/duration, EMA values, difficulty, and `q` exist only in the sampler/logger. They are absent from actor and critic observations and from evaluation. Thus DRTP changes training exposure, not the policy's legal information set.
