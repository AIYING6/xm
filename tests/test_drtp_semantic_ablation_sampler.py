from __future__ import annotations

import unittest

from algorithms.ri_gmappo.drtp_semantic_ablation_sampler import SemanticAblationTopologySampler
from algorithms.ri_gmappo.drtp_topology_sampler import ALL_GROUPS, FAILURE_GROUPS


def seed_ready_ema(sampler: SemanticAblationTopologySampler) -> None:
    sampler.ema = {group: 100.0 for group in ALL_GROUPS}
    sampler.ema.update({"F0": 96.0, "TE": 90.0, "TL": 84.0, "DS": 80.0, "DL": 75.0, "CP": 70.0})


class SemanticAblationSamplerTest(unittest.TestCase):
    def test_random_mode_is_seed_bound_permutation_and_keeps_feasible_q(self) -> None:
        sampler = SemanticAblationTopologySampler("random_drtp", seed=80011, total_updates=39063)
        seed_ready_ema(sampler)
        row = sampler.maybe_update(160)
        self.assertTrue(row["adapted"])
        self.assertEqual(row["reason"], "randomized_semantic_mapping_update")
        self.assertNotEqual(sampler.semantic_permutation, {group: group for group in FAILURE_GROUPS})
        self.assertAlmostEqual(sum(sampler.q.values()), 1.0)
        self.assertTrue(all(0.05 <= value <= 0.35 for value in sampler.q.values()))
        self.assertEqual(sampler.last_difficulty["CP"], sampler.last_observed_difficulty[sampler.semantic_permutation["CP"]])

    def test_fixed_mode_updates_once_then_preserves_q(self) -> None:
        sampler = SemanticAblationTopologySampler("fixed_drtp", seed=80011, total_updates=39063)
        seed_ready_ema(sampler)
        first = sampler.maybe_update(160)
        q_after_first = dict(sampler.q)
        seed_ready_ema(sampler)
        second = sampler.maybe_update(192)
        self.assertTrue(first["adapted"])
        self.assertFalse(second["adapted"])
        self.assertEqual(second["reason"], "fixed_q_after_first_eligible_semantic_update")
        self.assertEqual(sampler.q, q_after_first)


if __name__ == "__main__":
    unittest.main()
