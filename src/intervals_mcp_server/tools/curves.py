"""
Athlete-level performance-curve MCP tools for Intervals.icu.

Power / HR / pace best-curves over date ranges, plus the MMP power-duration
model used to resolve ``%MMP`` workout steps. The curve tools downsample to
coach-canonical durations by default — pass ``summary_only=False`` to get the
full ``secs[]``/``values[]`` arrays.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_curve_set, format_mmp_model
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


def _build_curve_params(
    start_date: str | None,
    end_date: str | None,
    sport_type: str,
    curves: str | None,
) -> dict[str, Any]:
    """Assemble query params for the curve endpoints."""
    params: dict[str, Any] = {"type": sport_type}
    if start_date is not None:
        params["oldest"] = start_date
    if end_date is not None:
        params["newest"] = end_date
    if curves is not None:
        params["curves"] = curves
    return params


def _extract_curve_list(result: Any) -> list[dict[str, Any]]:
    """Pull a list of curves from either {"list": [...]} or a raw list response."""
    if isinstance(result, dict):
        curve_list = result.get("list")
        return curve_list if isinstance(curve_list, list) else []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    return []


async def _fetch_athlete_curves(
    endpoint: str,
    curve_kind: str,
    athlete_id: str | None,
    api_key: str | None,
    start_date: str | None,
    end_date: str | None,
    sport_type: str,
    curves: str | None,
    summary_only: bool,
) -> str:
    """Shared body for the three athlete curve tools."""
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/{endpoint}.json",
        api_key=api_key,
        params=_build_curve_params(start_date, end_date, sport_type, curves),
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching {curve_kind} curves: {result.get('message')}"
    return format_curve_set(_extract_curve_list(result), curve_kind, summary_only)


@mcp.tool()
async def get_athlete_power_curves(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sport_type: str = "Ride",
    curves: str | None = None,
    summary_only: bool = True,
) -> str:
    """List best power curves for the athlete.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        start_date: Optional YYYY-MM-DD; default chosen by the API.
        end_date: Optional YYYY-MM-DD.
        sport_type: Sport (e.g. "Ride", "Run"). Required by the endpoint.
        curves: Optional comma-separated curve labels (e.g. "1y,42d,s0").
        summary_only: When True (default) emit ~10 coach-canonical buckets per
            curve; False emits every (secs, value) pair.
    """
    return await _fetch_athlete_curves(
        "power-curves", "power",
        athlete_id, api_key, start_date, end_date, sport_type, curves, summary_only,
    )


@mcp.tool()
async def get_athlete_hr_curves(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sport_type: str = "Ride",
    curves: str | None = None,
    summary_only: bool = True,
) -> str:
    """List best heart-rate curves for the athlete. See get_athlete_power_curves."""
    return await _fetch_athlete_curves(
        "hr-curves", "hr",
        athlete_id, api_key, start_date, end_date, sport_type, curves, summary_only,
    )


@mcp.tool()
async def get_athlete_pace_curves(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sport_type: str = "Run",
    curves: str | None = None,
    summary_only: bool = True,
) -> str:
    """List best pace curves for the athlete. Pace defaults to Run.

    Values are returned in m/s and rendered alongside a min/km label.
    """
    return await _fetch_athlete_curves(
        "pace-curves", "pace",
        athlete_id, api_key, start_date, end_date, sport_type, curves, summary_only,
    )


@mcp.tool()
async def get_mmp_model(
    athlete_id: str | None = None,
    api_key: str | None = None,
    sport_type: str = "Ride",
    date: str | None = None,
) -> str:
    """Get the MMP (mean-max-power) model used to resolve ``%MMP`` workout steps.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        sport_type: Sport (default "Ride").
        date: Optional anchor date in YYYY-MM-DD; the API computes the model
            over the preceding ``icu_mmp_days`` window.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    params: dict[str, Any] = {"type": sport_type}
    if date is not None:
        params["date"] = date

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/mmp-model", api_key=api_key, params=params
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching MMP model: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No MMP model returned for athlete {athlete_id_to_use}."
    return format_mmp_model(result)
