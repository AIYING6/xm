"""State-owning actor adapter for the frozen TATG chronological PPO path.

The legacy snapshot runner remains untouched.  This adapter is the narrow
integration boundary a future TATG-only outer loop must use: it owns legal
per-environment CETM state while acting, records the sampled action only after
its log-probability has been computed, resets completed slots from the new
reset graph, and replays a stored rollout chronologically for PPO's actor
term.  It deliberately owns neither an environment nor a critic.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.distributions import Categorical

from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor, TATGRuntimeStateBank
from algorithms.ri_gmappo.tatg_sequence_ppo import TATGSequenceReplay, replay_tatg_actor_sequence


@dataclass(frozen=True)
class TATGActorStep:
    """Actor-only values emitted for one vectorized environment transition."""

    actions: torch.Tensor
    log_prob: torch.Tensor
    entropy: torch.Tensor
    logits: torch.Tensor


class TATGSequenceActorRunner:
    """Own CETM rollout state and chronological actor replay for one rollout.

    This class is intentionally actor-only.  The existing centralized critic,
    reward, environment, sampler and GAE code remain outside this boundary and
    retain their ordinary snapshot-PPO implementation.
    """

    def __init__(self, actor: TATGMemoryActor, relation_adj: torch.Tensor, edge_feat: torch.Tensor):
        self.actor = actor
        self.state_bank = TATGRuntimeStateBank(actor, relation_adj, edge_feat)

    def rollout_start_state_dict(self) -> dict[str, dict[str, torch.Tensor]]:
        """Clone the exact legal memory state before the first rollout action."""

        return self.state_bank.runtime_state_dict()

    def load_rollout_start_state_dict(self, payload: dict[str, dict[str, torch.Tensor]]) -> None:
        """Restore a saved rollout-start state without consulting any outcome."""

        self.state_bank.load_runtime_state_dict(payload)

    def act(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor,
        role: torch.Tensor,
        adj: torch.Tensor,
        relation_adj: torch.Tensor,
        *,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
        action_generator: torch.Generator | None = None,
    ) -> TATGActorStep:
        """Sample/evaluate an action and then advance only the stored action.

        Stored rollout actions are supplied during audit/replay checks.  During
        collection the optional torch generator gives the outer loop the same
        explicit action-RNG ownership as the snapshot runner.
        """

        logits, _, _, next_state = self.actor.forward_with_memory(
            obs, node_feat, edge_feat, role, adj, self.actor.topology_memory.num_blue, relation_adj, self.state_bank.state
        )
        distribution = Categorical(logits=logits)
        if action is None:
            if deterministic:
                action = logits.argmax(dim=-1)
            elif action_generator is None:
                action = distribution.sample()
            else:
                probabilities = distribution.probs.reshape(-1, distribution.probs.shape[-1])
                action = torch.multinomial(probabilities, num_samples=1, generator=action_generator).reshape(logits.shape[:-1])
        action = action.long()
        if tuple(action.shape) != tuple(logits.shape[:-1]):
            raise ValueError("action must have shape [environment, agent]")
        self.state_bank.replace_state(self.actor.record_actions(next_state, action))
        return TATGActorStep(
            actions=action,
            log_prob=distribution.log_prob(action),
            entropy=distribution.entropy(),
            logits=logits,
        )

    def reset_completed(
        self, completed: torch.Tensor, relation_adj: torch.Tensor, edge_feat: torch.Tensor
    ) -> None:
        """Apply the completed-slot reset before the next actor graph row."""

        self.state_bank.reset_completed(completed, relation_adj, edge_feat)

    def replay_rollout(
        self,
        *,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor,
        role: torch.Tensor,
        adj: torch.Tensor,
        relation_adj: torch.Tensor,
        actions: torch.Tensor,
        dones: torch.Tensor,
        state_before_rollout: dict[str, dict[str, torch.Tensor]],
    ) -> TATGSequenceReplay:
        """Recompute actor outputs in the frozen full chronological order."""

        replay_bank = TATGRuntimeStateBank(self.actor, relation_adj[0], edge_feat[0])
        replay_bank.load_runtime_state_dict(state_before_rollout)
        return replay_tatg_actor_sequence(
            self.actor,
            obs=obs,
            node_feat=node_feat,
            edge_feat=edge_feat,
            role=role,
            adj=adj,
            relation_adj=relation_adj,
            actions=actions,
            dones=dones,
            state_before_rollout=replay_bank.state,
        )
