import numpy as np

from scripts.audit_pscr_p8_search_prefix_q0 import FORECAST_POSITION, PRIMARY_POSITION, make_env


def test_p8_task_positions_are_absolute_and_inside_flight_envelope():
    env = make_env(98_000)
    assert np.array_equal(env.primary_position, PRIMARY_POSITION)
    assert np.array_equal(env._forecast_position, FORECAST_POSITION)
    assert env.base.config.min_altitude < PRIMARY_POSITION[2] < env.base.config.max_altitude
    assert env.base.config.min_altitude < FORECAST_POSITION[2] < env.base.config.max_altitude
