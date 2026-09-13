"""Capacity defense with explicit, time-stamped legal target-track messages."""
from __future__ import annotations

import numpy as np

from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv


class MultiThreatCommunicativeCapacityDefenseEnv(MultiThreatCapacityShapedDefenseEnv):
    """Sighting payloads traverse only the current transitive communication graph."""

    def reset(self):
        super().reset()
        self.track_pos=np.zeros((self.num_agents,2,3),dtype=np.float32)
        self.track_valid=np.zeros((self.num_agents,2),dtype=bool)
        self.track_age=np.full((self.num_agents,2),np.inf,dtype=np.float32)
        self._update_tracks()
        return self._obs(),self._share_obs(),self._graph()

    def _update_tracks(self):
        self.track_age += 1.0
        reach=self.base._transitive_comm()
        for recipient in range(self.num_agents):
            for threat in range(2):
                sources=[source for source in range(self.num_agents) if reach[recipient,source]>0.5 and self._visible(source,threat)]
                if sources:
                    source=sources[0]
                    self.track_pos[recipient,threat]=self.red_pos[threat]
                    self.track_valid[recipient,threat]=True
                    self.track_age[recipient,threat]=0.0

    def _obs(self):
        base=super()._obs()
        # Parent construction invokes reset dynamically before this subclass
        # has allocated its message buffers.
        if not hasattr(self, "track_valid"):
            return base
        payload=[]
        for agent in range(self.num_agents):
            values=[]
            for threat in range(2):
                valid=float(self.track_valid[agent,threat])
                rel=(self.track_pos[agent,threat]-self.base.blue_pos[agent])/self.base.config.world_radius if valid else np.zeros(3,dtype=np.float32)
                age=min(float(self.track_age[agent,threat]),self.config.horizon)/self.config.horizon if valid else 1.0
                values.extend((*rel.tolist(),valid,age))
            payload.append(values)
        return np.concatenate((base,np.asarray(payload,dtype=np.float32)),axis=-1)

    def step(self, actions):
        _,share,graph,rewards,dones,info=super().step(actions)
        self._update_tracks()
        info["track_messages_valid"]=float(self.track_valid.sum())
        return self._obs(),share,self._graph(),rewards,dones,info
