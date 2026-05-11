"""Tests for the wellness day-level read/write + bulk-update tools."""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("ATHLETE_ID", "i1")

from intervals_mcp_server.server import (  # noqa: E402  pylint: disable=wrong-import-position
    bulk_update_wellness,
    get_wellness_day,
    set_wellness_day,
)
from tests._tool_helpers import (  # noqa: E402  pylint: disable=wrong-import-position
    run_tool,
)


WELLNESS_SAMPLE = {
    "id": "2026-05-11",
    "date": "2026-05-11",
    "ctl": 78,
    "atl": 65,
    "restingHR": 48,
    "sleepSecs": 28800,
}


def test_get_wellness_day(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        get_wellness_day,
        "wellness",
        kwargs={"date": "2026-05-11", "athlete_id": "1"},
        fake_response=WELLNESS_SAMPLE,
        capture=captured,
    )
    assert "Wellness" in result or "2026-05-11" in result
    assert captured["last"]["url"] == "/athlete/1/wellness/2026-05-11"


def test_get_wellness_day_validates_date(monkeypatch):
    """Invalid date format raises before any request is made."""

    async def boom(*_args, **_kwargs):
        raise AssertionError("should not call API")

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", boom)
    monkeypatch.setattr("intervals_mcp_server.tools.wellness.make_intervals_request", boom)
    import asyncio

    with pytest.raises(ValueError):
        asyncio.run(get_wellness_day(date="11-05-2026", athlete_id="1"))


def test_set_wellness_day(monkeypatch):
    captured: dict = {}
    result = run_tool(
        monkeypatch,
        set_wellness_day,
        "wellness",
        kwargs={
            "date": "2026-05-11",
            "payload": {"sleepSecs": 28800, "fatigue": 2},
            "athlete_id": "1",
        },
        fake_response=WELLNESS_SAMPLE,
        capture=captured,
    )
    assert "Updated wellness for 2026-05-11" in result
    assert captured["last"]["url"] == "/athlete/1/wellness/2026-05-11"
    assert captured["last"]["method"] == "PUT"
    assert captured["last"]["data"] == {"sleepSecs": 28800, "fatigue": 2}


def test_bulk_update_wellness(monkeypatch):
    captured: dict = {}
    entries = [
        {"id": "2026-05-10", "sleepSecs": 25200},
        {"id": "2026-05-11", "sleepSecs": 28800},
    ]
    result = run_tool(
        monkeypatch,
        bulk_update_wellness,
        "wellness",
        kwargs={"entries": entries, "athlete_id": "1"},
        fake_response=[WELLNESS_SAMPLE, WELLNESS_SAMPLE],
        capture=captured,
    )
    assert "Updated 2 wellness records" in result
    assert captured["last"]["url"] == "/athlete/1/wellness-bulk"
    assert captured["last"]["method"] == "PUT"
    assert captured["last"]["data"] == entries


def test_bulk_update_wellness_empty_list(monkeypatch):
    async def boom(*_args, **_kwargs):
        raise AssertionError("should not call API")

    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", boom)
    monkeypatch.setattr("intervals_mcp_server.tools.wellness.make_intervals_request", boom)
    import asyncio

    result = asyncio.run(bulk_update_wellness(entries=[], athlete_id="1"))
    assert "no wellness entries" in result


ERROR_CASES = [
    pytest.param(
        get_wellness_day, {"date": "2026-05-11", "athlete_id": "1"},
        "Error fetching wellness for 2026-05-11",
        id="get_wellness_day",
    ),
    pytest.param(
        set_wellness_day, {"date": "2026-05-11", "payload": {}, "athlete_id": "1"},
        "Error updating wellness for 2026-05-11",
        id="set_wellness_day",
    ),
    pytest.param(
        bulk_update_wellness, {"entries": [{"id": "2026-05-11"}], "athlete_id": "1"},
        "Error bulk-updating wellness",
        id="bulk_update_wellness",
    ),
]


@pytest.mark.parametrize("tool, kwargs, err", ERROR_CASES)
def test_tool_error(monkeypatch, tool, kwargs, err):
    result = run_tool(
        monkeypatch, tool, "wellness", kwargs, fake_response={"error": True, "message": "boom"}
    )
    assert err in result
    assert "boom" in result
