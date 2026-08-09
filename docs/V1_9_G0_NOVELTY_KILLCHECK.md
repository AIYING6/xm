# v1.9 G0-R2 Novelty Kill-Check

**Status: `NOVELTY_KILLCHECK_PASS_WITH_NARROWED_CLAIM`.**

This is an adversarial, paper-by-paper audit for two-source PCRF-R2.  It does
not constitute performance evidence, implementation authorization, or a
publication claim.  The table records the author-provided primary-source
verification completed on 2026-08-09; it deliberately treats a close paper as
relevant even when its application differs from the UAV setting.

## 1. Strict kill criterion

For a paper to kill the remaining R2 headline directly, it would have to
combine all five properties below in one evaluated method:

| ID | Required property |
|---|---|
| R | recipient-specific execution information rather than global/team truth |
| S | direct/local perception and actually received communication remain source-separated, without a common-observation bypass |
| D | delivered-packet timing, staleness, reliability/confidence, or provenance is explicit |
| C | fusion is conditioned on source disagreement, conflict, or reliability rather than being ordinary attention alone |
| B | a strong information-matched, near-capacity-matched unified single-graph comparator tests the architectural factorization |

`B` is intentionally demanding: a broad baseline suite does not substitute for
an architecture-identification comparator with the same source-tagged raw
inputs.  A complete `R+S+D+C+B` overlap was not found in the 12 nearest
verified works below.

## 2. Verified nearest-work matrix

`yes` means the property is explicit in the verified paper; `partial` means a
close but non-identical mechanism; `no` means it is absent or not its evaluated
mechanism.  The final column describes threat to the *remaining narrow claim*,
not a ranking of paper quality.

| Work | R | S | D | C | B | Remaining-overlap risk |
|---|:---:|:---:|:---:|:---:|:---:|---|
| [T2MAC (AAAI 2024)](https://arxiv.org/abs/2401.10973) | yes | yes | partial | yes | no | highest |
| [CDCMA (2026)](https://arxiv.org/abs/2604.03785) | yes | partial | yes | partial/yes | no | highest |
| [CoDe (AAAI 2025)](https://arxiv.org/abs/2501.05207) | partial/yes | partial | yes | partial | no | very high |
| [Communication-Aware MARL for Decentralized UAV Deployment (2026)](https://arxiv.org/abs/2603.16141) | yes | yes | no | no | no | high |
| [AsynCoMARL (2025)](https://arxiv.org/abs/2502.00558) | yes | partial | partial | no | no | medium-high |
| [CCGM (IEEE TCyb 2024)](https://doi.org/10.1109/TCYB.2024.3453892) | yes | yes | no | partial | no | medium-high |
| [MAAF (2024)](https://www.mdpi.com/2076-3417/14/21/10079) | partial | yes | no | no | no | medium-high |
| [ACUTE (2022)](https://www.mdpi.com/2079-9292/11/24/4204) | yes | yes | no | no | no | medium |
| [DACOM (AAAI 2023)](https://ojs.aaai.org/index.php/AAAI/article/view/26389) | partial | partial | yes | no | no | medium |
| [VIL2C (AAAI 2026)](https://ojs.aaai.org/index.php/AAAI/article/view/40234) | yes | partial | yes | partial | no | medium-high |
| [MAGI (AAAI 2024)](https://ojs.aaai.org/index.php/AAAI/article/view/29682) | partial | no | partial | no | no | medium |
| [MAGEC (IROS 2024)](https://arxiv.org/abs/2403.13093) | partial/yes | no | partial | no | no | medium |

**Verdict:** no row has all five `yes` entries.  Thus the strict kill criterion
does not terminate PCRF-R2.  It does terminate any broad claim that merely
names source separation, conflict-aware fusion, delayed messages, graph MARL,
or UAV communication as its novelty.

## 3. What is already prior art

The following statements are prohibited in all future v1.9 writing:

- “We are the first to separate local perception and communication.”
- “We are the first to fuse conflicting observed and received evidence.”
- “We are the first to handle stale or delayed communication.”
- “We are the first recipient-specific graph MARL method for constrained UAV communication.”
- Any novelty claim based only on attention, gating, graph communication,
  message reliability, relay failure, or robustness.

T2MAC is the closest challenge to source separation plus disagreement-aware
evidence integration.  CDCMA and CoDe are the closest challenges to a claim
about stale/delayed communication.  Communication-Aware UAV MARL and
AsynCoMARL are first-tier nearest works for the decentralized actor contract.
These five works must receive substantive treatment in the final related-work
and discussion sections; they may not be hidden in a generic baseline list.

## 4. Remaining, deliberately narrow scientific question

The only currently defensible R2 question is:

> Under a strict recipient-specific and delivery-grounded actor-information
> contract, does retaining the provenance of directly perceived target evidence
> and actually delivered/cache-valid communication until fusion improve
> decentralized UAV decision-making under their temporal or semantic
> inconsistency, relative to an equally informed, near-capacity-matched unified
> single-graph encoder?

The candidate contribution therefore lies in the conjunction of:

1. an auditable actor contract tied to actual delivery/cache validity;
2. P/C evidence sources whose target-related content cannot bypass the split
   through shared context;
3. a legal, exact-neutral conflict deviation using only source availability,
   content disagreement, delivered age, and confidence; and
4. a matched single-graph causal comparator that receives every source tag and
   conflict-relevant raw field.

This is a **hypothesis and experimental design**, not evidence that the
architecture is superior.  A failure against the matched single graph, absent
conflict-specific behavior, or an information-parity failure ends the headline
claim rather than motivating more modules.

## 5. G0-R2 release implication

The literature condition for the G0-R2 theory/comparator freeze is met.  This
audit alone does not authorize source-code changes, D0-R2, D1-R2, D2, GPU use,
formal training, held-out evaluation, OOD, ablation, or manuscript revision.
Those actions require their own explicit authorization after the final G0-R2
freeze is recorded.
