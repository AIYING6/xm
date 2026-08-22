# 4. Method

## 4.1 Matched Single-Graph backbone

DRTP-SG-MAPPO keeps the existing 116,728-parameter Single-Graph actor/critic and standard PPO settings. It adds no encoder, relation branch, recurrent module, reward term, critic input, or inference-time module. UTR-SG-MAPPO is the capacity- and topology-group-matched comparator.

## 4.2 Topology-perturbation groups

Training episodes are assigned to nominal `N`, canonical failure `F0`, early timing `TE`, late timing `TL`, short duration `DS`, long duration `DL`, or compound `CP`. The nominal exposure is fixed at `p_N=0.50`. For UTR, the remaining six groups have `q_k=1/6`. Each group's scenario members are sampled uniformly.

## 4.3 Bounded adaptive weighting

The conceptual robust objective is

`max_theta [ p_N J_N(theta) + (1-p_N) min_{q in Q} sum_k q_k J_k(theta) ]`,

where `Q={q in Delta^6: 0.05 <= q_k <= 0.35}`. The implementation approximates the inner distribution only through episode-sampling weights. Group returns are accumulated between adaptation boundaries, and the nominal return is the competence anchor. Difficulty is the clipped normalized nominal-minus-group return gap. The candidate update is exponentiated-gradient weighting followed by smoothed projection onto `Q`; the frozen constants are warm-up 128 updates, adaptation interval 32, EMA coefficient 0.20, temperature 1.00, smoothing 0.50, `d_max=2.00`, and `epsilon=1e-8`.

## 4.4 Information and inference boundary

Group labels, selected failure timing/duration, EMA values, difficulty, and `q` exist only in the sampler/logger. They are absent from actor and critic observations and from evaluation. Thus DRTP changes training exposure, not the policy's legal information set.
