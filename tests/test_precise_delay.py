import threading

import hal as real_hal
import wpilib.simulation as sim

from robotpy_ext.misc import precise_delay


def test_synchronous_step_acknowledges_caller_work(wpitime):
    """A real HAL step stays pending until the caller's next wait."""
    assert real_hal.initialize()
    work_blocked = threading.Event()
    release_work = threading.Event()
    second_wait = threading.Event()
    worker_done = threading.Event()
    step_done = threading.Event()
    errors = []
    ready = threading.Event()

    def worker():
        delay = precise_delay.NotifierDelay(0.02)
        ready.set()
        try:
            delay.wait()
            work_blocked.set()
            assert release_work.wait(5), "caller work was not released"
            second_wait.set()
            delay.wait()
            worker_done.set()
        except BaseException as exc:
            errors.append(exc)
        finally:
            delay.free()

    def stepper():
        try:
            sim.step_timing(0.02)
            step_done.set()
        except BaseException as exc:
            errors.append(exc)

    worker_thread = threading.Thread(target=worker, daemon=True)
    step_thread = threading.Thread(target=stepper, daemon=True)
    try:
        worker_thread.start()
        assert ready.wait(2)
        step_thread.start()
        assert work_blocked.wait(2), "alarm did not wake caller"
        assert not step_done.wait(0.1), "step acknowledged before work finished"
        release_work.set()
        assert second_wait.wait(2)
        assert step_done.wait(2), "next wait did not acknowledge step"
        assert not worker_done.is_set(), "second alarm fired without another step"
    finally:
        release_work.set()
        assert ready.wait(2)
        sim.step_timing_async(1.0)
        worker_thread.join(2)
        if step_thread.ident is not None:
            step_thread.join(2)
    assert not worker_thread.is_alive()
    assert not step_thread.is_alive()
    assert not errors, errors


def test_rearm_after_work(monkeypatch):
    calls = []
    monkeypatch.setattr(precise_delay.hal, "create_notifier", lambda: (123, 0))
    monkeypatch.setattr(
        precise_delay.hal, "set_notifier_alarm", lambda *args: calls.append("arm")
    )
    monkeypatch.setattr(
        precise_delay.hal, "destroy_notifier", lambda handle: calls.append("free")
    )
    monkeypatch.setattr(
        precise_delay.sync, "wait_for_object", lambda handle: calls.append("wait")
    )
    with precise_delay.NotifierDelay(0.02) as delay:
        delay.wait()
        calls.append("work")
        assert calls == ["arm", "wait", "work"]
        delay.wait()
        assert calls == ["arm", "wait", "work", "arm", "wait"]
    assert calls[-1] == "free"
