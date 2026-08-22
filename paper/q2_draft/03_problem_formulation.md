# 3. Problem Formulation

We consider a heterogeneous team with Scout, Relay, and Attacker roles and a target. The directed adjacency convention is `A[receiver, sender]`: entry `A[i,j]` indicates that receiver `i` can use a legal relation from sender `j`. Perception, communication, and task-support relations are generated from the frozen S2 environment and remain subject to local legality.

Let `G_t` denote the communication–task graph and `J` the mission score. A nominal episode has no Relay failure. In a failure episode, the prescribed Relay node is unavailable during the frozen onset/duration condition. The key event is:

`G_t^comm -> G_{t+}^comm`,

followed by a change in path composition, support-source availability, and coordination geometry. The analysis does not assume that all target information disappears. In particular, a legal direct Scout-to-Attacker path may remain available after Relay failure.

The primary paired endpoint is the nominal–failure degradation `Delta_J = J_nominal - J_failure`, accompanied by absolute `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`, timeout, collision, constraint violation, exposure, and topology/path telemetry. OOD conditions vary failure timing, duration, and their compound combinations. Overall performance retains every scheduled episode, including episodes that terminate before failure onset. Trigger validity is assessed separately among episodes alive immediately before scheduled onset.

The policy is decentralized at execution. Actors receive only the frozen legal local observation, node/edge features, roles, and adjacency. Training-sampler labels, failure labels, global routes, future links, and hidden simulator truth are not actor inputs.
