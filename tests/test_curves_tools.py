"""Tests for tools/curves.py — athlete-level power/HR/pace curves + MMP model."""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    get_athlete_hr_curves,
    get_athlete_pace_curves,
    get_athlete_power_curves,
    get_mmp_model,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    run_tool,
)


POWER_CURVE = {
    "label": "1y",
    "secs": [1, 5, 60, 1200, 3600],
    "values": [1100, 900, 420, 280, 240],
}

HR_CURVE = {
    "label": "1y",
    "secs": [5, 60, 1200, 3600],
    "values": [185, 175, 165, 155],
}

PACE_CURVE = {
    "label": "1y",
    "secs": [60, 1200, 3600],
    "values": [5.0, 4.2, 3.8],
}


def test_power_curves_summary(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        get_athlete_power_curves,
        "curves",
        kwargs={"athlete_id": "1", "sport_type": "Ride"},
        fake_response={"list": [POWER_CURVE]},
        capture=captured,
    )
    assert "Power curves (1)" in result
    # Coach-canonical bucket appears
    assert "20m: 280W" in result
    assert captured["last"]["url"] == "/athlete/1/power-curves.json"
    assert captured["last"]["params"]["type"] == "Ride"


def test_power_curves_full(monkeypatch):
    result = run_tool(
        monkeypatch,
        get_athlete_power_curves,
        "curves",
        kwargs={"athlete_id": "1", "summary_only": False},
        fake_response={"list": [POWER_CURVE]},
    )
    # Full mode emits every (secs,value) pair: 5 entries
    duration_lines = [line for line in result.splitlines() if line.strip().startswith(("1s:", "5s:", "1m:", "20m:", "1h:"))]
    assert len(duration_lines) >= 5


def test_hr_curves(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        get_athlete_hr_curves,
        "curves",
        kwargs={"athlete_id": "1"},
        fake_response={"list": [HR_CURVE]},
        capture=captured,
    )
    assert "HR curves (1)" in result or "Hr curves (1)" in result
    assert "175 bpm" in result
    assert captured["last"]["url"] == "/athlete/1/hr-curves.json"


def test_pace_curves(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        get_athlete_pace_curves,
        "curves",
        kwargs={"athlete_id": "1"},
        fake_response={"list": [PACE_CURVE]},
        capture=captured,
    )
    assert "Pace curves (1)" in result
    assert "/km" in result
    assert captured["last"]["url"] == "/athlete/1/pace-curves.json"


def test_curves_accept_raw_list_response(monkeypatch):
    """Endpoint may also respond with a bare list."""
    result = run_tool(
        monkeypatch,
        get_athlete_power_curves,
        "curves",
        kwargs={"athlete_id": "1"},
        fake_response=[POWER_CURVE, POWER_CURVE],
    )
    assert "Power curves (2)" in result


def test_curves_empty(monkeypatch):
    result = run_tool(
        monkeypatch,
        get_athlete_power_curves,
        "curves",
        kwargs={"athlete_id": "1"},
        fake_response={"list": []},
    )
    assert "No power curves" in result


def test_mmp_model(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        get_mmp_model,
        "curves",
        kwargs={"athlete_id": "1", "sport_type": "Ride", "date": "2026-05-11"},
        fake_response={"cp": 280, "w_prime": 19000, "p_max": 1100, "days": 90},
        capture=captured,
    )
    assert "CP: 280W" in result
    assert captured["last"]["url"] == "/athlete/1/mmp-model"
    assert captured["last"]["params"] == {"type": "Ride", "date": "2026-05-11"}


ERROR_CASES = [
    pytest.param(
        get_athlete_power_curves, {"athlete_id": "1"}, "Error fetching power curves",
        id="power",
    ),
    pytest.param(
        get_athlete_hr_curves, {"athlete_id": "1"}, "Error fetching hr curves", id="hr",
    ),
    pytest.param(
        get_athlete_pace_curves, {"athlete_id": "1"}, "Error fetching pace curves", id="pace",
    ),
    pytest.param(
        get_mmp_model, {"athlete_id": "1"}, "Error fetching MMP model", id="mmp",
    ),
]


@pytest.mark.parametrize("tool, kwargs, err", ERROR_CASES)
def test_tool_error(monkeypatch, tool, kwargs, err):
    result = run_tool(
        monkeypatch, tool, "curves", kwargs, fake_response={"error": True, "message": "boom"}
    )
    assert err in result
    assert "boom" in result
