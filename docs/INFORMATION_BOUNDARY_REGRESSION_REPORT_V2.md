# Information-boundary regression report v2

The new fixed-input hidden-state regression suite passes:

```text
44 passed (including hidden target/undelivered message/failure hidden-state families)
```

The tests are located in `tests/test_phase2h_information_boundary.py`. They prove that the policy output is unchanged when environment-only state is mutated after actor-visible tensors are fixed. The full Phase 2H requirement additionally demands code-grounded graph-edge legality and a tape-backed end-to-end adversarial replay. Those pieces are not yet implemented; Gate I therefore remains **PENDING**, not PASS.
