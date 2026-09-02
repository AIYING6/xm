# Topology-severity formulation

A policy-free structural quantity is possible for the primary graph:

`S_f = 1 - P(G_f) / P(G_0)`, where `P` is the count of frozen legal Scout→Attacker target-information paths.

Here `P(G_0)=1`. A primary-edge cut has `S_f=1`; an off-path channel failure has `S_f=0`. This is a valid structural diagnostic, but it is binary and does not create an exposure/training prior. Structural severity is not learning value, and no sampler prior is defined in P0.
