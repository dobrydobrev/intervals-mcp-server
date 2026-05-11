"""
Sport-settings MCP tools for Intervals.icu.

Per-sport zone definitions, thresholds (FTP, LTHR, threshold pace), and pace
units. Critical for any coaching tool that prescribes intensities.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import (
    format_sport_settings_details,
    format_sport_settings_summary,
)
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def list_sport_settings(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """List sport-settings records for the athlete (one per sport type).

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching sport settings: {result.get('message')}"
    settings_list = result if isinstance(result, list) else []
    return format_sport_settings_summary(settings_list)


@mcp.tool()
async def get_sport_settings(
    settings_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get one sport-settings record by id or activity type (e.g. "Run", "Ride").

    Args:
        settings_id: Sport-settings ID or activity type alias.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{settings_id}", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching sport settings: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No sport settings found for {settings_id}."
    return format_sport_settings_details(result)


@mcp.tool()
async def create_sport_settings(
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Create new sport-settings for a sport (FTP, LTHR, zones, etc.).

    Args:
        payload: Dict matching the Intervals.icu SportSettings shape.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings",
        api_key=api_key,
        method="POST",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error creating sport settings: {result.get('message')}"
    if isinstance(result, dict):
        return "Sport settings created:\n" + format_sport_settings_details(result)
    return f"Sport settings created for athlete {athlete_id_to_use}."


@mcp.tool()
async def update_sport_settings(
    settings_id: str,
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Update an existing sport-settings record.

    Args:
        settings_id: Sport-settings ID or activity type alias.
        payload: Partial dict; only fields you set are updated.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{settings_id}",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error updating sport settings: {result.get('message')}"
    if isinstance(result, dict):
        return "Sport settings updated:\n" + format_sport_settings_details(result)
    return f"Sport settings {settings_id} updated."


@mcp.tool()
async def apply_sport_settings(
    settings_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Recompute zones on matching historical activities (async upstream).

    Args:
        settings_id: Sport-settings ID or activity type alias.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/sport-settings/{settings_id}/apply",
        api_key=api_key,
        method="PUT",
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error applying sport settings: {result.get('message')}"
    return f"Sport settings {settings_id} apply queued for athlete {athlete_id_to_use}."
