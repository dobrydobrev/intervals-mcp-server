"""
Wellness-related MCP tools for Intervals.icu.

This module contains tools for retrieving and updating athlete wellness data
(daily check-ins: sleep, HRV, resting HR, soreness, mood, etc.).
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_wellness_entry
from intervals_mcp_server.utils.validation import (
    resolve_athlete_id,
    resolve_date_params,
    validate_date,
)

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def get_wellness_data(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_all_fields: bool = False,
) -> str:
    """Get wellness data for an athlete from Intervals.icu.

    By default returns standard wellness fields (training metrics, vitals, sleep,
    subjective scores, etc.). Set include_all_fields=True to also include any
    additional or custom fields configured by the user in Intervals.icu.

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        include_all_fields: If True, include additional and custom fields beyond the standard set (optional, defaults to False)
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    start_date, end_date = resolve_date_params(start_date, end_date)

    params = {"oldest": start_date, "newest": end_date}

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness", api_key=api_key, params=params
    )

    if isinstance(result, dict) and "error" in result:
        return f"Error fetching wellness data: {result.get('message')}"

    if not result:
        return (
            f"No wellness data found for athlete {athlete_id_to_use} in the specified date range."
        )

    wellness_summary = "Wellness Data:\n\n"

    if isinstance(result, dict):
        for date_str, data in result.items():
            if isinstance(data, dict) and "date" not in data:
                data["date"] = date_str
            wellness_summary += format_wellness_entry(data, include_all_fields=include_all_fields) + "\n\n"
    elif isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                wellness_summary += format_wellness_entry(entry, include_all_fields=include_all_fields) + "\n\n"

    return wellness_summary


@mcp.tool()
async def get_wellness_day(
    date: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    include_all_fields: bool = False,
) -> str:
    """Get the wellness record for a single day.

    Args:
        date: Local ISO-8601 day (YYYY-MM-DD).
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        include_all_fields: If True, also render custom fields.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness/{validate_date(date)}", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching wellness for {date}: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No wellness record found for {date}."
    if "date" not in result:
        result["date"] = date
    return format_wellness_entry(result, include_all_fields=include_all_fields)


@mcp.tool()
async def set_wellness_day(
    date: str,
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Create or update the wellness record for a single day.

    Args:
        date: Local ISO-8601 day (YYYY-MM-DD). Used as the record id.
        payload: Wellness fields to set, e.g.
            {"sleepSecs": 28800, "restingHR": 48, "soreness": 2, "fatigue": 3}.
            Only fields you set are changed.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness/{validate_date(date)}",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error updating wellness for {date}: {result.get('message')}"
    if isinstance(result, dict):
        if "date" not in result:
            result["date"] = date
        return f"Updated wellness for {date}:\n" + format_wellness_entry(result)
    return f"Wellness updated for {date}."


@mcp.tool()
async def bulk_update_wellness(
    entries: list[dict[str, Any]],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Update multiple wellness days in one request.

    Args:
        entries: List of Wellness dicts. Each entry's "id" must be the ISO-8601
            day (YYYY-MM-DD); the API only changes fields you provide.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    if not entries:
        return "Error: no wellness entries provided."

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/wellness-bulk",
        api_key=api_key,
        method="PUT",
        data=entries,  # type: ignore[arg-type]
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error bulk-updating wellness: {result.get('message')}"
    updated = result if isinstance(result, list) else []
    lines = [f"Updated {len(entries)} wellness records for athlete {athlete_id_to_use}."]
    if updated:
        lines.append(f"API returned {len(updated)} records.")
    return "\n".join(lines)
