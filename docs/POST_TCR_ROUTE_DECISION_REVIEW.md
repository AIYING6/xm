# Post-TCR Route Decision Review

**Review type:** zero-training project-level route decision
**Final project decision:** **R1 — FREEZE PROBLEM / BUILD SYSTEM-ROBUSTNESS PAPER**

This report only reuses existing evidence. It does not start training, create
a held-out or canonical evaluation, implement a new algorithm, reopen DRTP or
TCR, tune hyperparameters, or rewrite any historical result.

## 1. Frozen history

The following results are immutable:

| Route / phase | Historical result | Interpretation boundary |
|---|---|---|
| DRTP development | pooled signal, retention `NO-GO` | large pooled OOD values did not establish seed-consistent maturity/safety |
| DRTP held-out v2 | `HELD_OUT_FAIL` | seed2002 showed a real F0/OOD/safety reversal |
| DRTP forensic review | C — no actionable cause / intrinsic seed sensitivity | DRTP permanently closed as paper-main candidate |
| TCR Phase-C 1M | `PHASE-C-V2 GO` after exposure-gate reanalysis | eligible for strict continuation only; not superiority evidence |
| TCR Phase-D 2M | `STOP_AT_2M` | TCR/seed2101 violated the frozen catastrophic rule |
| TCR forensic review | C — no actionable cause / intrinsic seed sensitivity | TCR permanently closed as paper-main candidate |

The two forensic C conclusions are not evidence that every adaptive or
gradient-based method is impossible. They do establish that the two tested
optimizer-level routes do not provide an actionable, reproducible mechanism
that is safe to promote to the paper main method.

## 2. Reusable project assets

The current project has substantial assets that remain scientifically useful:

- a 3-UAV heterogeneous Scout/Relay/Attacker environment;
- a frozen relay-node failure and topology-perturbation semantics;
- a legal CTDE actor-information boundary;
- matched Single-Graph MAPPO and UTR-SG implementations;
- communication, perception, and task-support graph telemetry;
- paired nominal/failure evaluation and timing/duration/compound OOD cases;
- risk-set failure-trigger validity and pre-trigger termination accounting;
- runtime-state persistence and strict continuation provenance;
- parameter-matched graph controls;
- seed-level rather than episode-level inference discipline;
- an accumulated audit trail covering exposure, legality, safety, maturity,
  and failure mechanisms.

These assets support a robustness benchmark/system paper even though DRTP and
TCR are not acceptable final algorithms.

## 3. Stable-baseline audit

The following evidence slices are deliberately kept separate. They use
different budgets and tapes and therefore are not treated as one pooled
statistical experiment.

| Evidence slice | Methods / seeds | Budget | Main descriptive result | Valid use |
|---|---|---:|---|---|
| Phase-C 1M | UTR, SPC, TCR × 5 | 1,000,192 | pooled OOD-worst: UTR 54.628, SPC 72.883, TCR 97.583 | development stability screen; TCR later failed continuation |
| Phase-D 2M | UTR, SPC, TCR × 5 | 2,000,128 | pooled OOD-worst: UTR 83.252, SPC 114.555, TCR 106.775 | seed-level stability/stop-loss evidence |
| DRTP development | UTR, DRTP × 2 | up to 3M | DRTP pooled OOD-worst 172.241 vs UTR 103.149 | descriptive development evidence; retention failed |
| DRTP held-out | UTR, DRTP × 3 | 10,000,128 | DRTP pooled OOD-worst 144.758 vs UTR 138.354 | independent failure evidence; held-out failed because seed2002 reversed |
| MSR | Mixed-50 SG × 2 | 1,000,192 | pooled J_nominal 137.662, J_failure 138.306 | mature shared-policy reference; no OOD or 5-seed confirmation |
| S3/RSG development | MAPPO, matched SG, RSG-TC × 3 | 200,192 | matched SG mean nominal 35.924; RSG-TC 12.532 | early learnability evidence only |

### 3.1 Most defensible stable reference

**UTR-SG-MAPPO is the most defensible conservative robustness reference**, not
because it has the highest pooled return, but because it has:

- fixed exposure rather than return-adaptive exposure;
- no DRTP feedback state;
- no projection rule whose interpretation depends on gradient surgery;
- a shared Single-Graph backbone and a clean comparison contract;
- five-seed development evidence in the TCR protocol;
- no identified evaluator or runtime defect;
- no paper-main promotion claim attached to it.

UTR is not declared universally optimal or perfectly stable. Its performance
still varies by seed and budget. The narrower conclusion is that it is the
cleanest baseline around which to report topology-robustness behavior without
claiming that an unstable optimizer has solved it.

### 3.2 Why other baselines are not interchangeable

