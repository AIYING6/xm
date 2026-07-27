import torch

from scripts.train_happo_baseline import happo_policy_loss


def test_happo_policy_loss_applies_prefix_joint_ratio() -> None:
    ratio = torch.tensor([1.10, 0.90])
    prefix_ratio = torch.tensor([2.0, 0.5])
    advantage = torch.tensor([1.0, -1.0])

    loss = happo_policy_loss(
        ratio=ratio,
        prefix_ratio=prefix_ratio,
        advantage=advantage,
        clip_coef=0.2,
    )

    unclipped = prefix_ratio * ratio * advantage
    clipped = prefix_ratio * torch.clamp(ratio, 0.8, 1.2) * advantage
    expected = -torch.min(unclipped, clipped).mean()
    assert torch.allclose(loss, expected)


def test_happo_policy_loss_clips_only_current_agent_ratio() -> None:
    ratio = torch.tensor([1.50])
    prefix_ratio = torch.tensor([3.0])
    advantage = torch.tensor([1.0])

    loss = happo_policy_loss(
        ratio=ratio,
        prefix_ratio=prefix_ratio,
        advantage=advantage,
        clip_coef=0.2,
    )

    assert torch.allclose(loss, torch.tensor(-3.0 * 1.2))
