import time
from unittest.mock import MagicMock

from core.window import WindowManager


def test_show_hide_mock():
    wm = WindowManager(waiting_timeout=0.1)
    wm.start()
    wm.show()
    wm.hide()


def test_waiting_timer_fires():
    fired = []
    wm = WindowManager(waiting_timeout=0.1)
    wm.start()
    wm.set_timeout_callback(lambda: fired.append(True))
    wm.show()
    wm.start_waiting_timer()
    time.sleep(0.3)
    assert fired, "타임아웃 콜백이 호출되어야 한다"


def test_show_cancels_waiting_timer():
    fired = []
    wm = WindowManager(waiting_timeout=0.2)
    wm.start()
    wm.set_timeout_callback(lambda: fired.append(True))
    wm.start_waiting_timer()
    wm.show()  # 타이머 취소
    time.sleep(0.4)
    assert not fired, "show() 호출 시 타이머가 취소되어야 한다"
