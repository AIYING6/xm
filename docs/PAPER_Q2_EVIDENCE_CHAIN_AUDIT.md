# PAPER-Q2 Evidence Chain Audit

**Decision:** `EVIDENCE_CHAIN_PASS`
**Scientific training started:** no
**Independent unit:** training seed

## 1. Audited chain

The manuscript evidence chain is frozen as four linked layers:

1. **Upstream evidence:** development/held-out reports, topology mechanism report, REL-A0 reliability audit, archive/tape/checkpoint provenance recorded in those reports.
2. **Machine extraction:** P1 absolute tables, paired seed table, and canonical statistical JSON.
3. **Closeout evidence:** all absolute method×seed rows, paired deltas, contract-stratified summaries, reliability statistics, safety boundaries, and historical decisions.
4. **Manuscript routing:** claim–evidence matrix, figure-source manifest, section contracts, and legacy-source quarantine.

The machine lineage is stored in:

- `evidence_chain_manifest.json` — SHA256 and byte size for each frozen source and transformation script;
- `evidence_chain_edges.csv` — source → transformation → manuscript object links;
- `evidence_chain_audit.json` — executable audit result.

## 2. Machine checks

The verifier passed the following safeguards:

1. all hashed source files match the frozen manifest;
2. final main table is an identity-preserving export of the P1 machine table;
3. all five required paired seeds are present exactly once;
4. all 10 absolute UTR/DRTP method×seed rows reproduce the five paired deltas;
5. mean, median, sample SD, IQR, MAD, win count, and worst degradation recompute from seed rows;
6. development `n=2` and held-out `n=3` remain separate;
7. seed1902 and seed2002 negative outcomes remain intact;
8. `DRTP_Q2_LIMITATION_ONLY`, development `NO-GO`, and held-out `FAIL` remain preserved;
9. the legacy recovery manuscript remains quarantined;
10. the statistical prose table agrees with the machine JSON after correction.

## 3. Statistical transcription correction

The audit detected two errors in the earlier prose-only P1 statistics table:

| Metric | Incorrect prose MAD | Recomputed/canonical MAD |
|---|---:|---:|
| `J_F0` paired delta | 51.491 | 74.461 |
| `J_OOD_worst` paired delta | 16.136 | 68.938 |

The canonical values were already correct in `artifacts/paper_q2_p1/statistical_summary.json` and in the closeout reliability CSV. The prose table and its generator have now been corrected with an explicit note. No seed, raw value, mean, median, win count, worst degradation, historical decision, or scientific conclusion changed.

## 4. Evidence graph

```text
source reports + archive/tape/checkpoint provenance
                    ↓
       absolute method×seed rows (10)
                    ↓
          paired seed deltas (5)
                    ↓
  stratified statistics (n=2, n=3 separately)
                    ↓
 cross-stratum descriptive reliability summary
                    ↓
 claim matrix + figure sources + section contracts
```

No manuscript claim may skip a layer. A pooled episode result cannot substitute for a training-seed comparison, and a cross-stratum descriptive summary cannot substitute for confirmatory inference.

## 5. Remaining evidence limitations

- only two development and three held-out training seeds are available under different budgets/contracts;
- held-out seed2002 shows a severe reversal;
- safety is mixed;
- no fair external drop-in comparator is available under the frozen contract;
- the scope remains a 3-UAV simulation;
- common-hardware wall-clock and peak-memory comparisons are unavailable.

These are manuscript limitations, not permissions to start new experiments.
