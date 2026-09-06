"""Frozen contracts for the compute-efficient matched A/B PLR comparator."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FREEZE=ROOT/'configs/drtp_plr_external_matched_ab_freeze_20260906.json'
SEEDS={'A':(78011,78012,78013,78014,78015),'B':(78021,78022,78023,78024,78025)}
UPDATES,NUM_ENVS,ROLLOUT=39063,4,64
STEPS=UPDATES*NUM_ENVS*ROLLOUT
MILESTONES={3907:'1m',11719:'3m',39063:'10m'}
CONDITIONS=(('nominal',-1,0,0),('F0',1,44,80),('TE',1,28,80),('TL',1,52,80),('DS',1,44,40),('DL',1,44,100),('CP',1,28,120))
def freeze():
    x=json.loads(FREEZE.read_text(encoding='utf-8'))
    if tuple(x['cohorts'])!=('A','B') or any(tuple(x['cohorts'][c]['seeds'])!=SEEDS[c] for c in SEEDS): raise RuntimeError('matched A/B PLR freeze mismatch')
    return x
def tape(cohort):
    # This must be byte-for-byte the tape payload used for the already frozen
    # UTR/DRTP endpoint, not a merely equivalent new tape with a new hash.
    from scripts.create_drtp_stabilization_confirmatory_tape import payload as frozen_endpoint_tape
    value = frozen_endpoint_tape(cohort)
    ids = freeze()['cohorts'][cohort]['tape_seed_namespace']
    if value['episode_ids'] != list(range(ids[0], ids[1] + 1)):
        raise RuntimeError('matched PLR tape does not equal the frozen A/B endpoint tape')
    return value
