# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (including dev extras)
uv sync --all-extras

# Run the full test suite
pytest -v tests

# Run a single test file or test
pytest tests/test_event_extensions.py
pytest tests/test_event_extensions.py::test_add_or_update_event

# Lint
ruff .

# Type check
mypy src tests

# Run the server manually
mcp run src/intervals_mcp_server/server.py
```

All three checks (`ruff`, `mypy`, `pytest`) must pass before committing.

## Architecture

This is a [FastMCP](https://github.com/modelcontextprotocol/python-sdk)-based MCP server that wraps the Intervals.icu REST API.

### Registration flow

Tools self-register via `@mcp.tool()` decorators on import. `server.py` imports every tool module, which triggers registration against the `FastMCP` singleton in `mcp_instance.py`. Nothing else wires them up.

### Key layers

- **`api/client.py`** — single HTTP gateway. `make_intervals_request(url, ...)` is the only function that calls the Intervals.icu API. It returns `dict | list[dict]` on success, or `{"error": True, "message": ...}` on failure. All tool modules import and call this function.
- **`config.py`** — reads `ATHLETE_ID`, `API_KEY`, `INTERVALS_API_BASE_URL`, `LOG_LEVEL`, and `MCP_TRANSPORT` from the environment (`.env` via `python-dotenv`).
- **`tools/`** — one module per domain (`activities`, `athlete`, `curves`, `events`, `folders`, `sport_settings`, `wellness`, `workouts`, `custom_items`). Every tool returns a human-formatted string (never raw JSON).
- **`utils/formatting.py`** — shared formatters for human-readable output; includes `_KeyTracker` for key-access tracing.
- **`server_setup.py`** — transport selection logic. Defaults to `stdio`; set `MCP_TRANSPORT=sse` or `MCP_TRANSPORT=streamable-http` (alias `http`) for network transports.

### Tool conventions

- `athlete_id` and `api_key` are optional on every tool and fall back to the env vars.
- Date parameters accept `YYYY-MM-DD`.
- PUT/POST tools take a generic `payload: dict` (the LLM constructs the JSON body), except for small/stable endpoints like folders.
- Curve tools default to coach-canonical time buckets; pass `summary_only=False` for full data.

### Testing pattern

Tests mock `make_intervals_request` using helpers in `tests/_tool_helpers.py`:

```python
from tests._tool_helpers import run_tool, assert_substrings

def test_my_tool(monkeypatch):
    captured = {}
    result = run_tool(
        monkeypatch, my_tool_fn, "module_name",
        kwargs={"athlete_id": "i123"},
        fake_response={"id": "i123"},
        capture=captured,
    )
    assert_substrings(result, ["Expected text"])
    assert captured["last"]["url"] == "/athlete/i123/..."
```

`run_tool` patches both `intervals_mcp_server.api.client.make_intervals_request` and `intervals_mcp_server.tools.<module>.make_intervals_request` so the tool sees the stub regardless of import path.

## PR conventions

- Title format: `[intervals-mcp-server] <brief description>`
- Describe manual testing steps and confirm `pytest`, `ruff`, and `mypy` passed.
