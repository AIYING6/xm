from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

import numpy as np

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS, NOMINAL_GROUP
from algorithms.ri_gmappo.plr_topology_sampler import PLRTopologySampler
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo
from algorithms.redundant_topology_drtp_sampler import SixUAVDRTPTopologySampler


class PLRTopologySamplerTest(unittest.TestCase):
    def test_group_support_nominal_mass_and_runtime_restore(self) -> None:
        sampler = PLRTopologySampler(seed=79011, total_updates=39063)
        selections = [sampler.select(0, index % 4, index) for index in range(24)]
        self.assertTrue(all(selection.group == NOMINAL_GROUP or selection.group in FAILURE_GROUPS for selection in selections))
        self.assertTrue(all(sampler.seen.values()))
        row = sampler.record_rollout_scores(
            np.ones((4, 4, 5), dtype=np.float32),
            np.asarray([["F0", "TE", "TL", "DS"]] * 4),
        )
        self.assertEqual(row["record_type"], "rollout_score_update")
        self.assertAlmostEqual(sum(sampler.q.values()), 1.0)
        restored = PLRTopologySampler(seed=79011, total_updates=39063)
        restored.load_state_dict(sampler.state_dict())
        self.assertEqual(restored.state_dict(), sampler.state_dict())

    def test_score_input_shape_is_enforced(self) -> None:
        sampler = PLRTopologySampler(seed=79011, total_updates=39063)
        with self.assertRaises(ValueError):
            sampler.record_rollout_scores(np.ones((4, 4), dtype=np.float32), np.asarray([["F0"]]))

    def test_one_update_plr_path_writes_isolated_sampler_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "plr"
            config = RIGMAPPOConfig(
                env_name="3d_intercept", seed=79011, num_envs=4, rollout_steps=2,
                updates=1, ppo_epochs=1, minibatch_graphs=8, evaluation_enabled=False,
                save_interval=1, out_dir=str(output), device="cpu", drtp_sampler_mode="plr",
                drtp_sampler_seed=79011, drtp_sampler_logging=True,
            )
            train_ri_gmappo(config)
            self.assertTrue((output / "plr_topology_sampler_manifest.json").is_file())
            self.assertTrue((output / "plr_topology_sampler_log.csv").is_file())
            self.assertFalse((output / "drtp_topology_sampler_manifest.json").exists())

    def test_six_uav_original_drtp_state_restores(self) -> None:
        sampler = SixUAVDRTPTopologySampler("drtp", seed=69011, total_updates=39063)
        selections = [sampler.select(0, index % 4, index) for index in range(24)]
        for selection in selections:
            sampler.record_completed_return(selection, 1.0)
        sampler.maybe_update(32)
        restored = SixUAVDRTPTopologySampler("drtp", seed=69011, total_updates=39063)
        restored.load_state_dict(sampler.state_dict())
        self.assertEqual(restored.state_dict(), sampler.state_dict())


if __name__ == "__main__":
    unittest.main()
