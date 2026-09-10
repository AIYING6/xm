import torch

from algorithms.acfid_clipped_ppo import InvariantRecoveryCritic, PPOBatch, ppo_loss
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy


def test_clipped_ppo_is_finite_and_updates_actor():
    torch.manual_seed(4); batch_size = 12
    policy = ACFIDRecoveryPolicy(7, 5, 3); critic = InvariantRecoveryCritic(7, 5)
    context = torch.randn(batch_size, 7); faults = torch.randn(batch_size, 6, 5)
    active = torch.randint(0, 2, (batch_size, 6)).float(); relations = torch.randn(batch_size, 6, 6, 3)
    with torch.no_grad():
        logits = policy(context, faults, active, relations); actions = logits.argmax(-1)
        old = torch.distributions.Categorical(logits=logits).log_prob(actions)
        returns = torch.randn(batch_size); advantages = returns - critic(context, faults, active)
    batch = PPOBatch(context, faults, active, relations, actions, old, returns, advantages)
    before = torch.cat([p.detach().flatten() for p in policy.parameters()]); loss, metrics = ppo_loss(policy, critic, batch)
    optimizer = torch.optim.Adam([*policy.parameters(), *critic.parameters()], 3e-4); optimizer.zero_grad(); loss.backward(); optimizer.step()
    after = torch.cat([p.detach().flatten() for p in policy.parameters()])
    assert torch.isfinite(loss) and torch.linalg.vector_norm(after - before) > 0
    assert set(metrics) == {"policy_loss", "value_loss", "entropy", "ratio_mean"}


def test_critic_is_permutation_invariant_over_fault_registry():
    critic = InvariantRecoveryCritic(7, 5); context = torch.randn(3, 7); faults = torch.randn(3, 6, 5); active = torch.randint(0, 2, (3, 6)).float()
    permutation = torch.tensor([4, 0, 5, 2, 1, 3])
    assert torch.allclose(critic(context, faults, active), critic(context, faults[:, permutation], active[:, permutation]))
