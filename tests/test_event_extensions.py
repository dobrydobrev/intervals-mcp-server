"""Tests for the bulk + plan + tag tools added to tools/events.py."""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    apply_plan_to_calendar,
    bulk_create_events,
    bulk_delete_events,
    duplicate_events,
    list_event_tags,
    list_workout_tags,
    mark_event_done,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    assert_substrings,
    run_tool,
)


EVENT_SAMPLE = {
    "id": "e1",
    "name": "VO2",
    "date": "2026-01-15",
    "category": "WORKOUT",
}


def test_bulk_create_events_summary(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        bulk_create_events,
        "events",
        kwargs={
            "events": [{"name": "VO2", "start_date_local": "2026-01-15T00:00:00"}],
            "athlete_id": "1",
        },
        fake_response=[EVENT_SAMPLE, EVENT_SAMPLE, EVENT_SAMPLE],
        capture=captured,
    )
    assert "Created 3 events" in result
    assert "VO2" in result
    assert captured["last"]["url"] == "/athlete/1/events/bulk"
    assert captured["last"]["method"] == "POST"
    assert captured["last"]["data"][0]["category"] == "WORKOUT"


def test_mark_event_done(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        mark_event_done,
        "events",
        kwargs={"event_id": "e1", "athlete_id": "1"},
        fake_response={"id": "act-9"},
        capture=captured,
    )
    assert_substrings(result, ["marked done", "act-9"])
    assert captured["last"]["url"] == "/athlete/1/events/e1/mark-done"
    assert captured["last"]["method"] == "POST"


def test_apply_plan_to_calendar(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        apply_plan_to_calendar,
        "events",
        kwargs={
            "payload": {"folder_id": 99, "start_date_local": "2026-02-01"},
            "athlete_id": "1",
        },
        fake_response={},
        capture=captured,
    )
    assert "Plan applied" in result
    assert captured["last"]["url"] == "/athlete/1/events/apply-plan"
    assert captured["last"]["data"] == {"folder_id": 99, "start_date_local": "2026-02-01"}


def test_bulk_delete_events_wraps_ids(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        bulk_delete_events,
        "events",
        kwargs={"event_ids": [1, 2, 3], "athlete_id": "1"},
        fake_response={},
        capture=captured,
    )
    assert "Deleted 3 events" in result
    assert captured["last"]["url"] == "/athlete/1/events/bulk-delete"
    assert captured["last"]["method"] == "PUT"
    assert captured["last"]["data"] == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_bulk_delete_events_empty_list(monkeypatch):
    """Empty id list short-circuits without hitting the API."""

    async def boom(*_args, **_kwargs):
        raise AssertionError("should not be called")

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", boom)
    monkeypatch.setattr("intervals_mcp_server.tools.events.make_intervals_request", boom)
    import asyncio

    result = asyncio.run(bulk_delete_events(event_ids=[], athlete_id="1"))
    assert "no event ids" in result


def test_duplicate_events(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        duplicate_events,
        "events",
        kwargs={"payload": {"ids": [1, 2], "target_date_local": "2026-02-01"}, "athlete_id": "1"},
        fake_response=[EVENT_SAMPLE, EVENT_SAMPLE],
        capture=captured,
    )
    assert "Duplicated 2 events" in result
    assert captured["last"]["url"] == "/athlete/1/duplicate-events"


def test_list_workout_tags(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        list_workout_tags,
        "events",
        kwargs={"athlete_id": "1"},
        fake_response=["base", "vo2", "race-prep"],
        capture=captured,
    )
    assert_substrings(result, ["Workout tags (3)", "vo2"])
    assert captured["last"]["url"] == "/athlete/1/workout-tags"


def test_list_event_tags_empty(monkeypatch):
    result = run_tool(
        monkeypatch, list_event_tags, "events", {"athlete_id": "1"}, fake_response=[]
    )
    assert "No event tags" in result


ERROR_CASES = [
    pytest.param(
        bulk_create_events,
        {"events": [], "athlete_id": "1"},
        "Error creating events",
        id="bulk_create_events",
    ),
    pytest.param(
        mark_event_done,
        {"event_id": "e1", "athlete_id": "1"},
        "Error marking event done",
        id="mark_event_done",
    ),
    pytest.param(
        apply_plan_to_calendar,
        {"payload": {}, "athlete_id": "1"},
        "Error applying plan",
        id="apply_plan_to_calendar",
    ),
    pytest.param(
        bulk_delete_events,
        {"event_ids": [1], "athlete_id": "1"},
        "Error deleting events",
        id="bulk_delete_events",
    ),
    pytest.param(
        duplicate_events,
        {"payload": {}, "athlete_id": "1"},
        "Error duplicating events",
        id="duplicate_events",
    ),
    pytest.param(
        list_workout_tags,
        {"athlete_id": "1"},
        "Error fetching workout tags",
        id="list_workout_tags",
    ),
    pytest.param(
        list_event_tags,
        {"athlete_id": "1"},
        "Error fetching event tags",
        id="list_event_tags",
    ),
]


@pytest.mark.parametrize("tool, kwargs, err_prefix", ERROR_CASES)
def test_tool_error(monkeypatch, tool, kwargs, err_prefix):
    result = run_tool(
        monkeypatch,
        tool,
        "events",
        kwargs,
        fake_response={"error": True, "message": "boom"},
    )
    assert err_prefix in result
    assert "boom" in result
