import pytest
from core.state import AppState, StateController


def test_initial_state():
    ctrl = StateController()
    assert ctrl.current == AppState.IDLE


def test_valid_transitions():
    ctrl = StateController()
    assert ctrl.transition(AppState.LISTENING) is True
    assert ctrl.current == AppState.LISTENING

    assert ctrl.transition(AppState.PROCESSING) is True
    assert ctrl.current == AppState.PROCESSING

    assert ctrl.transition(AppState.SPEAKING) is True
    assert ctrl.current == AppState.SPEAKING

    assert ctrl.transition(AppState.WAITING) is True
    assert ctrl.current == AppState.WAITING

    assert ctrl.transition(AppState.IDLE) is True
    assert ctrl.current == AppState.IDLE


def test_invalid_transition_returns_false():
    ctrl = StateController()
    # IDLE → PROCESSING 은 유효하지 않음
    assert ctrl.transition(AppState.PROCESSING) is False
    assert ctrl.current == AppState.IDLE


def test_force_override():
    ctrl = StateController()
    ctrl.force(AppState.SPEAKING)
    assert ctrl.current == AppState.SPEAKING


def test_cancel_flow():
    ctrl = StateController()
    ctrl.transition(AppState.LISTENING)
    ctrl.transition(AppState.PROCESSING)
    ctrl.force(AppState.IDLE)
    assert ctrl.current == AppState.IDLE


def test_waiting_to_listening():
    ctrl = StateController()
    ctrl.transition(AppState.LISTENING)
    ctrl.transition(AppState.PROCESSING)
    ctrl.transition(AppState.SPEAKING)
    ctrl.transition(AppState.WAITING)
    assert ctrl.transition(AppState.LISTENING) is True
