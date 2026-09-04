from scripts.audit_tatg_mappo_p0 import all_present, result_from_checks


def test_all_present_requires_each_token() -> None:
    assert all_present("abc", ["a", "b"])
    assert not all_present("abc", ["a", "missing"])


def test_failed_static_check_closes_p0() -> None:
    result = result_from_checks({"actor": True, "legality": False})
    assert result["verdict"] == "TATG_P0_NO_GO"
    assert result["training_started"] is False


def test_pass_has_no_automatic_continuation() -> None:
    result = result_from_checks({"actor": True})
    assert result["verdict"] == "TATG_P0_FEASIBLE_FOR_P1_INFORMATION_GAP_PROBE"
    assert result["automatic_continuation"] is False
