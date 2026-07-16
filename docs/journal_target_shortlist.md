# Journal Target Shortlist

Date: 2026-07-13

Purpose:

```text
Select realistic journal targets for the current EA-RG-MAPPO-S manuscript.
This is a submission-planning document, not a guarantee of JCR quartile, acceptance, or review outcome.
Before submission, verify the latest JCR/CAS partition through the university library or Web of Science.
```

## Current Manuscript Positioning

Recommended title direction:

```text
Edge-Aware Role Graph MAPPO for Robust Multi-UAV Pursuit under Limited Communication
```

Recommended claim boundary:

```text
1. Main claim: edge-aware role graph coordination improves robustness and reduces collisions under limited communication.
2. Evidence: 3 seeds, 300 episodes per seed, communication radii 4/6/8/10, speed robustness, edge-feature diagnostic, paired descriptive confidence intervals.
3. Do not claim: verified 6DOF air combat, missile/radar engagement, human-machine teaming, or high-accuracy target intent recognition.
```

## Recommended Submission Order

| Priority | Journal | Practical Fit | Current Evidence Sufficiency | Risk | Suggested Decision |
|---:|---|---|---|---|---|
| 1 | Drones | Very high | High | APC and MDPI perception risk | Best first target if open-access fee is acceptable |
| 2 | Aerospace | High | Medium-high | Aerospace readers may expect more flight-dynamics realism | Good first target if framing emphasizes UAV/aerospace decision-making |
| 3 | Journal of Intelligent & Robotic Systems | High | Medium-high | Fully OA; robotics reviewers may ask for stronger system realism | Good non-MDPI-style robotics target |
| 4 | IEEE Access | Medium | Medium-high | Broad venue; APC; contribution must be written very clearly | Fast fallback target |
| 5 | Robotics and Autonomous Systems | Medium | Medium | Stronger bar; may expect more robotics realism or public benchmark | Stretch after LAG/6DOF validation |
| 6 | Engineering Applications of Artificial Intelligence | Medium | Low-medium | High bar; explicitly values real-world/public-data validation | Stretch after adding public benchmark or stronger engineering validation |

## Candidate Notes

### 1. Drones

Official-page signals:

```text
Scope: drones/UAVs/UASs and related unmanned systems.
Impact factor shown on official page: 5.2.
Median publication time shown on official page: 48 days.
Quartile signal shown on official page: JCR Q2 in Remote Sensing.
```

Fit:

```text
This is the most direct topical fit because the journal explicitly targets drones and UAVs.
Our limited-communication multi-UAV pursuit framing is easier to justify here than in a general AI journal.
The current 2D pursuit simulation is likely acceptable if the paper is honest about future 6DOF extension.
```

Required edits before submission:

```text
1. Replace air-combat language with multi-UAV pursuit / adversarial pursuit.
2. Keep intent recognition as diagnostic/auxiliary only.
3. Add a paragraph explaining why 2D pursuit is a first-stage abstraction and how edge-aware graph design transfers to richer 6DOF settings.
4. Ensure all figures and tables are in English.
```

### 2. Aerospace

Official-page signals:

```text
Scope: peer-reviewed open access journal of aeronautics and astronautics.
Impact factor shown on official page: 2.5.
Median publication time shown on official page: 43 days.
Quartile signal shown on official page: JCR Q2 in Engineering, Aerospace.
```

Fit:

```text
This is a practical Q2-aligned target if the manuscript is framed as UAV cooperative decision-making under constrained communication.
A recent Aerospace article page lists a GAT-MAPPO cooperative guidance paper, which means the journal is receptive to graph-attention MARL in adversarial guidance settings.
The risk is that aerospace reviewers may ask why the current simulator is 2D and does not include flight dynamics.
```

Required edits before submission:

```text
1. Emphasize limited-communication robustness and collision reduction rather than generic MARL performance.
2. Add a short discussion comparing against GAT-MAPPO-style graph attention and explaining the edge-aware/role-graph distinction.
3. Make the 6DOF/LAG migration plan explicit but clearly marked as future work.
```

