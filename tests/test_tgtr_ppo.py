import torch

from algorithms.ri_gmappo.tgtr_ppo import clip_derived_kl_cap, project_halfspaces
from algorithms.ri_gmappo.tgtr_topology_sampler import SynchronizedTopologyGroupSampler


def test_sampler_has_exact_group_and_split_assignment():
    sampler = SynchronizedTopologyGroupSampler(17, 24)
    assignments = [(sampler.group_for_env(i), sampler.split_for_env(i)) for i in range(24)]
    assert sum(group == "N" for group, _ in assignments) == 12
    assert sum(group == "N" and split == "design" for group, split in assignments) == 6
    for group in ("F0", "TE", "TL", "DS", "DL", "CP"):
        assert assignments.count((group, "design")) == 1
        assert assignments.count((group, "certificate")) == 1


def test_halfspace_projection_is_feasible_and_minimal_in_simple_case():
    displacement = torch.tensor([-2.0, -1.0], dtype=torch.float64)
    normals = [torch.tensor([1.0, 0.0], dtype=torch.float64), torch.tensor([0.0, 1.0], dtype=torch.float64)]
    projected, info = project_halfspaces(displacement, normals)
    assert torch.allclose(projected, torch.zeros_like(projected), atol=1e-9)
    assert info["max_violation"] <= 1e-9


def test_clip_derived_kl_cap_matches_frozen_value():
    assert abs(clip_derived_kl_cap(0.2) - 0.02314355131420976) < 1e-14
