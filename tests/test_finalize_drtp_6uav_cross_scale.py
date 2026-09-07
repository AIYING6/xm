"""Integrity test for the read-only 6-UAV submission finalizer."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import finalize_drtp_6uav_cross_scale as finalizer


class FinalizeDrtp6UavTest(unittest.TestCase):
    def build_fixture(self, root: Path) -> None:
        root.mkdir(parents=True)
        (root / "DRTP_6UAV_CROSS_SCALE_COMPLETE.json").write_text(
            json.dumps({"status": "DRTP_6UAV_CROSS_SCALE_COMPLETE", "endpoint_evaluation_completed": True}),
            encoding="utf-8",
        )
        for arm_index, arm in enumerate(finalizer.ARMS):
            for seed_index, seed in enumerate(finalizer.SEEDS):
                run = root / "runs" / arm / f"seed{seed}"
                evaluation = root / "evaluations" / arm
                run.mkdir(parents=True)
                evaluation.mkdir(parents=True, exist_ok=True)
                checkpoint = f"sha-{arm_index}-{seed}"
                (run / "run_manifest.json").write_text(
                    json.dumps({"status": "completed", "updates": 39063, "checkpoint_sha256": checkpoint}),
                    encoding="utf-8",
                )
                rows = []
                for group_index, group in enumerate(finalizer.ALL_GROUPS):
                    for episode in range(finalizer.EPISODES_PER_GROUP):
                        base = 100.0 + seed_index + group_index
                        score = base + (3.0 if arm == finalizer.ARMS[1] else 0.0)
                        rows.append({
                            "arm": arm,
                            "seed": seed,
                            "group": group,
                            "episode": episode,
                            "score": score,
                            "success": 0.7 + 0.01 * arm_index,
                            "timeout": 0.2 - 0.01 * arm_index,
                            "collision": 0.05,
                            "checkpoint_sha256": checkpoint,
                        })
                with (evaluation / f"seed{seed}_final_10m.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)

    def test_complete_frozen_endpoint_is_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "output"
            report = Path(temp) / "report"
            self.build_fixture(root)
            argv = [
                "finalize_drtp_6uav_cross_scale.py",
                "--output-root", str(root),
                "--report-dir", str(report),
                "--execute",
            ]
            with patch.object(sys, "argv", argv):
                finalizer.main()
            with (report / "DRTP_6UAV_COHORT_SUMMARY.csv").open(encoding="utf-8") as handle:
                summary = list(csv.DictReader(handle))
            with (report / "DRTP_6UAV_PAIRED_DELTAS.csv").open(encoding="utf-8") as handle:
                paired = list(csv.DictReader(handle))
            self.assertEqual([row["method"] for row in summary], ["UTR", "DRTP"])
            self.assertEqual(summary[0]["n_training_seeds"], "5")
            self.assertEqual(len(paired), 5)
            self.assertTrue(all(float(row["delta_J_perturbed"]) == 3.0 for row in paired))
            self.assertTrue((report / "Fig6_6UAV_cross_scale_paired_endpoint.pdf").is_file())
            self.assertTrue((report / "DRTP_6UAV_FINALIZATION.json").is_file())


if __name__ == "__main__":
    unittest.main()
