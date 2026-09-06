from __future__ import annotations

import unittest

from scripts.prepare_drtp_final_evidence_zero_training import (
    external_comparator_contract,
    fairness_audit,
    six_uav_preflight,
)


class FinalEvidencePreparationTests(unittest.TestCase):
    def test_cross_scale_preflight_is_nonlearning_and_complete(self) -> None:
        report = six_uav_preflight()
        self.assertEqual(report["verdict"], "DRTP_FINAL_6UAV_PREFLIGHT_PASS")
        self.assertFalse(report["training_started"])
        self.assertFalse(report["evaluation_started"])
        self.assertEqual(len(report["legal_paths"]), 8)

    def test_final_utr_drtp_contract_has_only_sampler_difference(self) -> None:
        audit = fairness_audit()
        self.assertEqual(audit["verdict"], "DRTP_UTR_FINAL_FAIRNESS_PASS")
        self.assertEqual(audit["allowed_difference"], "drtp_sampler_mode only")

    def test_plr_mapping_forbids_evaluation_access(self) -> None:
        contract = external_comparator_contract()
        self.assertEqual(contract["mapping"]["evaluation_access"], "forbidden")
        self.assertFalse(contract["training_started"])


if __name__ == "__main__":
    unittest.main()
