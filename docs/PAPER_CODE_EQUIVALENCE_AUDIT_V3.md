# Paper–Code equivalence audit v3

Final method equation: role-pair gates are relation-conditioned payload multipliers applied after attention softmax; edge features are attention-score bias; the union/global residual is an ungated parallel branch multiplied by its configured residual weight. Receiver/sender indexing follows the audited adjacency convention.

Baselines: MAPPO is no-graph CTDE; canonical Single-Graph is merged-adjacency and parameter-matched (hidden width 115); no-union is the final Full model with global residual multiplier zero. The manuscript must use these exact definitions before submission.
