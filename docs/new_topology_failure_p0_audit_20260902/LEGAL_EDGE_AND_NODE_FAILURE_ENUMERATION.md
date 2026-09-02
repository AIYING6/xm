# Legal edge and node failure enumeration

The following candidates are enumerated from actual blue-team channels; their masks are deterministic and policy-independent. A future implementation would have to apply the mask **before both message delivery/cache updates and graph construction**. The current OOD prune hook occurs after some cache processing, so it is insufficient by itself as a strict information-failure interface.

| Candidate | Kind | Masked directed channels | Nominal S→A task path remains | Mask hash |
| --- | --- | --- | --- | --- |
| TD-AR | single_directed_edge | Attacker->Relay | True | 584342571251 |
| TD-AS | single_directed_edge | Attacker->Scout | True | 0f17ab5bd783 |
| TD-RA | single_directed_edge | Relay->Attacker | False | 65e199da9184 |
| TD-RS | single_directed_edge | Relay->Scout | True | ac97342a4adb |
| TD-SA | single_directed_edge | Scout->Attacker | True | 9a5a82b3c02d |
| TD-SR | single_directed_edge | Scout->Relay | False | b845189956a5 |
| TD-RX | relay_inbound_partial | Attacker->Relay, Scout->Relay | False | 7e2c3a1ae4e1 |
| TD-RT | relay_outbound_partial | Relay->Attacker, Relay->Scout | False | 7dc378ab67d1 |
| TD-RN | full_relay_node | Attacker->Relay, Relay->Attacker, Relay->Scout, Scout->Relay | False | 5ab83bcf11bd |
| TD-CUT | compound_primary_cut | Relay->Attacker, Scout->Relay | False | 382d2c8fabb4 |

This enumeration is descriptive only. It neither implements the mask nor authorizes a new benchmark.
