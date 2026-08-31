# DRTP English Manuscript Red-Team Review

## Review setup

- **Input scope:** the complete English Markdown manuscript in `paper/q2_final_en/` (editorial canon, abstract, problem formulation, introduction/related work, method, experiments, discussion, conclusion, and references).
- **Assessment boundary:** this is a reviewer-style pre-submission stress test, not an editorial decision or an author rebuttal. The supplied package does not include a target-journal template, rendered English figures/tables, an English supplementary document, or a live anonymous repository.
- **Shared manuscript claim summary:** within a frozen relay-failure UAV coordination task, bounded adaptive topology-perturbation reweighting (DRTP) improved primary mission-score endpoints relative to matched uniform reweighting (UTR) in a prospective five-seed formal cohort, but did not reproduce its direction in a separately completed independent cohort.
- **Visible evidence base:** matched UTR--DRTP design; 10M final checkpoints; five formal training seeds; a paired 12-condition tape; condition, safety, and trigger-validity reporting; a NoGraph external reference; an independent three-method cohort; cross-tape checks; post hoc unseen-member evaluation; and a bounded discussion of post-formal stabilization stress tests.
- **Missing materials affecting confidence:** source-level per-seed supplementary tables/figures in English, rendered figure/table verification, exact anonymous-repository access, release metadata, and target-journal instructions are not part of this packet.

## Reviewer 1 — technical-soundness / technical-failings emphasis

### Overall assessment

The manuscript is unusually transparent for an algorithmic MARL study: it preserves the negative independent cohort, keeps training seed as the statistical unit, separates the primary matched ablation from the NoGraph reference, and does not convert telemetry into causal mechanism. The central formal-cohort comparison is technically much stronger than a conventional seed-averaged leaderboard claim. The same transparency, however, makes the central limitation decisive: the headline benefit is not yet reliable across completed training cohorts.

### Who would be interested in the results, and why

Researchers studying cooperative MARL, UAV coordination, and robustness reporting would be interested because the paper treats relay failure as a legal path-reconfiguration problem and shows both the upside and non-replication of a controlled adaptive-sampling intervention.

### Major strengths

- UTR and DRTP share the policy backbone, PPO, reward, perturbation support, nominal anchor, budget, and actor information boundary (Sections 4 and 5.1).
- The manuscript does not pool the formal and independent cohorts into an artificial \(n=10\) confirmation (Section 5.1).
- Safety and evaluator validity are reported separately from mission score (Section 5.5).

### Major concerns

**R1-M1 — [experimental design / claim moderation]**

- **Claim pointer:** DRTP is presented as having formal-cohort upside but unresolved training-cohort sensitivity.
- **Evidence pointer:** Sections 5.3 and 5.7; Sections 6.1--6.2; Conclusion.
- **Concern:** The independent cohort reverses every aggregate DRTP-minus-UTR task endpoint and includes a catastrophic DRTP seed. The manuscript correctly discloses this, but its title, abstract, and contribution hierarchy must continue to make the reliability limitation co-equal with the formal gain. Any wording that treats the formal cohort as a general method validation would not be supported.
- **Resolution test:** retain the current cohort-bounded language throughout the title, abstract, results headers, conclusion, figure captions, and cover letter; provide a concise side-by-side formal-versus-independent evidence table in the English supplement.

**R1-M2 — [experimental design / causal interpretation]**

- **Claim pointer:** the primary comparison estimates adaptive relative to uniform reweighting.
- **Evidence pointer:** Sections 1, 3.4, 5.1, and 6.1.
- **Concern:** The formal cohort does not include a concurrently trained fixed non-uniform sampler. The later SNR arm belongs to a different cohort and cannot identify whether online adaptation is necessary relative to a fixed non-uniform allocation. The manuscript states this limitation, but a reviewer will test every result sentence for accidental stronger language.
- **Resolution test:** preserve the UTR--DRTP contrast as the only causal comparison; label SNR and NoGraph as contextual evidence only; include an explicit “can answer / cannot answer” comparator table in the English supplement.

