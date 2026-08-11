# M2 pilot partial result: read-only diagnosis

**Status:** `M2_PARTIAL_DIAGNOSIS__MECHANISM_OPTIMIZATION_UNSTABLE`

This diagnosis replays only the four frozen M2 pilot checkpoints from archive
`M2_PILOT_8c2b597.tar.gz` on the same 32 frozen evaluation seeds.  It does not
train, update parameters, alter the environment, or introduce any episode seed.
The replay reproduced every archived endpoint summary exactly.

## Paired episode decomposition

| Training seed | Both neutralized | Full only | B1 only | Both failed |
| --- | ---: | ---: | ---: | ---: |
| 9201 | 8 | 0 | 9 | 15 |
| 9202 | 7 | 1 | 0 | 24 |

For attack-range acquisition, seed 9201 has 7 `B1-only` acquisitions and no
`Full-only` acquisition; seed 9202 has 4 `Full-only` acquisitions and no
`B1-only` acquisition.  This is the frozen pilot's instability, not a
confirmatory performance comparison.

## Control and modulation observations

Full's four checkpoint artifacts and training logs have distinct SHA256 values,
so identical endpoint counts for its two seeds are not an output-overwrite
artifact.  However, the evaluated Full policies exhibit a collapsed control
regime:

- Full seed 9201: attacker commit is 1.0 on every evidence-present step; turn
  and climb commands have very small standard deviations (0.036 and 0.026).
- Full seed 9202: attacker commit is 0.0 on every evidence-present step; turn
  and climb standard deviations are 0.040 and 0.047.
- The Full progress modulation mean is nearly time-invariant within each seed:
  `0.5020 ± 0.0003` (9201) and `0.4924 ± 0.0002` (9202).
- By contrast, B1 seed 9201 has materially varying pursuit commands and is
  substantially better on acquisition and neutralization; B1 seed 9202 is
  weak, which explains the reversed direction in that pair.

The available evidence supports a failure of robust optimization for the
current progress-conditioned modulation, rather than an actor-contract,
collector-expiry, archive-integrity, or concurrent-launch defect.

## Frozen decision

The pilot remains development-only and is **not** authorized to receive extra
seeds, more updates, reward changes, or a modified module.  It cannot enter a
formal multi-seed protocol.  The only defensible next decision is whether to
close this current mechanism or to separately authorize a redesigned method
hypothesis; this result cannot be rescued by tuning.
