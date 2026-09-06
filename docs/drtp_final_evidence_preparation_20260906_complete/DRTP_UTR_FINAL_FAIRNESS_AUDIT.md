# DRTP versus UTR final fairness audit

**Verdict:** `DRTP_UTR_FINAL_FAIRNESS_PASS`.

| Dimension | UTR | Original DRTP | Audit result |
|---|---|---|---|
| Actor/critic, PPO, reward, environment, failure support | Frozen common configuration | Frozen common configuration | identical |
| Training distribution | Uniform topology sampling | Adaptive DRTP sampling | intended sole method difference |
| Budget | 39,063 updates / 10,000,128 steps | same | identical |
| Checkpoint / stopping | final 10M only; no promotion | same | identical |
| Seeds and endpoint tapes | matched within each cohort | same | identical |

The audit is a source/configuration comparison, not a performance claim. It identifies no implementation correction; further fairness re-auditing is not automatically authorized.