**R1-m1 — [safety reporting]**

- **Claim pointer:** DRTP reduces timeout while slightly increasing collision in the formal cohort.
- **Evidence pointer:** Sections 5.3--5.5 and 6.4.
- **Concern:** The aggregate trade-off is clear, but a technical reader needs direct access to the complete condition-by-seed safety denominators and the concentration of the collision increase in seed 2304.
- **Resolution test:** expose the existing full formal condition and safety table as an English Supplementary Table, including pre-onset terminations and risk-set trigger denominators.

### Assessment against Nature-style criteria

- **Originality:** the original element is the frozen relay-failure/path-reconfiguration task plus controlled training-distribution comparison, not graph attention or PPO themselves.
- **Scientific importance:** useful to the MARL reliability conversation; broader importance is constrained by the three-UAV simulation and replication reversal.
- **Interdisciplinary readership:** limited but plausible across learning, autonomy, and networked control if the opening keeps the path-reconfiguration explanation concrete.
- **Technical soundness:** formal-cohort inference is careful; cross-cohort reliability is explicitly not established.
- **Readability for nonspecialists:** the main argument is clear, but the distinction among formal, independent, external-reference, and post hoc evidence must be visually obvious in the final rendered manuscript.

### Recommendation posture

Supportive of a carefully bounded application-oriented submission once the English supplementary evidence package and cohort-comparison presentation are complete.

## Reviewer 2 — originality / scientific-importance emphasis

### Overall assessment

The manuscript avoids common novelty inflation and presents a more credible story than a simple “new robust MARL method” paper. Its potential value is the combination of a specific relay-failure semantics, an isolated training-distribution contrast, and transparent reliability reporting. The risk is that readers may see DRTP as a composition of familiar ingredients--PPO/MAPPO, graph attention, EMA difficulty, exponentiated reweighting, and curriculum/domain-randomization ideas--unless the manuscript makes the task-specific scientific question, rather than the sampler formula alone, the primary advance.

### Who would be interested in the results, and why

The work will interest readers concerned with how structural communication faults affect distributed autonomy, and MARL researchers who value honest negative replication evidence alongside formal positive results.

### Major strengths

- The introduction distinguishes legal direct communication from total information loss (Sections 1 and 2.2).
- Related work does not claim novelty for graph MARL, PPO, or general robust optimization (Section 3).
- The evidence hierarchy prevents NoGraph, telemetry, and historical results from being presented as a performance leaderboard (Section 5.1).

### Major concerns

**R2-M1 — [novelty-significance]**

- **Claim pointer:** DRTP is positioned as bounded adaptive reweighting for relay-failure topology/path reconfiguration.
- **Evidence pointer:** Sections 1, 3.1--3.3, and 4.3.
- **Concern:** The formula itself is incremental relative to prior group reweighting, active randomization, and curriculum ideas. The manuscript can still make a coherent contribution, but only if it foregrounds the controlled problem definition and evidence contract rather than implying a broad new robust-RL principle.
- **Resolution test:** make the opening contribution sentence and final title/abstract emphasize “formal gains and training-cohort sensitivity”; in the related-work table or supplement, map each inherited component to its prior source and state the task-specific difference.

**R2-M2 — [novelty-significance / reproducibility]**

- **Claim pointer:** the paper reports systematic stabilization stress tests as a reliability boundary.
- **Evidence pointer:** Section 6.3 and Supplementary Table S5 (referenced but not included in the current English packet).
- **Concern:** This material strengthens credibility, but it could read as an unstructured catalogue of failed variants if the supplement does not give each variant a frozen role, cohort, outcome, and non-claim boundary. Conversely, omitting it entirely would invite the question of why simple safeguards were not tried.
- **Resolution test:** provide one compact English S5 table with columns for intervention target, pre-frozen role, independent evidence, final status, and prohibited inference. Keep the main text to the existing short boundary paragraph.

