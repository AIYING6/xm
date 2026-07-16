# Journal Template Migration Plan

Date: 2026-07-13

Purpose:

```text
Convert the current English LaTeX manuscript into a target-journal submission package after the first target is selected.
This plan keeps the current article-style paper_latex_en/ project intact until the journal choice is confirmed.
```

## Current Source Package

Primary source:

```text
paper_latex_en/main.tex
paper_latex_en/sections/*.tex
paper_latex/references.bib
results/latex_*.tex
results/figures/*.png
```

Current readiness:

```text
The English manuscript has a complete title, abstract, keywords, seven main sections, and appendix experiments.
The current main text has about 3175 words excluding appendix, and about 3831 words including appendix.
The current environment cannot verify PDF rendering because xelatex/latexmk/bibtex are unavailable.
```

## Shared Migration Checklist

Do these steps for any selected journal:

```text
1. Create a new target-specific folder, for example paper_latex_en_drones/ or paper_latex_en_aerospace/.
2. Copy the current English sections into the target folder without changing experimental claims.
3. Replace the generic article class with the target journal class/template.
4. Replace author placeholder, affiliation, corresponding author, and ORCID fields.
5. Add Data Availability, Code Availability, Funding, Conflict of Interest, and Author Contributions statements as required.
6. Convert figure/table placement to the target journal style.
7. Convert bibliography style from plain to the target journal style.
8. Compile locally in a LaTeX-capable environment and fix float overflow, table width, and reference formatting.
9. Run all project gates after template migration.
```

Keep these boundaries unchanged:

```text
1. Do not describe the current work as validated full 6DOF air combat.
2. Do not describe missile, radar, or human-UAV teaming as current experimental components.
3. Do not claim high-accuracy target intent recognition.
4. Keep the main contribution as edge-aware role graph coordination under limited communication.
```

## Route A: Drones

Use when:

```text
The first priority is the closest UAV/drone topical fit and a practical first submission route.
```

Title style:

```text
Edge-Aware Role Graph MAPPO for Robust Multi-UAV Pursuit under Limited Communication
```

Abstract emphasis:

```text
1. Multi-UAV pursuit under limited communication.
2. Communication-radius robustness.
3. Collision reduction as a safety-oriented metric.
4. Two-dimensional pursuit as a first-stage validation before 6DOF migration.
```

Required language edits:

```text
1. Replace broad air-combat wording with UAV pursuit / adversarial pursuit unless it appears in future work.
2. Expand the introduction sentence on drone swarm applications.
3. Add a short paragraph on why communication-radius masking is relevant to real UAV networks.
4. Keep LAG/JSBSim as future validation, not current evidence.
```

Recommended appendix placement:

```text
1. Keep seed-paired CI table in appendix.
2. Keep speed robustness in appendix.
3. Keep edge-feature masking as mechanism diagnostic in appendix.
```

Risk:

```text
Open-access APC and possible perception risk around MDPI should be discussed with the adviser before submission.
```

## Route B: Aerospace

Use when:

```text
The adviser prefers an aerospace engineering framing and the work is positioned as UAV cooperative decision-making.
```

Title style:

```text
Limited-Communication Multi-UAV Cooperative Pursuit via Edge-Aware Role Graph Reinforcement Learning
```

Abstract emphasis:

```text
1. Aerospace UAV cooperative guidance / decision-making.
2. Graph attention enhanced by physical edge relations.
3. Evaluation across communication radii and target speeds.
4. Explicit limitation that the current simulator is a 2D decision-layer abstraction.
```

Required language edits:

```text
1. Add more detail on platform heterogeneity in the environment section.
2. Explain that actions are decision-layer commands rather than full flight-control inputs.
3. Strengthen the discussion of future 6DOF integration.
4. Avoid using terms that imply weapon engagement validation.
```

Recommended appendix placement:

```text
1. Move training settings near the experiment setup if the template allows large tables.
2. Keep paired CI and speed robustness as appendix tables.
3. Consider moving edge-feature masking to supplementary material if page limits are strict.
```

Risk:

```text
Reviewers may ask for flight dynamics. The response should be that this paper validates the decision and representation layer, while 6DOF migration is future work unless an additional LAG/JSBSim experiment is completed.
```

## Route C: Journal of Intelligent & Robotic Systems

Use when:

```text
The preferred framing is intelligent robotic systems / unmanned systems rather than aerospace-only publishing.
```

Title style:

```text
Edge-Aware Role Graph Multi-Agent Reinforcement Learning for Communication-Constrained Multi-Robot Pursuit
```

Abstract emphasis:

```text
1. Multi-robot/UAV pursuit under communication constraints.
2. Edge semantics for spatial and communication relations.
3. Safety and stability measured by collision rate and seed variance.
4. Reusable representation layer for more realistic unmanned-system simulators.
```

Required language edits:

```text
1. Reduce air-combat terminology in introduction and conclusion.
2. Add multi-robot coordination framing before UAV-specific details.
3. Expand related work on graph MARL and communication-constrained coordination.
4. Present the environment as an unmanned-system abstraction, not a combat simulator.
```

Recommended appendix placement:

```text
1. Keep all appendix experiments if page limits permit.
2. If page limits are strict, keep paired CI in the main appendix and move edge masking to supplementary notes.
```

Risk:

```text
Robotics reviewers may expect stronger benchmark comparison. The current evidence should be positioned as a reproducible custom UAV pursuit benchmark with clear limits.
```

## Target Selection Decision Rule

```text
Choose Drones if topical fit and practical submission speed matter most.
Choose Aerospace if the adviser wants aerospace-engineering alignment.
Choose JIRS if the adviser prefers a broader robotics/unmanned-systems venue and is comfortable with a potentially stricter systems review.
Do not choose RAS/EAAI as first target unless LAG/JSBSim or another stronger validation is added.
```

## Post-Migration Gates

Run after any target-template migration:

```bash
python scripts/build_paper_assets.py
python scripts/check_latex_project.py
python scripts/check_paper_claim_consistency.py
python scripts/check_english_latex_consistency.py
python scripts/check_paper_text_risk.py
python scripts/check_reproducibility_artifacts.py
python scripts/audit_english_manuscript_readiness.py
```

Additional manual gate:

```text
Compile the target LaTeX project to PDF in a LaTeX-capable environment and inspect:
1. title/author block;
2. abstract and keywords;
3. figure resolution and captions;
4. table width and page breaks;
5. bibliography style;
6. appendix placement;
7. declarations required by the selected journal.
```
