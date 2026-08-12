# Role-Gate implementation audit

For relation branch `r`, receiver `i`, sender `j`, and hidden coordinate `d`, the final implementation is:

```text
z[r, role_i, role_j, d] is a trainable embedding logit
g_ij^r[d] = sigmoid(z[r, role_i, role_j, d])
m_i^r = sum_j alpha_ij^r * h_j * g_ij^r
```

`alpha` is normalized by softmax before the gate is applied. The gate modulates message payload, not attention score. Each relation layer owns a separate gate embedding, so the final gate is relation-conditioned. The union/global residual is an ungated `GraphAttentionLayer` branch and is a possible compensation path, but it does not bypass relation branch computation.

Gate parameters are standard `nn.Embedding` parameters under the actor and are included in the optimizer through `agent.parameters()`.

## Prior semantics

Historical raw assignment of `0.4` would yield `sigmoid(0.4)=0.598688`, so it was a prior/logit semantic bug if `0.4` meant probability. Final code treats `role_gate_prior_strength` as probability and stores `log(0.4/0.6)=-0.405465`, yielding an effective initial gate of 0.4 on selected pairs. Default unprioritized gates remain 0.5.
