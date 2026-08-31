# 2. Problem formulation

## 2.1 Heterogeneous relay-failure coordination under a legal information boundary

We study a three-UAV cooperative interception task with fixed heterogeneous roles: a Scout (agent 0), a Relay (agent 1), and an Attacker (agent 2). The Scout acquires target information, the Relay can provide multi-hop communication support, and the Attacker uses legally available target information to form an attack window. The task is therefore not a collection of independent flight controllers: its feasible coordination depends jointly on motion, sensing, communication, and task-support relations.

At time \(t\), these relations are represented by a graph \(G_t=(V,E_t,X_t,Z_t)\), where \(V\) includes the three UAVs and the target, \(E_t\) contains legal sensing, communication, and task-support relations, and \(X_t\) and \(Z_t\) are node and edge features. We use a receiver-row adjacency convention: \(A_t[i,j]=1\) if receiver \(i\) may legally use a relation sent by \(j\). A sensing edge is determined only by the frozen sensing model. A communication edge must satisfy the physical range, node-state, and communication rules. A task-support edge records legally delivered information and active support; it is not an additional route for simulator ground truth.

The decentralized actor observes its own motion state and only legally available task information. In particular, a UAV that neither detects the target nor receives a fresh legal cache cannot reconstruct the true target state through graph messages. Failure labels, shortest paths, future edges, and simulator ground truth are excluded from actor input. A centralized critic is used only during training under the CTDE convention [14]; it does not enlarge the actor's execution-time information. This boundary makes the problem one of adapting coordination to legal relation changes, rather than exploiting a hidden failure indicator.

## 2.2 Relay-node failure as topology/path reconfiguration

A relay-node failure disables the Relay's sensing, transmission, and reception capabilities during a frozen interval beginning at \(t_f\) and lasting \(d_f\) steps, and removes the Relay-associated communication edges. Canonical F0 uses \(t_f=44\) and \(d_f=80\). Before the event, legal target information may follow the Scout--Relay--Attacker path. During the failure, a direct Scout--Attacker edge can remain legal when the physical rules permit it. The change is therefore

\[
0\rightarrow1\rightarrow2\quad\longrightarrow\quad0\rightarrow2,
\]

not an assumed universal information blackout. The object of adaptation is the composition of legal communication paths, the source of task support, and the resulting coordination geometry.

The frozen training universe contains a nominal condition \(N\), F0, and five two-member groups: early onset \(TE=\{(28,80),(36,80)\}\), late onset \(TL=\{(52,80),(60,80)\}\), short duration \(DS=\{(44,40),(44,60)\}\), long duration \(DL=\{(44,100),(44,120)\}\), and compound perturbations \(CP=\{(28,120),(60,120)\}\). The tuple gives onset and duration in environment steps. These ten onset--duration members are in the training sampler support. Consequently, the cross-perturbation endpoints used in the formal study are not strict out-of-distribution (OOD) metrics. A separate post hoc evaluation on six excluded onset--duration tuples is reported only as additional unseen-member evidence.

## 2.3 Estimands, safety outcomes, and technical validity

For condition \(c\), let \(J_c\) be the mean episode mission score. An episode score is the sum of stepwise rewards across the three UAVs. It includes team components for target approach, tracking, attack-window availability, legal communication connectivity, and information freshness; role components for Scout detection, Relay connectivity, and Attacker attack-window state; and penalties for energy use, collision, and constraint violations. Completion after a sustained attack window receives a terminal reward. Thus, a higher \(J_c\) indicates a more complete approach--information-support--attack-window--completion trajectory under the frozen reward contract; it is not a physical measure of distance, time, or communication throughput and cannot replace terminal safety outcomes.

The principal mission endpoints are

\[
J_{\mathrm{nominal}},\qquad J_{F0},\qquad
J_{\mathrm{pert,mean}}=\frac{1}{10}\sum_{c\in\mathcal C_{\mathrm{pert}}}J_c,\qquad
J_{\mathrm{pert,worst}}=\min_{c\in\mathcal C_{\mathrm{pert}}}J_c,
\]

where \(\mathcal C_{\mathrm{pert}}\) is the ten-member frozen perturbation family. We also report failure degradation \(D_c=J_{\mathrm{nominal}}-J_c\) and the paired training-seed difference \(\Delta J_c^{D-U}=J_c^{\mathrm{DRTP}}-J_c^{\mathrm{UTR}}\). Collision rate, timeout rate, constraint-violation rate, episode length, and pre-onset collision rate are reported alongside mission score.

Failure-trigger validity is evaluated within the risk set \(R_c\) of episodes still alive at the scheduled failure onset:

\[
V_{\mathrm{trigger},c}=
\frac{\#\{\text{episodes in }R_c\text{ with a correctly triggered failure}\}}
{|R_c|}.
\]

Episodes that terminate through a pre-onset collision remain in unconditional mission-score and safety denominators. They are excluded only from the conditional trigger-validity denominator because no failure can be injected after a legitimate termination. Training seed, rather than evaluation episode, is the independent unit for method comparison.
