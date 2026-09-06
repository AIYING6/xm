# DRTP reviewer attack list and evidence-ready responses

| Likely question | Evidence / response required |
|---|---|
| Why not just use MAPPO/HAPPO? | State the matched SG-MAPPO/UTR backbone and restrict the contribution to reset-side topology allocation; add any claimed external baseline only when protocol-matched evidence exists. |
| Is DRTP merely curriculum learning? | Explain that support is frozen, selection is reset-side and feedback-driven, and no temporal stage or reward shaping is introduced. |
| Is it just PLR with another name? | Use the completed matched PLR-style A/B table and mechanism map; do not make this claim before those results are available. |
| Why should topology be represented in groups? | Show the condition taxonomy and that allocation operates at a failure-semantic group level, while each group retains multiple frozen members. |
| Do all seeds improve? | No. Report paired distributions and cohort summaries; explicitly avoid universal dominance language. |
| Does DRTP always improve safety? | Report timeout and collision separately. Make only the safety claim supported by the final tables. |
| Could test conditions leak into training? | Cite the fixed tapes, manifests, training-access prohibition and distinct training/evaluation seed streams. |
| Is the method robust beyond the nominal benchmark? | Use structural and parameter held-out endpoints, keeping the claim limited to those tested shifts. |
| Does the method scale? | Use the frozen 6-UAV study only after it completes; do not extrapolate to arbitrary swarm sizes. |
| Are reported gains due to tuning? | State frozen constants, fixed 10M endpoint, no checkpoint promotion, fresh cohorts and separate A/B analyses. |
| Why no real flight test? | Position the work as simulation-based algorithmic evidence; do not claim deployment readiness. |