MAPPO, matched Single-Graph, no-graph, HAPPO, and earlier Phase-1/Phase-2
comparators remain useful controls and historical context. However, older
results were generated under different task phases, tapes, horizons,
failure semantics, or training contracts. They must not be placed beside the
current OOD-worst values as if they were paired current evidence.

The current paper should use them in one of two ways:

1. current-protocol controls when an existing result has the same frozen
   topology-robustness contract; or
2. historical motivation/appendix evidence when the task contract differs.

## 4. Scientific lessons from DRTP and TCR

### H1 — High pooled robustness is not cross-seed robustness

**Supported.** DRTP reached strong pooled development values and favorable
pooled held-out means, but held-out seed2002 dropped from UTR J_F0 `186.921` to
DRTP `72.970` and from UTR OOD-worst `150.697` to DRTP `53.597`. TCR also had a
strong 1M pooled OOD-worst signal but TCR/seed2101 became catastrophic at 2M.
Pooled means cannot override seed-level failure.

### H2 — Adaptive exposure feedback can create seed-dependent trajectories

**Supported as a bounded interpretation, not a uniquely proven causal law.**
DRTP's adaptive group-weight loop produced strong pooled performance but failed
independent confirmation, and its forensic review found no single repairable
cause. The evidence is consistent with trajectory dependence in adaptive
exposure, but does not prove that one particular EMA/q update caused the
held-out reversal.

### H3 — Fixed exposure plus gradient conflict handling can look strong early

**Supported, but not as a durable method claim.** TCR's fixed-exposure 1M
screen passed its prospective stability gates, including 5/5 positive
OOD-worst direction. The same route failed at 2M because seed2101 crossed the
catastrophic threshold. The result is a direct warning against treating a
short-budget stability screen as maturity evidence.

### H4 — The central challenge is training-seed-stable topology robustness

**Strongly supported.** Across the two candidate routes, the recurring failure
is not absence of an observable topology perturbation or a broken evaluator.
It is the inability to maintain a high absolute robustness profile across
independent training trajectories and longer budgets. This is a publishable
problem statement even without claiming that DRTP or TCR solved it.

## 5. Route A — stable baseline plus problem, mechanism, and evaluation paper

### A1. Performance hierarchy

There is a meaningful but non-monotone hierarchy. At 1M, TCR's pooled OOD
values are high, but at 2M SPC's pooled OOD-worst exceeds TCR and TCR has a
catastrophic seed. DRTP has the strongest pooled development values but fails
held-out seed consistency. UTR is lower in pooled return but remains the clean
fixed-exposure reference. Mixed-50 has strong two-seed final values, but no
OOD confirmation and too few seeds to serve as the primary robustness result.

This is a useful result pattern for a systems paper: mean performance,
absolute failure performance, safety, maturity, and seed stability do not
rank methods identically.

### A2. Independent contribution without a new optimizer

Route A can form a coherent paper around the following contributions:

1. **Problem formulation.** A legal and physically consistent heterogeneous
   communication–task graph formulation for relay-node failures.
2. **Mechanism.** Relay failure removes relay-mediated path components and
   forces communication/path reorganization; mission degradation can occur
   without asserting an artificial information blackout or a unique relay
   intermediary.
3. **Evaluation framework.** Nominal, F0, timing, duration, compound, OOD-worst,
   risk-set trigger validity, pre-trigger termination, safety, and seed-level
   reporting are evaluated under a frozen contract.
4. **Robustness trade-off evidence.** Fixed exposure, adaptive exposure, and
   gradient-conflict controls are compared as descriptive strategies, with
   failed strategies retained as negative evidence rather than converted into
   superiority claims.
5. **Mechanistic reporting.** Path switching, task-support source, legal
   information, cache age, maneuver/control burden, and safety are used to
   explain why pooled performance alone is insufficient.

### A3. Novelty and publication assessment

| dimension | Route A assessment |
|---|---|
| Scientific novelty | **moderate** — topology-perturbation problem plus legality-aware evaluation is stronger than a generic UAV fault test |
| Experimental strength | **strong in audit/provenance; moderate for final paper unless the existing evidence is curated into one frozen comparison** |
| Algorithm novelty | **weak** — the paper should not sell UTR/SG as a new optimizer |
| Risk | **low-to-medium** |
| Additional compute | **zero for this decision; potentially 0–15M steps only if a final common-budget reference run is later required** |
| Expected positioning | **plausible Q2 for an application/robustness/systems venue; weak for an algorithm-centric Q2 venue** |

Route A is therefore sufficient for a Q2-oriented submission only if the
paper sells the benchmark, mechanism, and seed-stable robustness question,
not an invented algorithmic superiority claim. It is not a guaranteed Q2
result.

## 6. Route B — new architecture-level main algorithm

Route B should not mean another optimizer patch. DRTP and TCR provide enough
evidence to retire adaptive return weighting, difficulty/EMA feedback,
curriculum-style reweighting, generic gradient surgery, and nominal/failure
projection as the immediate development loop.