**R2-m1 — [claim moderation]**

- **Claim pointer:** the formal cohort provides “formal gains.”
- **Evidence pointer:** Title, Abstract, Sections 5.3--5.4, and Conclusion.
- **Concern:** “Formal gains” is defensible only when visibly paired with the independent reversal. It should not be shortened to “robust gains” or “improved robustness” in a way that obscures the cohort qualifier.
- **Resolution test:** perform a final global wording sweep for “robust,” “stable,” “generalization,” “OOD,” “reliable,” and “DRO,” and maintain the editorial terminology ledger as the controlling document.

### Assessment against Nature-style criteria

- **Originality:** clear at the task-and-evidence-contract level; limited at the generic algorithmic-primitive level.
- **Scientific importance:** potentially useful evidence on reliability-aware MARL evaluation, but not an established general solution to robust coordination.
- **Interdisciplinary readership:** the path-reconfiguration framing gives a bridge to networked autonomy; the method details remain specialist.
- **Technical soundness:** claims are unusually restrained; the strength of the contribution depends on preserving that restraint after template migration.
- **Readability for nonspecialists:** good conceptual opening, but the term “topology-perturbation reweighting” should be paired with a simple schematic in the final PDF.

### Recommendation posture

Promising as a rigor-focused algorithmic application paper if its novelty is framed as a bounded task-and-evidence contribution rather than a universal stabilization advance.

## Reviewer 3 — interdisciplinary-readership / readability emphasis

### Overall assessment

The manuscript's strongest communication feature is its refusal to call relay failure a complete blackout when a legal direct path remains. This makes the problem intelligible outside the exact implementation. The English source, however, is not yet a complete submission artifact: it has no rendered figures or English supplement, and the reproducibility statement cannot be independently followed without the author-supplied anonymous release information.

### Who would be interested in the results, and why

Readers in autonomous systems, networked control, UAV communication, and MARL evaluation may care because the paper connects a concrete network-fault semantics to a controlled learning comparison and reports reliability failure rather than hiding it.

### Major strengths

- The abstract states both the formal positive results and independent negative result.
- The problem formulation explains legal information boundaries without relying on simulation-specific jargon alone.
- The conclusion does not introduce a new mechanism claim.

### Major concerns

**R3-M1 — [reproducibility / data-resource quality]**

- **Claim pointer:** the study is presented as audit-ready and reproducible.
- **Evidence pointer:** Method Section 4.4; Experimental protocol Section 5.1; internal audit scope; release gate is not included in the English manuscript packet.
- **Concern:** Code, manifests, tapes, checkpoints, hashes, and raw records are described elsewhere in the project, but the English packet contains neither a live anonymous repository nor a submission-ready Data/Code Availability statement. This is not evidence of non-reproducibility; it is not assessable until the author provides the external release link and policies.
- **Resolution test:** after journal selection, add a precise anonymous availability statement, external access test, artifact hash manifest, licensing/checkpoint policy, and final repository URL or reviewer-access route.

**R3-M2 — [figures-and-tables / writing clarity]**

- **Claim pointer:** readers can interpret the evidence hierarchy and the safety/reliability boundary.
- **Evidence pointer:** Sections 5.1, 5.5, 5.7, and 6; rendered English figures/tables are not supplied.
- **Concern:** The argument has several evidence strata--formal cohort, independent cohort, cross-tape diagnosis, NoGraph reference, unseen-member evaluation, and S5 stress tests. Without a single visual timeline/evidence map and full English supplementary tables, nonspecialists may confuse them as one pooled experiment.
- **Resolution test:** include a one-page evidence hierarchy/timeline figure or table in the main manuscript, and ensure all detailed tables use the same cohort labels and explain that training seed is the independent unit.

**R3-m1 — [scope / claim moderation]**

