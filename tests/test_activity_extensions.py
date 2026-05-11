"""Tests for the activity-level curves and search tools added to tools/activities.py."""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    get_activities_around,
    get_activities_by_ids,
    get_activity_best_efforts,
    get_activity_hr_curve,
    get_activity_interval_stats,
    get_activity_pace_curve,
    get_activity_power_curve,
    get_activity_power_vs_hr,
    get_activity_weather_summary,
    interval_search_activities,
    search_activities,
    search_activities_full,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    run_tool,
)


POWER_CURVE = {"label": "this", "secs": [1, 60, 300, 1200, 3600], "values": [1000, 400, 320, 280, 240]}
HR_CURVE = {"label": "this", "secs": [5, 60, 1200, 3600], "values": [185, 175, 165, 155]}
PACE_CURVE = {"label": "this", "secs": [60, 300, 1200, 3600], "values": [5.0, 4.5, 4.2, 3.8]}
ACTIVITY = {"id": "a1", "name": "Easy Spin", "type": "Ride", "start_date_local": "2026-05-11"}


SUCCESS_CASES = [
    pytest.param(
        get_activity_best_efforts,
        {"activity_id": "a1"},
        {"efforts": [{"duration": 60, "average": 350}, {"duration": 300, "average": 290}]},
        ["Best efforts (2)", "1m: avg=350"],
        "/activity/a1/best-efforts",
        id="best_efforts",
    ),
    pytest.param(
        get_activity_power_curve,
        {"activity_id": "a1"},
        POWER_CURVE,
        ["[this]", "20m: 280W"],
        "/activity/a1/power-curve.json",
        id="power_curve",
    ),
    pytest.param(
        get_activity_hr_curve,
        {"activity_id": "a1"},
        HR_CURVE,
        ["[this]", "175 bpm"],
        "/activity/a1/hr-curve.json",
        id="hr_curve",
    ),
    pytest.param(
        get_activity_pace_curve,
        {"activity_id": "a1"},
        PACE_CURVE,
        ["/km"],
        "/activity/a1/pace-curve.json",
        id="pace_curve",
    ),
    pytest.param(
        get_activity_power_vs_hr,
        {"activity_id": "a1"},
        {"decoupling": 3.2, "hr_values": [120, 140, 160], "power_values": [180, 220, 260]},
        ["Aerobic decoupling: 3.2", "bpm"],
        "/activity/a1/power-vs-hr.json",
        id="power_vs_hr",
    ),
    pytest.param(
        get_activity_interval_stats,
        {"activity_id": "a1", "start_secs": 60, "end_secs": 360},
        {"id": "1", "elapsed_time": 300, "moving_time": 298, "average_watts": 280},
        ["Interval stats", "280 W"],
        "/activity/a1/interval-stats",
        id="interval_stats",
    ),
    pytest.param(
        get_activity_weather_summary,
        {"activity_id": "a1"},
        {"average_temp": 16, "min_temp": 12, "max_temp": 20, "average_humidity": 55},
        ["Avg temp: 16°", "Humidity: 55%"],
        "/activity/a1/weather-summary",
        id="weather_summary",
    ),
    pytest.param(
        get_activities_by_ids,
        {"ids": "a1,a2", "athlete_id": "1"},
        [ACTIVITY, ACTIVITY],
        ["Activities:", "Easy Spin"],
        "/athlete/1/activities/a1,a2",
        id="activities_by_ids",
    ),
    pytest.param(
        search_activities,
        {"query": "vo2", "athlete_id": "1", "limit": 10},
        [ACTIVITY],
        ["Activity search results", "Easy Spin"],
        "/athlete/1/activities/search",
        id="search_activities",
    ),
    pytest.param(
        search_activities_full,
        {"query": "#race", "athlete_id": "1"},
        [ACTIVITY],
        ["Activity search results", "Easy Spin"],
        "/athlete/1/activities/search-full",
        id="search_activities_full",
    ),
    pytest.param(
        interval_search_activities,
        {
            "min_secs": 60,
            "max_secs": 600,
            "min_intensity": 95,
            "max_intensity": 120,
            "athlete_id": "1",
        },
        [{"activity_id": "a1", "interval_index": 0, "duration": 300, "average_watts": 320}],
        ["Matching intervals (1)", "320W"],
        "/athlete/1/activities/interval-search",
        id="interval_search",
    ),
    pytest.param(
        get_activities_around,
        {"activity_id": "a1", "athlete_id": "1"},
        [ACTIVITY],
        ["Activities:", "Easy Spin"],
        "/athlete/1/activities-around",
        id="activities_around",
    ),
]


