# DRTP REL-A0-R Checkpoint Recovery Audit

- Protocol: `DRTP-REL-A0-R-ASSET-RECOVERY-V1`
- Training started: **NO**
- Complete paired seeds: **5/5** (1901, 1902, 2001, 2002, 2003)
- Minimum required to reopen REL-A0: **4**
- Recovery gate: **PASS**

## Interpretation

The provisional 2/5 block is superseded by the recovered archive evidence. The historical Phase-S1-A `F_TECHNICAL_INVALID` conclusion is not rewritten; this report only establishes asset availability for the separate REL-A0 audit.

## Recovered paired assets

| seed | UTR status | DRTP status | steps | parameters | UTR hash | DRTP hash |
|---:|---|---|---:|---:|---|---|
| 1901 | completed | completed | 10000128 | 116728 | `52719762aac0a0b954a52317ff4a77ac5d81973cfca74c48d5c28a379b82e2e8` | `38a6a8c8c324d9b151be0494df8b3287b08cd0e0f5ec351b42e2cf40047cadd8` |
| 1902 | completed | completed | 10000128 | 116728 | `b7276c6d0628038f000c3b1ea0e3f0b6277e24c8e317845b2756e2dfefaccf86` | `bfb172749b2393da7d704774ae9ac882ce8ece24dd79b66877b19dabd8b2095a` |
| 2001 | completed | completed | 10000128 | 116728 | `7169320e85fa91bc69089d4bb3b7178ee979a26f475171b5278630da9e85c74c` | `4a73e12d6fc0ef049021fd8df5a9cb3ea3b7b4874dec3fce21d9ccf48a5c47c3` |
| 2002 | completed | completed | 10000128 | 116728 | `547b2c0568e0f93ce420dc167d252a6711793763841dde239d4ba2acb2bc9252` | `32d06bd919152c7731513bc0b21e1fffe9c75b1ea5739eea8f5f6c0ed0fc6907` |
| 2003 | completed | completed | 10000128 | 116728 | `ecf345baaf4fc2f411a05b9a000a6e8cfb28f875978a3ae9b7d9e494bc6a97fe` | `fc7678c5ecac7f7c195957a0d668dae33981443db92bccd412fece65044223d8` |

## Required invariants

- All ten runs are completed 10,000,128-step trajectories.
- All checkpoints have 116,728 parameters and the expected UTR/DRTP config hash.
- Model and runtime-state SHA256 values match the archived manifests.
- No training, resume, checkpoint promotion, or seed substitution was performed.