### 3. Journal of Intelligent & Robotic Systems

Official-page signals:

```text
Scope: theory and practice of intelligent systems and robotics.
Specific focus includes unmanned systems, robotics and automation, and human-robot interaction.
Impact factor shown on official page: 3.1 for 2025.
Submission to first decision median shown on official page: 12 days.
The journal page states that it includes a dedicated section for Unmanned Systems.
```

Fit:

```text
This is a credible robotics/unmanned-systems target.
The current paper should be written as a multi-robot coordination method, not as a weapons or full air-combat system.
It is also suitable if the adviser prefers a Springer robotics venue over MDPI.
```

Required edits before submission:

```text
1. Reframe the environment as multi-robot pursuit with UAV dynamics abstraction.
2. Add related work on multi-robot pursuit, graph MARL, and communication-constrained coordination.
3. Consider adding one more non-combat scenario name in the experiments, even if the underlying environment is the same.
```

### 4. IEEE Access

Official-page signals:

```text
Scope: multidisciplinary, online-only, gold fully open access journal across IEEE fields of interest.
The official page states a submission-to-publication time of 4 to 6 weeks.
Top listed categories include Computational & Artificial Intelligence, Communications Technology, and Signal Processing.
```

Fit:

```text
IEEE Access is practical if speed matters and APC is acceptable.
The manuscript must make the engineering application and reproducibility very clear because the venue is broad.
It is less topically precise than Drones/Aerospace/JIRS.
```

Required edits before submission:

```text
1. Tighten the contribution list and reproducibility appendix.
2. Include code/checkpoint/material availability statements if allowed by the adviser.
3. Avoid a niche air-combat title; use limited-communication multi-agent UAV coordination.
```

### 5. Robotics and Autonomous Systems

Official-page signals:

```text
Scope: robotics, with special emphasis on autonomous systems; includes theoretical, computational, and experimental aspects.
Impact factor shown on official page: 5.2.
Article publishing options include subscription with no publication fee, or optional open access APC.
Submission to first decision shown on official page: 32 days.
```

Fit:

```text
This is a stronger stretch target.
The current evidence is promising but may be considered too simulation-specific unless the paper adds a public benchmark, richer dynamics, or stronger robotics interpretation.
```

Required edits before submission:

```text
1. Add a stronger autonomous-systems framing.
2. Add LAG/JSBSim or another public benchmark if possible.
3. Provide more detailed failure analysis and reproducibility package.
```

### 6. Engineering Applications of Artificial Intelligence

Official-page signals:

```text
Scope: practical application of AI methods across engineering.
Impact factor shown on official page: 8.0.
The official page says papers should report novel AI contributions for real-world engineering applications and be validated using public data sets for replicability.
```

Fit:

```text
This is not the best first target for the current version.
It becomes realistic only if the work is strengthened with public benchmark validation, stronger engineering application framing, and perhaps a 6DOF/LAG experiment.
```

Required edits before submission:

```text
1. Add public benchmark or simulator validation.
2. Strengthen the AI novelty beyond applying graph attention to MAPPO.
3. Make the engineering application concrete and reproducible.
```

## Immediate Action Plan

```text
1. Choose Drones, Aerospace, or JIRS as the first target.
2. Convert paper_latex_en/ to the selected template.
3. Keep the title and abstract on limited-communication multi-UAV pursuit, not air combat.
4. Add the seed-paired CI table as appendix evidence.
5. Compile PDF in a LaTeX-capable environment and fix formatting before any submission.
```

## Source Notes

```text
Official pages checked on 2026-07-13:
https://www.mdpi.com/journal/drones
https://www.mdpi.com/journal/aerospace
https://link.springer.com/journal/10846
https://ieeeaccess.ieee.org/
https://www.sciencedirect.com/journal/robotics-and-autonomous-systems
https://www.sciencedirect.com/journal/engineering-applications-of-artificial-intelligence
```
