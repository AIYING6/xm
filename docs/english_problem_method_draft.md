# English Problem Formulation and Method Draft

Date: 2026-07-13

## Problem Formulation

We consider a cooperative pursuit task with \(N\) pursuer UAVs and \(M\) maneuvering targets. In the current experimental setting, \(N=3\) and \(M=1\). At time step \(t\), the motion state of pursuer \(i\) is denoted as \(x_i^t=(p_i^t,\psi_i^t,v_i^t,\eta_i^t)\), where \(p_i^t\) is the two-dimensional position, \(\psi_i^t\) is the heading angle, \(v_i^t\) is the speed, and \(\eta_i^t\) denotes the remaining energy or platform-specific state variable. The target state is denoted as \(x_{\mathrm{tar}}^t=(p_{\mathrm{tar}}^t,\psi_{\mathrm{tar}}^t,v_{\mathrm{tar}}^t)\). Each pursuer selects a discrete action \(a_i^t\) according to its local observation \(o_i^t\) and graph information \(G^t\). The action space consists of turning and acceleration/deceleration combinations.

### Centralized Training and Decentralized Execution

The policy is trained under the centralized training and decentralized execution paradigm. During training, a centralized critic \(V_\phi(s^t)\) uses the global state \(s^t\), which contains all pursuer and target states. During execution, each agent only uses its local observation and graph-encoded representation. The learning objective is to maximize the expected discounted team return:

```text
max_theta E[ sum_{t=0}^{T} gamma^t r^t ].
```

### Limited-Communication Graph

Limited communication is modeled by a communication radius \(R_c\). The communication reachability between pursuers \(i\) and \(j\) is defined as:

```text
I_ij^comm = I( ||p_i^t - p_j^t||_2 <= R_c ).
```

If the distance between two pursuers is larger than \(R_c\), their direct teammate edge is unavailable, and the corresponding teammate-observation slot is masked to zero. The dynamic graph used by the policy is denoted as \(G^t=(V^t,E^t)\), where nodes include pursuers and the target. Edges among pursuers are constrained by the communication radius. The target node is retained as a task-relevant observation node, while the edge feature records communication reachability. The main evaluation uses \(R_c \in \{4,6,8,10\}\).

### Reward and Evaluation Metrics

The reward consists of target-approaching reward, individual distance reward, heading reward, successful interception reward, collision penalty, and timeout-related penalty. The evaluation metrics include success rate, collision rate, timeout rate, and average episode length. Collision rate is emphasized as the main safety metric. An episode is counted as successful if any pursuer reaches the target capture radius within the time limit. A collision is counted if the distance between pursuers is below the safety threshold. An episode is counted as timeout if the maximum number of steps is reached without successful capture.

## Method

### Overview

The proposed method is denoted as EA-RG-MAPPO-S, namely Edge-Aware Role Graph MAPPO with Staged random-radius fine-tuning. It contains a local-observation encoder, an edge-aware role graph encoder, a centralized critic, and a staged random-radius fine-tuning procedure. The actor input is the concatenation of the local observation representation and the graph representation, while the critic uses the centralized global state.

### Role Graph Construction

At each time step, a dynamic graph \(G^t=(V^t,E^t)\) is constructed. The node set includes pursuer nodes and the target node. Each node contains normalized position, heading, speed, and platform-related state features. A role indicator is used to distinguish UAV nodes from target nodes. The node feature and role embedding are concatenated before entering the graph encoder:

```text
h_i^0 = f_in([x_i, Emb(role_i)]).
```

The role graph allows the model to distinguish teammates from the target, avoiding a homogeneous treatment of all graph nodes.

### Relative Edge-Feature Enhanced Attention

For the directed edge from node \(i\) to node \(j\), a relative edge feature vector \(e_{ij}\) is constructed:

```text
e_ij = [
  Delta x_ij,
  Delta y_ij,
  d_ij / d_max,
  d_ij / R_c,
  cos(beta_ij),
  sin(beta_ij),
  Delta v_ij^x,
  Delta v_ij^y,
  I_ij^comm,
  I_j^target
].
```

Here \(d_{ij}\) is the distance between nodes, \(d_{\max}\) is the environment-scale normalization constant, \(\beta_{ij}\) is the relative bearing, \(I_{ij}^{comm}\) indicates communication reachability, and \(I_j^{target}\) indicates whether node \(j\) is the target. The edge-aware attention score is computed as:

```text
score_ij = LeakyReLU( a^T [W h_i, W h_j] ) + g_e(e_ij),
```

where \(g_e\) is an edge-feature scoring network. A masked softmax is then applied over reachable neighbors:

```text
alpha_ij = exp(score_ij) / sum_{k in N_i} exp(score_ik),  j in N_i.
```

The node representation is updated by:

```text
h_i' = tanh( sum_{j in N_i} alpha_ij W h_j ).
```

Compared with standard GAT, which computes attention only from node embeddings, EA-RG-MAPPO-S directly uses distance, bearing, velocity difference, and communication reachability to adjust neighbor weights. This design makes the graph policy more aware of physical relations and communication constraints.

### MAPPO Optimization

The policy network outputs the action distribution \(\pi_\theta(a_i|o_i,G)\) for each agent. MAPPO is used with the clipped surrogate objective. The probability ratio is:

```text
rho_i^t(theta) = pi_theta(a_i^t | o_i^t, G^t) /
                 pi_theta_old(a_i^t | o_i^t, G^t).
```

The policy loss is:

```text
L_policy = - E[ min(
  rho_i^t A_i^t,
  clip(rho_i^t, 1-epsilon, 1+epsilon) A_i^t
) ].
```

The total loss is:

```text
L = L_policy + c_v L_value - c_H L_entropy + c_aux L_aux.
```

\(L_{aux}\) is an optional auxiliary loss. Since the current target-intent branch does not achieve reliable balanced accuracy, the main conclusions do not depend on that auxiliary branch.

### Staged Random-Radius Fine-Tuning

Training only under a fixed communication radius may make the policy over-adapt to a single communication topology. This paper uses a two-stage training strategy. In the first stage, the edge-aware role graph policy is trained under a fixed communication radius \(R_c=8\) to learn basic coordination. In the second stage, the policy is initialized from the first-stage checkpoint and fine-tuned with a smaller learning rate. For each episode, the communication radius is sampled from:

```text
R_c ~ U(4, 10).
```

The purpose of this stage is to improve adaptation to different communication topologies rather than merely increasing the total training time.

## Boundary for Later Use

```text
This method draft describes the current 2D limited-communication pursuit implementation.
It provides a reusable representation and training structure for later LAG/JSBSim or 6DOF migration, but it is not itself a completed 6DOF air-combat validation.
```
