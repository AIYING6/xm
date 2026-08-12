# Phase 2IA5 E0 launch record

**Status:** prepared before E0 results; authorizes checkpoint-only E0 execution.  
**Protocol:** `PHASE2IA5-ETF-V1`  
**Executor commit:** `bbce7ade6a783cb0b64e6df795050042e3559754`

## Preconditions

1. `PHASE2IA5_ELIGIBILITY_TRIGGERED_FAILURE_PROTOCOL.md` is frozen and
   committed independently.
2. Unit test and static executor audit pass.
3. The smoke run confirms that an existing final checkpoint can be loaded and
   that the raw schema/trace writer complete without overwriting prior output.
4. The six fixed Phase 2IA4 final checkpoints are available under the archival
   training root and have the hashes recorded in the Phase 2IA4 completion
   audit.

## Frozen E0 invocation

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/run_phase2ia5_e0_eligibility_validation.py `
  --execute `
  --training-root archival/results/development/role_gate_phase2ia4/runs `
  --out-dir results/development/role_gate_phase2ia5_e0 `
  --episodes 100 `
  --device cuda
```

This produces exactly 600 DEVELOPMENT_ONLY_E0 episodes: 2 arms × 3 seeds ×
100 paired deterministic episodes. The executor rejects pre-existing E0 raw
and trace paths, so it cannot silently overwrite an attempt.

## Prohibited actions

- no new training;
- no canonical seed/test/result;
- no change to arm, seed, strict endpoint, four-step eligibility hold, step-220
  eligibility cap, relay identity, failure duration, or fixed-final checkpoint;
- no checkpoint selection, resume, early stopping, or seed exclusion;
- no Role-Gate KEEP/REMOVE conclusion before the independent E0 adequacy audit.

## Post-execution action

Run the independently implemented E0 trace/reconstruction audit. It may only
declare E0 PASS/FAIL. A fail leaves Role-Gate `UNRESOLVED` and Phase 3A
`NO-GO`; a pass merely permits a separately frozen V1 development protocol.

## Smoke closure

- `full_gate`, seed 101, one episode: checkpoint reload and raw schema/trace
  emission passed; the episode was not eligible and therefore no fault was
  injected, as required.
- `no_role_gate`, seed 101, ten episodes: raw schema/trace emission passed;
  all ten were correctly retained as not eligible rather than receiving a
  fixed-time fallback fault.
- The environment-level integration test independently verified that once an
  E0 trigger sets start step `s`, relay 1 is inactive before `s`, active for
  `s` through `s+79`, and inactive at `s+80`.

These smoke checks establish mechanics only and are not used as efficacy or
adequacy evidence. The full E0 suite remains the only result-producing run.
