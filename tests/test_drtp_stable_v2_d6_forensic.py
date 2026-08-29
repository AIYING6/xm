from __future__ import annotations

from scripts.run_drtp_stable_v2_d6_forensic import first_q_divergence, q_uniform_l1


def sampler_row(update: int, count: int, value: float) -> dict[str, str]:
    return {
        "update": str(update), "adaptation_count": str(count), "adapted": "True",
        "q_F0": str(value), "q_TE": str(1.0 - value),
        "q_TL": "0.0", "q_DS": "0.0", "q_DL": "0.0", "q_CP": "0.0",
    }


def test_first_q_divergence_uses_adaptation_count_and_order():
    original = [sampler_row(160, 1, 0.5), sampler_row(320, 2, 0.5)]
    candidate = [sampler_row(160, 1, 0.5), sampler_row(320, 2, 0.6)]
    found = first_q_divergence(original, candidate)
    assert found is not None
    assert found["candidate_update"] == 320
    assert found["adaptation_count"] == 2


def test_uniform_distance_is_zero_for_exact_uniform_distribution():
    row = {key: str(1.0 / 6.0) for key in ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")}
    assert q_uniform_l1(row) == 0.0
