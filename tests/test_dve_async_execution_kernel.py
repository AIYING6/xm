import numpy as np

from envs.dve_async_execution_kernel import (
    CompletionState,
    DVEAsyncExecutionKernel,
    SnapshotState,
)


SNAPSHOT = SnapshotState(own_x=0.0, own_v=1.0, target_x=1.0, corridor_open=True)


def make_kernel(target_x: float, reserved: bool = False):
    return DVEAsyncExecutionKernel(
        SNAPSHOT,
        CompletionState(elapsed_ms=80.0, own_x=1.0, target_x=target_x, corridor_reserved=reserved),
    )


def test_divergent_completion_states_have_identical_proposal_information():
    valid = make_kernel(target_x=2.0)
    obsolete = make_kernel(target_x=5.0)
    assert np.array_equal(valid.reset()[0], obsolete.reset()[0])
    valid.begin_inference(1)
    obsolete.begin_inference(1)
    assert not np.array_equal(valid.admission_observation(), obsolete.admission_observation())


def test_proposal_must_be_frozen_before_completion_observation():
    kernel = make_kernel(target_x=2.0)
    kernel.reset()
    try:
        kernel.admission_observation()
    except RuntimeError:
        pass
    else:
        raise AssertionError("completion state leaked before proposal freeze")


def test_same_proposal_has_different_correct_admission_decisions():
    valid = make_kernel(target_x=2.0)
    obsolete = make_kernel(target_x=5.0)
    for kernel in (valid, obsolete):
        kernel.reset()
        kernel.begin_inference(1)
    valid_result = valid.step(1)
    obsolete_result = obsolete.step(0)
    assert valid_result[3].tolist() == [8.0]
    assert obsolete_result[3].tolist() == [3.0]
    assert not valid_result[5][0]["stale_accept"]
    assert not obsolete_result[5][0]["stale_accept"]

