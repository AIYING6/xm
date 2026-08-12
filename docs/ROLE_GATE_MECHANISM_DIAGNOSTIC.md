# Role-Gate mechanism diagnostic

The code uses `alpha * g * h_j`; the gate applies after attention normalization. Deterministic interventions demonstrate that `g` changes actor logits. No trained DEVELOPMENT_ONLY trajectory was run, so alpha/g co-adaptation correlation and saturation during optimization are not yet estimated. There is therefore no evidence of attention compensation, only an identified theoretical possibility through attention and the ungated union residual.
