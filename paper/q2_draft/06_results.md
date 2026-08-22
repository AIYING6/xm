# 6. Results

## 6.1 Relay failure changes topology and mission support

The S1/S2 audits show that Relay failure changes legal path composition and task-support structure while legal direct alternatives can remain. The resulting mission degradation is therefore interpreted as a coordination/topology effect, not as evidence of complete information loss.

## 6.2 Main robustness performance

At the 3M development endpoint, pooled UTR versus DRTP values are respectively `147.157` versus `171.007` for nominal score, `127.929` versus `183.880` for F0, `120.607` versus `183.464` for OOD mean, and `103.149` versus `172.241` for OOD worst. Failure collision is `0.0136` versus `0.0014`, timeout is `0.8086` versus `0.5600`, and both constraint rates are zero. These pooled values are positive descriptive evidence, but the development contract remains NO-GO because seed/condition retention rules failed.

## 6.3 Seed-level effects

Across the five historical paired records, DRTP−UTR mean/median gains are +26.404/+29.804 for F0, +34.218/+26.305 for OOD mean, and +31.479/+23.688 for OOD worst. The nominal mean/median gain is +46.231/+40.794. These numbers coexist with seed1902 negative F0/OOD-mean deltas and held-out seed2002 severe reversal; all five records must be plotted.

## 6.4 Held-out reliability and safety

Held-out pooled DRTP versus UTR values are `221.493/168.893/170.147/144.758` versus `160.341/162.187/155.021/138.354` for nominal/F0/OOD mean/OOD worst. The held-out contract still FAILS: seed2002 has DRTP F0 `72.970` versus UTR `186.921`, OOD worst `53.597` versus `150.697`, and timeout `0.9064` versus `0.5145`. Collision is higher for DRTP in all three held-out seeds. The pooled upside cannot erase these reliability and safety outcomes.

## 6.5 OOD and mechanism presentation

The final figures should separate early/late timing, short/long duration, and compound conditions, then identify the worst condition per seed. Mechanism panels should show path switching, task-support source, and mission-score change rather than imply information restoration.
