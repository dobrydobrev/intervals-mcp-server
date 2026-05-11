"""Tests for tools/athlete.py and tools/sport_settings.py.

Uses tests/_tool_helpers.py to keep each parametrized case to one row in a
table. One success row + one error row per tool.
"""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    apply_plan_changes,
    apply_sport_settings,
    create_sport_settings,
    get_athlete,
    get_athlete_profile,
    get_fitness_model_events,
    get_sport_settings,
    get_training_plan,
    list_sport_settings,
    set_training_plan,
    update_athlete,
    update_sport_settings,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    assert_substrings,
    run_tool,
)


ATHLETE_SAMPLE = {
    "id": "i1",
    "firstname": "Ada",
    "lastname": "Lovelace",
    "icu_weight": 60.0,
    "icu_resting_hr": 48,
    "timezone": "Europe/Sofia",
    "icu_type_settings": [{"type": "Ride"}],
}

PROFILE_SAMPLE = {
    "athlete": ATHLETE_SAMPLE,
    "sharedFolders": [{"id": 1, "name": "Base"}],
    "customItems": [],
}

PLAN_SAMPLE = {
    "athlete_id": "i1",
    "training_plan_id": 9,
    "training_plan_start_date": "2026-01-01",
    "training_plan_alias": "Build",
    "training_plan": {"id": 9, "name": "Build Folder"},
}

SPORT_SETTINGS_SAMPLE = {
    "id": "Ride",
    "athlete_id": "i1",
    "types": ["Ride"],
    "ftp": 280,
    "lthr": 165,
    "max_hr": 188,
    "power_zones": [55, 75, 90, 105, 120],
}


# (tool, module, kwargs, fake_response, expected substrings in result,
#  expected url, expected method)
SUCCESS_CASES = [
    pytest.param(
        get_athlete,
        "athlete",
        {"athlete_id": "1"},
        ATHLETE_SAMPLE,
        ["Ada Lovelace", "Europe/Sofia"],
        "/athlete/1",
        None,
        id="get_athlete",
    ),
    pytest.param(
        update_athlete,
        "athlete",
        {"payload": {"icu_weight": 61.0}, "athlete_id": "1"},
        ATHLETE_SAMPLE,
        ["Updated athlete", "Ada Lovelace"],
        "/athlete/1",
        "PUT",
        id="update_athlete",
    ),
    pytest.param(
        get_athlete_profile,
        "athlete",
        {"athlete_id": "1"},
        PROFILE_SAMPLE,
        ["Athlete Profile", "Base"],
        "/athlete/1/profile",
        None,
        id="get_athlete_profile",
    ),
    pytest.param(
        get_training_plan,
        "athlete",
        {"athlete_id": "1"},
        PLAN_SAMPLE,
        ["Training Plan:", "Build Folder", "Build"],
        "/athlete/1/training-plan",
        None,
        id="get_training_plan",
    ),
    pytest.param(
        set_training_plan,
        "athlete",
        {"payload": {"training_plan_id": 9}, "athlete_id": "1"},
        PLAN_SAMPLE,
        ["Training plan updated"],
        "/athlete/1/training-plan",
        "PUT",
        id="set_training_plan",
    ),
    pytest.param(
        apply_plan_changes,
        "athlete",
        {"athlete_id": "1"},
        {},
        ["Plan changes applied"],
        "/athlete/1/apply-plan-changes",
        "PUT",
        id="apply_plan_changes",
    ),
    pytest.param(
        get_fitness_model_events,
        "athlete",
        {"athlete_id": "1", "start_date": "2026-01-01", "end_date": "2026-01-31"},
        [
            {"start_date_local": "2026-01-15", "category": "WORKOUT", "name": "VO2"},
        ],
        ["Fitness model events (1)", "VO2"],
        "/athlete/1/fitness-model-events",
        None,
        id="get_fitness_model_events",
    ),
    pytest.param(
        list_sport_settings,
        "sport_settings",
        {"athlete_id": "1"},
        [SPORT_SETTINGS_SAMPLE],
        ["Sport Settings (1)", "FTP=280"],
        "/athlete/1/sport-settings",
        None,
        id="list_sport_settings",
    ),
    pytest.param(
        get_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "athlete_id": "1"},
        SPORT_SETTINGS_SAMPLE,
        ["FTP: 280W", "Ride"],
        "/athlete/1/sport-settings/Ride",
        None,
        id="get_sport_settings",
    ),
    pytest.param(
        create_sport_settings,
        "sport_settings",
        {"payload": {"types": ["Run"], "ftp": 350}, "athlete_id": "1"},
        SPORT_SETTINGS_SAMPLE,
        ["Sport settings created"],
        "/athlete/1/sport-settings",
        "POST",
        id="create_sport_settings",
    ),
    pytest.param(
        update_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "payload": {"ftp": 290}, "athlete_id": "1"},
        SPORT_SETTINGS_SAMPLE,
        ["Sport settings updated"],
        "/athlete/1/sport-settings/Ride",
        "PUT",
        id="update_sport_settings",
    ),
    pytest.param(
        apply_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "athlete_id": "1"},
        {},
        ["apply queued"],
        "/athlete/1/sport-settings/Ride/apply",
        "PUT",
        id="apply_sport_settings",
    ),
]


