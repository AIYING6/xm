from __future__ import annotations

import json
import unittest

from scripts.verify_drtp_final_evidence_p0_preflight import check_environment, load_freeze


class FinalEvidenceP0Tests(unittest.TestCase):
    def test_frozen_ood_registry_and_environment_interface(self) -> None:
        spec = load_freeze()
        self.assertEqual(spec["checkpoint_contract"]["arms"], ["utr_sg", "drtp_sg"])
        self.assertEqual(spec["fresh_heldout_ood_tape"]["episode_ids"], [782000, 782099])
        report = check_environment(spec)
        self.assertEqual(report["pruned_directed_links_at_reset"]["structural_symmetric_longest_edge"], 2)
        self.assertEqual(report["pruned_directed_links_at_reset"]["structural_directed_longest_edge"], 1)
        self.assertFalse(report["condition_descriptor_direct_actor_input"])

    def test_archive_hashes_are_frozen(self) -> None:
        spec = load_freeze()
        self.assertEqual(
            spec["source_archives"]["A"]["sha256"],
            "429f13444c4ed10327abd62a13a0d9bf8ee737cedb6b6448353fd9087bcb275f",
        )
        self.assertEqual(
            spec["source_archives"]["B"]["sha256"],
            "d5c4adbe4f0004f0f415ba38e2b03232c55cb46c7d5dc7c7b1031eef7c1eef73",
        )
        self.assertTrue(json.dumps(spec))


if __name__ == "__main__":
    unittest.main()
