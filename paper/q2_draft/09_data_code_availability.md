# 9. Data and Code Availability

The reproducibility package should be released with the manuscript in an anonymous or public repository consistent with the target journal's policy. The minimum archive is:

1. the exact SG actor/critic implementation and DRTP sampler update;
2. frozen configuration files, PPO settings, topology-group definitions, nominal anchor, and information-boundary specification;
3. evaluation-tape manifests, episode namespaces, hashes, and condition definitions;
4. final-checkpoint manifests and SHA256 values for every reported method/seed/budget cell;
5. raw evaluation records and the aggregation scripts used for tables and figures;
6. telemetry schema for adjacency, path composition, task-support source, trigger validity, terminal reason, timeout, collision, and constraint flags;
7. the evidence ledger, claim boundary, historical NO-GO/FAIL reports, and a README explaining which artifacts are non-comparable legacy material.

No generated result is silently replaced by a selected intermediate checkpoint. Development and held-out contracts remain separate in the archive. If an underlying simulator or dataset has redistribution restrictions, the release should provide its identifier, license, retrieval instructions, and the scripts needed to reconstruct the legal evaluation interface rather than redistributing restricted content.

This section is a release checklist, not a claim that every artifact is already public. Before submission, the placeholder wording must be replaced by the actual repository/DOI and license information.
