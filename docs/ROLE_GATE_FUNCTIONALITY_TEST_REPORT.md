# Role-Gate functionality test report

`results/development/role_gate_phase2ia/role_gate_diagnostic.json` contains deterministic DEVELOPMENT_ONLY diagnostics for seeds 101/202/303.

| Candidate | Gate parameters | Gradient norm | Force-0/1 actor-logit change | Result |
|---|---:|---:|---:|---|
| G0 no gate | 0 | n/a | n/a | valid simplicity reference |
| G1 shared | 800 | 1.38e-4 to 1.74e-4 | 0.024–0.033 | functional |
| G2 relation-conditioned | 4,800 | 1.55e-4 to 2.86e-4 | 0.012–0.020 | functional |

Gate parameters are registered, trainable, and receive finite non-zero gradients. Interventions change actor logits with other weights fixed. The test establishes functionality; it is not a performance comparison.

The union residual remains a potential compensation path because it is ungated. It was not shown to erase gate effects: gate interventions still changed actor outputs while the residual was enabled. A full ON/OFF compensation analysis requires future mechanism logging and remains a pre-training closure item.
