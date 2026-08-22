# 8. Conclusion

We studied heterogeneous UAV coordination when a Relay failure reorganizes legal communication and task-support paths. DRTP-SG-MAPPO preserves the matched Single-Graph MAPPO architecture and changes only the training distribution over predefined topology-perturbation groups. The historical evidence shows substantial average and median robustness gains across F0 and OOD conditions, but it also shows meaningful sensitivity to training initialization, including an adverse held-out seed and non-uniform safety outcomes.

The appropriate conclusion is therefore bounded: DRTP is a high-upside, seed-sensitive topology-perturbation training strategy for the studied three-UAV setting. It is not a universally stable or guaranteed robust method. Reporting the full seed distribution, absolute performance, safety, exposure validity, and topology/path mechanism is essential for making that conclusion reproducible.
