# v1.9 G0-R1 Task-Support Identifiability Audit

**Status: READ-ONLY AUDIT COMPLETE — TASK-SUPPORT IS NOT AN INDEPENDENT LEGAL
INFORMATION SOURCE IN THE CURRENT IMPLEMENTATION.**

This audit was authorized after G0 found
`A_Communication == A_TaskSupport`.  It makes no architecture, environment,
reward, protocol, or training change.  Its only question is whether the two
relations differ in a way that is both actor-legal and independently
intervenable.

## Prespecified decision rule

Task-Support could remain a separate scientific source only if all three
levels have affirmative evidence:

1. **support identifiability:** a legal state has `A_T != A_C`;
2. **feature identifiability:** with equal support, Task-Support carries a
   legal field not determined by Communication plus fixed role constants; and
3. **intervention identifiability:** a legal environment change can alter T
   while C remains fixed.

Changing `graph_relation_ablation=no_task_support` is an implementation
ablation, not a legal physical/task intervention, and cannot satisfy level 3.

## Audit design

The companion script uses fixed method-independent actions, three seeds per
condition, and 100 steps per seed.  It covers nominal operation, packet loss,
delayed delivery, radar dropout, relay failure, and their formal-like
combination.  It also reads the actual graph-construction and PCRF factor-call
source, rather than inferring input identity from tensor shape.

The machine-readable record is
[`V1_9_G0_R1_TASK_SUPPORT_IDENTIFIABILITY_REPORT.json`](V1_9_G0_R1_TASK_SUPPORT_IDENTIFIABILITY_REPORT.json).

## Result

Across 6 conditions × 3 fixed seeds × 101 graph states = **1,818** recipient
graph states, all audited conditions have zero C/T adjacency mismatches and
zero differences between the corresponding edge feature flags.  Source
inspection further confirms:

* both C and T use the same `valid teammate` predicate;
* the Task-Support edge field is exactly the same `support` scalar;
* PCRF factor layers receive the same generic legal `edge_feat` tensor, with
  only the relation adjacency channel selected separately; and
* the only code path that changes T independently is the explicit ablation
  flag, which is not a real actor-available task signal.

Thus `X_T` is determined by `X_C` and fixed implementation/role constants in
the current design.  There is no lawful environment intervention supporting a
separate Task-Support mechanism.

## Consequence

The three-factor PCRF-R1 hypothesis is over-parameterized for this
environment.  This result does not invalidate the source-conflict idea between
local perception and delivered/cache-valid communication.  It does prohibit
calling C and T independent evidence sources or training PCRF-R1 as a
three-source mechanism.

The recommended next scientific action is an author-authorized, separately
versioned **two-source PCRF-R2 (P,C)** theory/protocol freeze.  That action is
not taken by this audit.  Until the author explicitly authorizes it, GPU work
remains paused at G0 and the project status remains blocked.