A future Route-B method would need to operate at a different level, such as a
fixed-objective architecture with explicit topology representation,
decentralized topology belief/memory, structural role/task decomposition,
or a topology-conditioned equivariant representation. This review does not
choose or implement one of them.

| dimension | Route B assessment |
|---|---|
| Scientific novelty | **potentially strong** if a genuine architecture-level gap is demonstrated |
| Experimental strength | **currently weak** — both tested optimizer-level candidates were closed after seed instability |
| Algorithm novelty | **potentially strong, currently unproven** |
| Risk | **high** |
| Additional compute | **roughly 15–60M environment steps** for one bounded 5-seed screen, maturity extension, and confirmation; evaluation/engineering is additional |
| Expected positioning | **plausible Q2 only if the new method survives strict seed/maturity/held-out gates; otherwise below target** |

Route B has a higher novelty ceiling but a substantially lower probability of
stable completion. It also reopens the exact algorithm-selection loop that has
already consumed DRTP and TCR budgets. No evidence currently shows that the
next architecture would repay this cost.

## 7. Route C — change the scientific question

Route C is not justified at present. The topology-robustness problem has a
validated intervention, measurable mission degradation, a legal information
boundary, and a nontrivial seed-stability challenge. The failure of DRTP/TCR
is evidence about solution stability, not evidence that the problem is empty.

### C1. Assets that could transfer

The environment, roles, SG-MAPPO, CTDE legality, failure semantics, topology
telemetry, and evaluation pipeline can transfer to a new question.

### C2. Historical evidence that could motivate a new question

The recovery-task infeasibility results, relay-necessity audits, DRTP/TCR
instability, and information-boundary audits can motivate a study of
topology-induced coordination and training instability. They cannot be
relabelled as evidence for a different causal claim.

### C3–C4. Cost and value

Changing the question would require a new problem contract, new estimand,
new tape, and likely at least `10–50M` environment steps before a fair
comparison. It has no demonstrated publication advantage over the already
validated Route-A problem and would discard part of the current evidence
chain. Route C is therefore not recommended.

| dimension | Route C assessment |
|---|---|
| Scientific novelty | unknown until a new question is defined |
| Experimental strength | weak initially; current evidence is not directly transferable |
| Algorithm novelty | not applicable yet |
| Risk | high |
| Additional compute | roughly 10–50M steps plus a new validation contract |
| Expected positioning | likely below Q2 target until a new problem is proven |

## 8. Route comparison and ranked recommendation

### 1. PRIMARY RECOMMENDATION — Route A / R1

**Freeze the topology-robustness problem and build a system-robustness paper.**

This ranks first because it has the best combination of scientific
defensibility, existing evidence, completion probability, and low additional
cost. It can make a clear claim:

> Relay-node failures induce communication/path reconfiguration and measurable
> heterogeneous mission degradation; robust training strategies must be judged
> by absolute F0/OOD performance, safety, maturity, and training-seed stability,
> not pooled return alone.

This claim is supported by the current evidence and does not require promoting
DRTP or TCR.

### 2. SECONDARY FALLBACK — Route A backbone with an optional Route-B upgrade / R3

If a target venue requires a method contribution, retain the Route-A paper
backbone as a standalone publishable unit and allow at most one separately
authorized architecture-level candidate later. The candidate must be allowed
to fail without invalidating the benchmark paper. It must not be another
return-weighting, curriculum, or gradient-projection variant.

R3 is a project-management fallback, not authorization to implement or train
anything now.

### 3. REJECTED / NOT RECOMMENDED — current Route B optimizer loop and Route C

Do not continue DRTP/TCR, design a third optimizer-level patch, or change the
scientific question merely because pooled values were attractive. The first
action would have high compute cost and high risk while adding little new
evidence; the second would discard a problem that is already scientifically
measurable.

## 9. Final project-level decision

```text
R1 — FREEZE PROBLEM / BUILD SYSTEM-ROBUSTNESS PAPER
```

Operational meaning:

- stop the DRTP and TCR paper-main routes permanently;
- use UTR-SG as the conservative stable robustness reference;
- use Mixed-50 only as a mature shared-policy reference until independent OOD
  evidence exists;
- report DRTP/TCR as pre-registered negative/instability evidence, never as
  successful superiority methods;
- keep MAPPO, matched SG, SPC, and older HAPPO/no-graph results separated by
  protocol compatibility;
- preserve all failed seeds and all historical `NO-GO`, `FAIL`, `STOP`, and
  `TECHNICAL_INVALID` conclusions;
- do not start new training, held-out evaluation, canonical seeds, or a new
  algorithm under this review.

This route decision is complete and intentionally stops before paper writing,
new implementation, or formal experiment authorization.
