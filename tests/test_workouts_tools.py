"""Tests for tools/workouts.py and tools/folders.py."""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    create_folder,
    create_workout,
    delete_folder,
    delete_workout,
    get_workout,
    list_folders,
    list_workouts,
    update_folder,
    update_workout,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    assert_substrings,
    run_tool,
)

WORKOUT_SAMPLE = {
    "id": 7,
    "name": "VO2 6x3",
    "description": "6 x 3min @ 110% FTP",
    "type": "Ride",
    "moving_time": 4500,
    "icu_training_load": 85,
    "workout_doc": {"steps": [{"duration": 300}, {"duration": 180}, {"duration": 300}]},
}

FOLDER_SAMPLE = {
    "id": 99,
    "name": "Base 1",
    "type": "PLAN",
    "num_workouts": 12,
    "activity_types": ["Ride"],
}


SUCCESS_CASES = [
    pytest.param(
        list_workouts,
        "workouts",
        {"athlete_id": "1"},
        [WORKOUT_SAMPLE, WORKOUT_SAMPLE],
        ["Workouts (2)", "VO2 6x3"],
        "/athlete/1/workouts",
        None,
        id="list_workouts",
    ),
    pytest.param(
        get_workout,
        "workouts",
        {"workout_id": "7", "athlete_id": "1"},
        WORKOUT_SAMPLE,
        ["VO2 6x3", "Intervals: 3"],
        "/athlete/1/workouts/7",
        None,
        id="get_workout",
    ),
    pytest.param(
        create_workout,
        "workouts",
        {"payload": {"name": "X", "type": "Ride", "folder_id": 1}, "athlete_id": "1"},
        WORKOUT_SAMPLE,
        ["Workout created"],
        "/athlete/1/workouts",
        "POST",
        id="create_workout",
    ),
    pytest.param(
        update_workout,
        "workouts",
        {"workout_id": "7", "payload": {"name": "Y"}, "athlete_id": "1"},
        WORKOUT_SAMPLE,
        ["Workout updated"],
        "/athlete/1/workouts/7",
        "PUT",
        id="update_workout",
    ),
    pytest.param(
        delete_workout,
        "workouts",
        {"workout_id": "7", "athlete_id": "1"},
        {},
        ["Workout 7 deleted"],
        "/athlete/1/workouts/7",
        "DELETE",
        id="delete_workout",
    ),
    pytest.param(
        list_folders,
        "folders",
        {"athlete_id": "1"},
        [FOLDER_SAMPLE],
        ["Folders (1)", "Base 1", "PLAN"],
        "/athlete/1/folders",
        None,
        id="list_folders",
    ),
    pytest.param(
        create_folder,
        "folders",
        {"name": "Build", "athlete_id": "1", "folder_type": "PLAN", "activity_types": ["Ride"]},
        FOLDER_SAMPLE,
        ["Folder created", "Base 1"],
        "/athlete/1/folders",
        "POST",
        id="create_folder",
    ),
    pytest.param(
        update_folder,
        "folders",
        {"folder_id": "99", "athlete_id": "1", "name": "New Name"},
        {},
        ["Folder 99 updated"],
        "/athlete/1/folders/99",
        "PUT",
        id="update_folder",
    ),
    pytest.param(
        delete_folder,
        "folders",
        {"folder_id": "99", "athlete_id": "1"},
        {},
        ["Folder 99 deleted"],
        "/athlete/1/folders/99",
        "DELETE",
        id="delete_folder",
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


def test_create_folder_payload_includes_only_provided_fields(monkeypatch):
    """Optional folder fields aren't sent when omitted."""
    captured: dict = {}
    run_tool(
        monkeypatch,
        create_folder,
        "folders",
        kwargs={"name": "X", "athlete_id": "1"},
        fake_response=FOLDER_SAMPLE,
        capture=captured,
    )
    assert captured["last"]["data"] == {"name": "X", "type": "FOLDER"}


ERROR_CASES = [
    pytest.param(list_workouts, "workouts", {"athlete_id": "1"}, "Error fetching workouts", id="list_workouts"),
    pytest.param(
        get_workout, "workouts", {"workout_id": "7", "athlete_id": "1"}, "Error fetching workout",
        id="get_workout",
    ),
    pytest.param(
        create_workout, "workouts", {"payload": {}, "athlete_id": "1"}, "Error creating workout",
        id="create_workout",
    ),
    pytest.param(
        update_workout,
        "workouts",
        {"workout_id": "7", "payload": {}, "athlete_id": "1"},
        "Error updating workout",
        id="update_workout",
    ),
    pytest.param(
        delete_workout, "workouts", {"workout_id": "7", "athlete_id": "1"}, "Error deleting workout",
        id="delete_workout",
    ),
    pytest.param(list_folders, "folders", {"athlete_id": "1"}, "Error fetching folders", id="list_folders"),
    pytest.param(
        create_folder, "folders", {"name": "X", "athlete_id": "1"}, "Error creating folder",
        id="create_folder",
    ),
    pytest.param(
        update_folder, "folders", {"folder_id": "99", "athlete_id": "1"}, "Error updating folder",
        id="update_folder",
    ),
    pytest.param(
        delete_folder, "folders", {"folder_id": "99", "athlete_id": "1"}, "Error deleting folder",
        id="delete_folder",
    ),
]


@pytest.mark.parametrize("tool, module, kwargs, err_prefix", ERROR_CASES)
def test_tool_error(monkeypatch, tool, module, kwargs, err_prefix):
    result = run_tool(
        monkeypatch, tool, module, kwargs, fake_response={"error": True, "message": "boom"}
    )
    assert err_prefix in result
    assert "boom" in result
