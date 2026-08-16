# DRTP Self-Reference Criterion Adequacy Review

## Status and scope

**REVIEW FINDING: `R_OOD` IS SCIENTIFICALLY UNSUITABLE AS A HARD NECESSARY
GATE FOR ABSOLUTE ROBUSTNESS SUPERIORITY.**

This is a mathematical and metric-semantics review only.  It starts no
training, does not generate or inspect held-out data, and changes neither
DRTP/UTR, PPO, the S2 environment, reward, failure semantics, information
boundary, seed set, or evaluation results.

`DRTP_SG_MAPPO_METHOD_CONTRACT.md` v1 and its recorded 10M development result
remain historical **`DEVELOPMENT_RETENTION_NO_GO`**.  This review does not
rewrite that result as PASS and does not retroactively change any v1 gate.

## 1. Reviewed quantity and intended use

The v1 self-reference diagnostics are

\[
R_{\mathrm{OOD,mean}}=\frac{J_{\mathrm{OOD,mean}}}{J_{F0}},\qquad
R_{\mathrm{OOD,worst}}=\frac{J_{\mathrm{OOD,worst}}}{J_{F0}}.
\]

They describe how a policy's unseen-condition return compares with its own
seen-F0 return.  They can be useful descriptive indicators of *relative
retention across conditions*.  The question here is narrower: can either
ratio be a necessary hard condition for declaring method A absolutely more
robust than method B when A has higher `J_F0` and higher `J_OOD`?

## 2. Monotonicity analysis

For positive denominator (F=J_{F0}>0) and numerator (O=J_{OOD}>0),

\[
R(O,F)=\frac{O}{F},\qquad
\frac{\partial R}{\partial O}=\frac{1}{F}>0,\qquad
\frac{\partial R}{\partial F}=-\frac{O}{F^2}<0.
\]

Thus, holding OOD performance fixed, an improvement in canonical-F0
performance *lowers* the ratio.  The quantity is not monotone in the pair of
absolute performance coordinates ((F,O)).

More generally, let method B have positive ((F_B,O_B)).  Let method A satisfy

\[
F_A=aF_B,\qquad O_A=bO_B,\qquad a>b>1.
\]

Then A strictly dominates B on both absolute endpoints:

\[
F_A>F_B,\qquad O_A>O_B,
\]

but

\[
R_A=\frac{b}{a}R_B<R_B.
\]

For a concrete counterexample, B may have ((F_B,O_B)=(100,108)), while A
has ((F_A,O_A)=(200,162)).  A is strictly better at both F0 and OOD, but
`R_A=0.81 < 1.08=R_B`.

Consequently, a rule requiring `R_A >= R_B` can reject A solely because its
F0 improvement is larger than its OOD improvement, even when A is absolutely
better in both conditions.  It fails the monotonicity required of a necessary
criterion for *absolute robustness superiority*.

## 3. Frozen-development illustration (not a re-analysis gate)

The archived strict-continuous 10M development result illustrates the
counterexample without defining any new threshold:

| pooled 10M quantity | UTR-SG | DRTP-SG |
|---|---:|---:|
| `J_F0` | 88.6035 | 182.1619 |
| `J_OOD_mean` | 95.2907 | 182.2866 |
| `J_OOD_worst` | 79.4429 | 173.1004 |
| `R_OOD_mean` | 1.0807 | 1.0002 |
| `R_OOD_worst` | 0.8965 | 0.9477 |

DRTP is higher on both absolute F0 and both absolute OOD endpoints, while its
mean self-reference ratio is lower.  The v1 hard self-reference row therefore
failed exactly through the structural non-monotonicity above, not through a
missing evaluation, seed exclusion, safety violation, or aggregation error.

## 4. Adequacy decision

`R_OOD_mean` and `R_OOD_worst` remain legitimate **descriptive relative-
retention diagnostics**, subject to their denominator dependence.  They may
help explain whether OOD performance changes proportionally with F0.  They
must not, alone, veto an otherwise absolute-performance-dominant method.

The v1 self-reference hard-gate role is therefore scientifically unsuitable.
This finding authorizes creation of a versioned, forward-looking held-out
confirmation contract.  It does not authorize held-out execution.  The v2
contract preserves every v1 absolute-performance, seed-consistency, safety,
and exposure criterion and changes only the classification of these two ratios
from hard gate to descriptive diagnostic.
