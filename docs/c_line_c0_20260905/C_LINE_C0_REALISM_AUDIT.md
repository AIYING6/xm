# C-Line C0 realism audit

| Candidate semantic | Classification | Evidence and boundary |
|---|---|---|
| Multi-hop UAV relay routing with limited link capacity and multiple simultaneous connections | Source-supported | Javad-Kalbasi and Valaee formulate route refreshment with limited air-to-air capacity and connection migration in a UAV relay network (IEEE ICC Workshops 2021, DOI: `10.1109/ICCWorkshops50388.2021.9473723`). |
| Reconfiguration after UAV failure with service-disruption and operating-time cost | Source-supported | Yuan et al. study online UAV network reconfiguration after failures, changing connectivity and trajectories (Computer Networks 263, 2025, DOI: `10.1016/j.comnet.2025.111210`). |
| Hard information-freshness requirements | Source-supported | Li et al. study schedulability under per-source maximum-AoI thresholds rather than merely a soft age reward (IEEE/ACM ToN 30(5), 2022, DOI: `10.1109/TNET.2022.3156866`). |
| Disruption-free migration consuming advance capacity | Source-supported at the concept level | The 2021 UAV relay work explicitly derives a condition for disruption-free connection migration. The exact two-slot latency in C0's toy is not claimed native. |
| Discrete slots, unit relay capacity, two named services, fixed priorities 6 and 10 | Reasonable abstraction only | These make a minimal proof readable. They are not measurements from the current UAV simulators and cannot become a performance-model claim without a separately frozen deployment model. |
| Current repository natively supports controllable relay activation, route selection, capacity allocation, and migration | False | `redundant_topology_uav_env.py` states that relay actions are ignored; the B P1.5 audit already found no transition-effective relay control. The 3D environment has message age and dynamic communication but no service-routing/migration action interface. |

## Result

The broad problem semantics are real, but the current simulator is only a reusable physical/freshness substrate, not a native C-line implementation. Any later environment must be introduced openly as a new, constrained benchmark; it cannot be represented as a minor unmodified extension of the existing task.
