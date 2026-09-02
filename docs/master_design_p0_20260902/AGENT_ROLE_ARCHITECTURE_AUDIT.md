# Agent-role architecture audit

All candidates use a directed layered task-support family `Scout -> Relay -> Terminal`. A path is only potential until a future semantic contract proves that its source information, relay forwarding and terminal action are needed by the task.

| Design | role composition | UAVs | legal potential paths | edge-disjoint route capacity | internally node-disjoint routes |
|---|---|---:|---:|---:|---:|
| A | Conservative | 4 | 2 | 2 | 2 |
| B | Recommended | 6 | 8 | 4 | 2 |
| C | Ambitious | 8 | 18 | 6 | 3 |

| Design | scientific richness | topology diversity | recoverability | scalability | implementation risk | training cost | external validity | paper ceiling |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: 1S+2R+1T | 3 | 3 | 3 | 2 | 5 | 5 | 3 | 3 |
| **B: 2S+2R+2T** | **5** | **5** | **5** | **4** | **3** | **3** | **5** | **5** |
| C: 2S+3R+3T | 5 | 5 | 5 | 5 | 2 | 1 | 5 | 5 |

## Recommendation

Select **B (6 UAV)** only after redesign: Scouts must have complementary sensing sectors/altitude/range, terminals must have complementary terminal capabilities or spatial responsibilities, and relays must be individually meaningful routing resources. If any duplicated role is interchangeable without changing task-information or mission semantics, B fails and must be redesigned rather than trained. A is a sanity scale; C is an eventual scale stress test, not the main formal scale.