@pytest.mark.parametrize(
    "tool, module, kwargs, fake_resp, expected, exp_url, exp_method", SUCCESS_CASES
)
def test_tool_success(monkeypatch, tool, module, kwargs, fake_resp, expected, exp_url, exp_method):
    captured: dict = {}
    result = run_tool(monkeypatch, tool, module, kwargs, fake_resp, captured)
    assert_substrings(result, expected)
    assert captured["last"]["url"] == exp_url
    if exp_method is not None:
        assert captured["last"]["method"] == exp_method


ERROR_CASES = [
    pytest.param(get_athlete, "athlete", {"athlete_id": "1"}, "Error fetching athlete", id="get_athlete"),
    pytest.param(
        update_athlete,
        "athlete",
        {"payload": {}, "athlete_id": "1"},
        "Error updating athlete",
        id="update_athlete",
    ),
    pytest.param(
        get_athlete_profile,
        "athlete",
        {"athlete_id": "1"},
        "Error fetching athlete profile",
        id="get_athlete_profile",
    ),
    pytest.param(
        get_training_plan,
        "athlete",
        {"athlete_id": "1"},
        "Error fetching training plan",
        id="get_training_plan",
    ),
    pytest.param(
        set_training_plan,
        "athlete",
        {"payload": {}, "athlete_id": "1"},
        "Error setting training plan",
        id="set_training_plan",
    ),
    pytest.param(
        apply_plan_changes,
        "athlete",
        {"athlete_id": "1"},
        "Error applying plan changes",
        id="apply_plan_changes",
    ),
    pytest.param(
        get_fitness_model_events,
        "athlete",
        {"athlete_id": "1"},
        "Error fetching fitness-model events",
        id="get_fitness_model_events",
    ),
    pytest.param(
        list_sport_settings,
        "sport_settings",
        {"athlete_id": "1"},
        "Error fetching sport settings",
        id="list_sport_settings",
    ),
    pytest.param(
        get_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "athlete_id": "1"},
        "Error fetching sport settings",
        id="get_sport_settings",
    ),
    pytest.param(
        create_sport_settings,
        "sport_settings",
        {"payload": {}, "athlete_id": "1"},
        "Error creating sport settings",
        id="create_sport_settings",
    ),
    pytest.param(
        update_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "payload": {}, "athlete_id": "1"},
        "Error updating sport settings",
        id="update_sport_settings",
    ),
    pytest.param(
        apply_sport_settings,
        "sport_settings",
        {"settings_id": "Ride", "athlete_id": "1"},
        "Error applying sport settings",
        id="apply_sport_settings",
    ),
]


@pytest.mark.parametrize("tool, module, kwargs, err_prefix", ERROR_CASES)
def test_tool_error(monkeypatch, tool, module, kwargs, err_prefix):
    result = run_tool(
        monkeypatch,
        tool,
        module,
        kwargs,
        fake_response={"error": True, "message": "boom"},
    )
    assert err_prefix in result
    assert "boom" in result
