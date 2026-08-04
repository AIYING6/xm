# EA-RG Mechanism Semantics Audit

**Audit date:** 2026-08-04
**Audit commit:** `2514ca3` (`formal-post-sixth-eval-ops-v1.4.2`)
**Code:** `algorithms/ri_gmappo/simple_ri_gmappo.py`
**Scope:** every module that can change message weights along the EA-RG forward
path, to align the paper's mechanism description with the actual implementation.

## Mechanism semantics table

| Mechanism | Dynamic? | Depends on | Paper wording (correct) |
|---|---|---|---|
| Role-pair gate (`role_pair_gate`) | **No** (static learned embedding) | static role-pair index | "learned static role-pair communication modulation" |
| Graph attention scores (`self.attn`) | **Yes** (input-dependent) | node hidden states `h` (`cat([hi,hj])` → LeakyReLU) | "state-dependent graph attention" |
| Edge-feature modulation (`edge_score(edge_feat)`) | **Yes** | per-edge features | "edge-feature-modulated attention" |
| Communication availability mask (`mask = clamp(adj+eye)`) | **Yes** (environment-driven) | env dropout/delay/topology (per step) | "environment-driven dynamic communication availability" |
| Relation projections (per-relation layers) | Static (per relation) | relation type | "relation-specific message transformation" |
| Critic value path | No graph gate | `share_obs + role_one_hot` via MLP | "critic uses share-obs + role one-hot MLP (no graph gate)" |

## Code evidence

- Role-pair gate — `RoleConditionedGraphAttentionLayer.forward` line 224-227:
  ```python
  pair_index = receiver_role * self.num_roles + sender_role
  gate = torch.sigmoid(self.role_pair_gate(pair_index)) if self.use_role_pair_gate else torch.full_like(hj, 0.5)
  ```
  `role_pair_gate` is `nn.Embedding(num_roles*num_roles, out_dim)` (line 201),
  learned, keyed by the static agent role IDs. It does **not** take obs, state,
  or any failure indicator as input → **static**.
- Graph attention — same file lines 172 / 216:
  ```python
  scores = self.leaky_relu(self.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1)
  if self.edge_score is not None and edge_feat is not None:
      scores = scores + self.edge_score(edge_feat).squeeze(-1)
  ```
  `attn` maps node-pair hidden state → scalar; therefore attention is
  **input/state-dependent**.
- Communication mask — lines 176-178 / 219-221:
  ```python
  mask = torch.clamp(adj + eye, 0.0, 1.0)
  scores = scores.masked_fill(mask <= 0.0, -1e9)
  ```
  `adj` is the per-step communication/reachability matrix produced by the env
  (dropout / delay / topology / node failure) — **environment-driven dynamic**.
- Critic — lines 574-579:
  ```python
  self.critic = MLP(share_obs_dim + num_roles, 1, hidden_dim)
  def critic_value(self, share_obs, role):
      role_one_hot = F.one_hot(role[:, :self.num_agents].long().clamp(0, self.num_roles-1), self.num_roles)
      return self.critic(torch.cat([share_obs, role_one_hot], dim=-1)).squeeze(-1)
  ```
  The critic does **not** use the graph encoder or role-pair gate.
- No module in the EA-RG forward path conditions message weights on a failure
  indicator; node-failure affects behaviour only through the env-provided
  `adj`/mask (and hence which messages exist).

## Implications for the paper

- **Allowed statements:**
  - "learned static role-pair communication modulation";
  - "state-dependent graph attention with edge-feature modulation";
  - "environment-driven dynamic communication availability (dropout/delay/topology)";
  - "relation-specific message transformations".
- **NOT allowed (no supporting module):**
  - "gate dynamically closes stale/failed messages after a node failure" — the
    role-pair gate is static; message exclusion after failure comes from the
    env-driven availability mask, not from a learned gate reacting to failure.

## Checkpoint parameter names

- `actor.multi_relation_graph.layer{1,2}.{0,1,2}.role_pair_gate.weight` (gate)
- `actor.multi_relation_graph.layer{1,2}.{0,1,2}.attn.weight/bias` (attention)
- `actor.multi_relation_graph.layer{1,2}.{0,1,2}.edge_score.*` (edge modulation, if enabled)
- `actor.obs_encoder.*`, `actor.intent_emb.*` (feature encoders)
- Critic has no `*.multi_relation_graph.*` parameters.
