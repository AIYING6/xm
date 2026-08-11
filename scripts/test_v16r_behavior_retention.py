"""Deterministic checks for evidence-masked behavior retention in PPO."""
from __future__ import annotations
import copy, numpy as np, torch
from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update

def main() -> int:
    torch.manual_seed(44); actor=ContinuousGuidanceActor(12,hidden_dim=16,role_specific=False); ref=copy.deepcopy(actor); critic=CentralizedValueCritic(10,hidden_dim=16)
    batch={"obs":np.random.randn(4,2,12).astype(np.float32),"share_obs":np.random.randn(4,2,10).astype(np.float32),"actions":np.zeros((4,2,2),np.float32),"logp":np.zeros((4,2),np.float32),"rewards":np.ones((4,2,1),np.float32),"dones":np.zeros((4,2),np.float32),"next_share_obs":np.random.randn(2,10).astype(np.float32),"evidence_mask":np.ones((4,2),np.float32)}
    m=ppo_update(actor,critic,batch,V16RPPOConfig(epochs=1),reference_actor=ref,retention_coef=1.0)
    assert np.isfinite(m["retention_loss"]) and m["retention_loss"] < 1e-7
    with torch.no_grad():
        for p in actor.parameters(): p.add_(0.1)
    m2=ppo_update(actor,critic,batch,V16RPPOConfig(epochs=1),reference_actor=ref,retention_coef=1.0)
    assert np.isfinite(m2["retention_loss"]) and m2["retention_loss"] > 0.0
    m3=ppo_update(actor,critic,batch,V16RPPOConfig(epochs=1),reference_actor=ref,retention_coef=1.0,adaptive_retention=True,retention_beta=1.0)
    assert np.isfinite(m3["retention_loss"])
    print("checks=3, failed=0"); return 0
if __name__=="__main__": raise SystemExit(main())
