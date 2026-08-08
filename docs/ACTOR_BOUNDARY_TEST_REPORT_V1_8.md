# Actor boundary test report v1.8

**Command:** `D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/test_actor_boundary_v1_8.py`

**Result:** PASS — 14/14 tests.

## Covered checks

1. Unavailable teammate position is hidden.
2. Unavailable teammate velocity/status is hidden.
3. Delayed packet is unavailable before delivery.
4. Delayed packet becomes visible at delivery.
5. Dropped packet never enters cache.
6. Delivered packet snapshots sender fields at send time.
7. Cache does not refresh from simulator truth.
8. Target unavailable is zeroed except static target metadata.
9. Invalid endpoints produce no valid geometry.
10. Relation masks do not create provenance.
11. Pending packet payload is absent from the recipient view.
12. Critic shared-state changes are outside actor input construction.
13. Relay failure does not bypass cache provenance.
14. Vectorized recipient views equal the per-receiver reference builder.

The suite is an engineering gate only. It does not establish learning quality,
scientific superiority, or formal statistical evidence. Any future R4 change to
packet fields, cache rules, graph dimensions or masking order requires rerunning
this suite before a pilot.