- **Claim pointer:** the task has relevance to UAV coordination under communication failure.
- **Evidence pointer:** Sections 2, 5, 6.5, and Conclusion.
- **Concern:** The supplied evidence is limited to a lightweight three-UAV 3DOF simulation with predefined failure conditions. The manuscript states this limitation, but a broad audience needs a concise distinction between task-level insight and deployment readiness.
- **Resolution test:** retain the explicit simulation-only boundary in the abstract/conclusion and avoid operational claims about field deployment, real communication stacks, hardware-in-the-loop, or flight validation.

### Assessment against Nature-style criteria

- **Originality:** the framing is accessible and specific, although the technical primitives are familiar.
- **Scientific importance:** field-relevant; the practical impact is contingent on future validation beyond simulation.
- **Interdisciplinary readership:** strongest for adjacent autonomy and networked-systems readers, not yet for a very broad scientific audience.
- **Technical soundness:** the visible protocol is disciplined; release and rendered supplementary artifacts remain author-side completion items.
- **Readability for nonspecialists:** the text is understandable, but visual evidence organization is needed to prevent cohort and comparator confusion.

### Recommendation posture

Potentially clear for an application-oriented audience after the manuscript is rendered, supplemented, and linked to an externally testable anonymous release.

## Cross-review synthesis

### Consensus strengths

- The paper's most credible contribution is its controlled UTR--DRTP comparison within a concrete relay-failure/path-reconfiguration task, not a generic claim about graph MARL or robust RL.
- The formal protocol is unusually careful about parameter matching, final-checkpoint selection, training-seed reporting, safety, and trigger validity.
- Full disclosure of the independent reversal improves trust and makes the reliability limitation scientifically meaningful rather than hidden.

### Consensus technical risks

1. **CR-M1 — cross-cohort reliability boundary.** Raised by Reviewers 1 and 2. The independent reversal must remain equally prominent wherever formal gains are summarized. A side-by-side English table is required for reader comprehension, not a new training run.
2. **CR-M2 — narrow causal identification.** Raised by Reviewers 1 and 2. The formal result identifies bounded adaptive versus uniform reweighting only; it cannot establish online adaptation as necessary relative to every fixed non-uniform distribution.
3. **CR-M3 — English supplementary/release completion.** Raised by Reviewers 1 and 3. Per-seed safety, S5, full condition tables, rendering, and an externally testable anonymous release are needed before submission.

### Where emphasis differs across reviewers

- Reviewer 1 gives greatest weight to whether the evidence contract supports the causal and reliability statements.
- Reviewer 2 gives greatest weight to whether the contribution reads as a specific task-and-evidence advance rather than a recombination of known algorithmic primitives.
- Reviewer 3 gives greatest weight to whether readers can follow the evidence hierarchy and independently inspect the claimed reproducibility package.

### Broad-interest / significance readout

The current evidence supports field-specific interest in reliability-aware adaptive MARL and UAV coordination under structural communication faults. It does not by itself establish broad or deployment-ready impact. An application-oriented journal is a more natural fit than a venue requiring a universal algorithmic advance.

### Most important issues to resolve before the manuscript is released for submission

1. Create the English supplementary package, especially the formal-versus-independent comparison, full safety/condition tables, and compact S5 ledger.
2. Add a visual evidence hierarchy that prevents accidental cohort pooling and makes the primary causal contrast unmistakable.
3. Complete author-owned anonymous-release fields and validate the external reviewer-access path after a target journal is selected.
4. Perform a final wording and PDF/template audit so that “formal gain” is never decoupled from “independent non-replication.”

## Risk / unsupported claims

- The supplied evidence does **not** support stable superiority across training cohorts, strict OOD generalization, a general DRO guarantee, a causal mechanism for the seed/cohort reversal, or necessity relative to every fixed non-uniform sampler.
- The supplied packet does **not** provide a rendered English PDF, complete English supplementary material, or a live anonymous repository. Their final quality and accessibility are therefore not assessable here.
- No new experiment is required to address the main presentation risks identified above. Any future experiment would need a separate frozen contract and must not be used to overwrite the completed formal or independent cohorts.
