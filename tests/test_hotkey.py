from core.hotkey import HotkeyListener


def test_trigger_calls_callback():
    called = []
    hl = HotkeyListener("<ctrl>+<space>", on_press=lambda: called.append(True))
    hl.start()
    hl.trigger()
    assert called, "trigger() 시 콜백이 호출되어야 한다"


def test_multiple_triggers():
    count = []
    hl = HotkeyListener("<ctrl>+<space>", on_press=lambda: count.append(1))
    hl.start()
    hl.trigger()
    hl.trigger()
    assert len(count) == 2
