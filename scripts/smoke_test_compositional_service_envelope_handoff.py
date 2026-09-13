"""Smoke-test the V5 public service-envelope handoff contract."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env


def main() -> None:
    profiles = ("current_compact", "current_delayed", "future_fresh", "future_durable")
    expected_future = (False, False, True, True)
    route_choices: list[bool] = []
    for index, (profile, future_required) in enumerate(zip(profiles, expected_future)):
        cfg = RIGMAPPOConfig(
            env_name="commitment_handoff_3d",
            seed=81_000 + index,
            target_init_range_scale=0.65,
            handoff_service_envelope_mode="compositional_v5",
            handoff_service_envelope_profile=profile,
        )
        env = make_env(cfg, cfg.seed, training=False)
        obs, share_obs, _ = env.reset()
        assert env._future_service_required() is future_required, profile
        # V5 supplies six envelope scalars in place of legacy three-way
        # context fields; no public profile/category one-hot is present.
        assert obs.shape[-1] == 54 and share_obs.shape[-1] == 53
        route_choices.append(env._future_service_required())
    assert route_choices == [False, False, True, True]
    print("PASS: V5 exposes public service envelopes and yields two legal current/future route requirements")


if __name__ == "__main__":
    main()
