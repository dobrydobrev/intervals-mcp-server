"""Shared helpers for testing MCP tools.

Tools in ``intervals_mcp_server.tools.*`` all follow the same shape: they call
``make_intervals_request`` then format the result into a human string. The
helpers here mock that single dependency so a tool test is reduced to:

    captured: dict = {}
    result = run_tool(
        monkeypatch, get_event_by_id, "events",
        kwargs={"event_id": "e1", "athlete_id": "1"},
        fake_response={"id": "e1", "name": "X"},
        capture=captured,
    )
    assert_substrings(result, ["Event Details", "X"])
    assert captured["last"]["url"] == "/athlete/1/events/e1"

This keeps the existing one-test-per-tool pattern but removes the inline
``async def fake_request`` and the double ``monkeypatch.setattr`` boilerplate.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Iterable
from typing import Any


def make_fake_request(
    response: Any,
    capture: dict[str, Any] | None = None,
) -> Callable[..., Coroutine[Any, Any, Any]]:
    """Return an async stub for ``make_intervals_request``.

    If ``capture`` is provided, the request's keyword arguments are recorded
    under ``capture["last"]`` so the caller can assert on URL/method/params.
    """

    async def _fake(*_args: Any, **kwargs: Any) -> Any:
        if capture is not None:
            capture["last"] = {
                "url": kwargs.get("url"),
                "method": kwargs.get("method"),
                "params": kwargs.get("params"),
                "data": kwargs.get("data"),
                "api_key": kwargs.get("api_key"),
            }
        return response

    return _fake


def run_tool(
    monkeypatch: Any,
    tool: Callable[..., Coroutine[Any, Any, str]],
    module_path: str,
    kwargs: dict[str, Any],
    fake_response: Any,
    capture: dict[str, Any] | None = None,
) -> str:
    """Invoke an MCP tool with a mocked ``make_intervals_request``.

    Patches both ``intervals_mcp_server.api.client.make_intervals_request`` and
    ``intervals_mcp_server.tools.<module_path>.make_intervals_request`` so the
    tool sees the stubbed response regardless of which import path it uses.
    """
    fake = make_fake_request(fake_response, capture)
    monkeypatch.setattr("intervals_mcp_server.api.client.make_intervals_request", fake)
    monkeypatch.setattr(
        f"intervals_mcp_server.tools.{module_path}.make_intervals_request", fake
    )
    return asyncio.run(tool(**kwargs))


def assert_substrings(result: str, expected: Iterable[str]) -> None:
    """Assert every string in ``expected`` appears in ``result``."""
    for piece in expected:
        assert piece in result, f"expected {piece!r} in:\n{result}"
