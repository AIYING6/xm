# GO/NO-GO tree

```text
Benchmark semantics and redundant legal paths valid?
├─ no  -> STOP / redesign benchmark
└─ yes
   ├─ failure equivalence has >=3 recoverable classes and clean R/C/I tiers?
   │  ├─ no  -> STOP / redesign graph
   │  └─ yes
   │     ├─ external comparators map fairly and information boundaries pass?
   │     │  ├─ no  -> redesign before learning
   │     │  └─ yes
   │     │     ├─ plain/UTR learns nominal and Tier-R task?
   │     │     │  ├─ no  -> environment/metric failure
   │     │     │  └─ yes
   │     │     │     ├─ one pre-frozen candidate passes pilot?
   │     │     │     │  ├─ no -> benchmark-only/negative-study decision; no blind tuning
   │     │     │     │  └─ yes
   │     │     │     │     ├─ independent cohort repeats Level-1/2 direction?
   │     │     │     │     │  ├─ no -> mixed-result claim only
   │     │     │     │     │  └─ yes -> confirmatory, OOD and scale evidence
```