@pytest.mark.parametrize("tool, kwargs, fake_resp, expected, exp_url", SUCCESS_CASES)
def test_tool_success(monkeypatch, tool, kwargs, fake_resp, expected, exp_url):
    captured: dict = {}
    result = run_tool(monkeypatch, tool, "activities", kwargs, fake_resp, captured)
    for piece in expected:
        assert piece in result, f"missing {piece!r} in:\n{result}"
    assert captured["last"]["url"] == exp_url


def test_search_activities_passes_query_and_limit(monkeypatch):
    captured: dict = {}
    run_tool(
        monkeypatch,
        search_activities,
        "activities",
        kwargs={"query": "tempo", "athlete_id": "1", "limit": 5},
        fake_response=[],
        capture=captured,
    )
    assert captured["last"]["params"] == {"q": "tempo", "limit": 5}


def test_interval_search_required_params(monkeypatch):
    captured: dict = {}
    run_tool(
        monkeypatch,
        interval_search_activities,
        "activities",
        kwargs={
            "min_secs": 60,
            "max_secs": 600,
            "min_intensity": 95,
            "max_intensity": 120,
            "athlete_id": "1",
            "sport_type": "Ride",
        },
        fake_response=[],
        capture=captured,
    )
    params = captured["last"]["params"]
    assert params["minSecs"] == 60
    assert params["maxSecs"] == 600
    assert params["minIntensity"] == 95
    assert params["maxIntensity"] == 120
    assert params["type"] == "Ride"


ERROR_CASES = [
    pytest.param(get_activity_best_efforts, {"activity_id": "a1"}, "Error fetching best efforts", id="best_efforts"),
    pytest.param(get_activity_power_curve, {"activity_id": "a1"}, "Error fetching power curve", id="power_curve"),
    pytest.param(get_activity_hr_curve, {"activity_id": "a1"}, "Error fetching hr curve", id="hr_curve"),
    pytest.param(get_activity_pace_curve, {"activity_id": "a1"}, "Error fetching pace curve", id="pace_curve"),
    pytest.param(get_activity_power_vs_hr, {"activity_id": "a1"}, "Error fetching power vs hr", id="power_vs_hr"),
    pytest.param(
        get_activity_interval_stats, {"activity_id": "a1"}, "Error fetching interval stats",
        id="interval_stats",
    ),
    pytest.param(
        get_activity_weather_summary, {"activity_id": "a1"}, "Error fetching weather summary",
        id="weather_summary",
    ),
    pytest.param(
        get_activities_by_ids, {"ids": "a1", "athlete_id": "1"}, "Error fetching activities",
        id="activities_by_ids",
    ),
    pytest.param(
        search_activities, {"query": "vo2", "athlete_id": "1"}, "Error searching activities",
        id="search_activities",
    ),
    pytest.param(
        search_activities_full, {"query": "vo2", "athlete_id": "1"}, "Error searching activities",
        id="search_activities_full",
    ),
    pytest.param(
        interval_search_activities,
        {"min_secs": 60, "max_secs": 600, "min_intensity": 95, "max_intensity": 120, "athlete_id": "1"},
        "Error searching intervals",
        id="interval_search",
    ),
    pytest.param(
        get_activities_around, {"activity_id": "a1", "athlete_id": "1"},
        "Error fetching activities around",
        id="activities_around",
    ),
]


@pytest.mark.parametrize("tool, kwargs, err", ERROR_CASES)
def test_tool_error(monkeypatch, tool, kwargs, err):
    result = run_tool(
        monkeypatch, tool, "activities", kwargs, fake_response={"error": True, "message": "boom"}
    )
    assert err in result
    assert "boom" in result
