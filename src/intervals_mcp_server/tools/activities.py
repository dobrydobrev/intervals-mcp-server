"""
Activity-related MCP tools for Intervals.icu.

This module contains tools for retrieving and managing athlete activities.
"""

from datetime import datetime, timedelta
from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_activity_message, format_activity_summary, format_intervals
from intervals_mcp_server.utils.validation import resolve_athlete_id, resolve_date_params

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


def _parse_activities_from_result(result: Any) -> list[dict[str, Any]]:
    """Extract a list of activity dictionaries from the API result."""
    activities: list[dict[str, Any]] = []

    if isinstance(result, list):
        activities = [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        # Result is a single activity or a container
        for _key, value in result.items():
            if isinstance(value, list):
                activities = [item for item in value if isinstance(item, dict)]
                break
        # If no list was found but the dict has typical activity fields, treat it as a single activity
        if not activities and any(key in result for key in ["name", "startTime", "distance"]):
            activities = [result]

    return activities


def _filter_named_activities(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out unnamed activities from the list."""
    return [
        activity
        for activity in activities
        if activity.get("name") and activity.get("name") != "Unnamed"
    ]


async def _fetch_more_activities(
    athlete_id: str,
    start_date: str,
    api_key: str | None,
    api_limit: int,
) -> list[dict[str, Any]]:
    """Fetch additional activities from an earlier date range."""
    oldest_date = datetime.fromisoformat(start_date)
    older_start_date = (oldest_date - timedelta(days=60)).strftime("%Y-%m-%d")
    older_end_date = (oldest_date - timedelta(days=1)).strftime("%Y-%m-%d")

    if older_start_date >= older_end_date:
        return []

    more_params = {
        "oldest": older_start_date,
        "newest": older_end_date,
        "limit": api_limit,
    }
    more_result = await make_intervals_request(
        url=f"/athlete/{athlete_id}/activities",
        api_key=api_key,
        params=more_params,
    )

    if isinstance(more_result, list):
        return _filter_named_activities(more_result)
    return []


def _format_activities_response(
    activities: list[dict[str, Any]],
    athlete_id: str,
    include_unnamed: bool,
) -> str:
    """Format the activities response based on the results."""
    if not activities:
        if include_unnamed:
            return (
                f"No valid activities found for athlete {athlete_id} in the specified date range."
            )
        return f"No named activities found for athlete {athlete_id} in the specified date range. Try with include_unnamed=True to see all activities."

    # Format the output
    activities_summary = "Activities:\n\n"
    for activity in activities:
        if isinstance(activity, dict):
            activities_summary += format_activity_summary(activity) + "\n"
        else:
            activities_summary += f"Invalid activity format: {activity}\n\n"

    return activities_summary


@mcp.tool()
async def get_activities(  # pylint: disable=too-many-arguments,too-many-return-statements,too-many-branches,too-many-positional-arguments
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
    include_unnamed: bool = False,
) -> str:
    """Get a list of activities for an athlete from Intervals.icu

    Args:
        athlete_id: The Intervals.icu athlete ID (optional, will use ATHLETE_ID from .env if not provided)
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        limit: Maximum number of activities to return (optional, defaults to 10)
        include_unnamed: Whether to include unnamed activities (optional, defaults to False)
    """
    # Resolve athlete ID and date parameters
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    start_date, end_date = resolve_date_params(start_date, end_date)

    # Fetch more activities if we need to filter out unnamed ones
    api_limit = limit * 3 if not include_unnamed else limit

    # Call the Intervals.icu API
    params = {"oldest": start_date, "newest": end_date, "limit": api_limit}
    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities", api_key=api_key, params=params
    )

    # Check for error
    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activities: {error_message}"

    if not result:
        return f"No activities found for athlete {athlete_id_to_use} in the specified date range."

    # Parse activities from result
    activities = _parse_activities_from_result(result)

    if not activities:
        return f"No valid activities found for athlete {athlete_id_to_use} in the specified date range."

    # Filter and fetch more if needed
    if not include_unnamed:
        activities = _filter_named_activities(activities)

        # If we don't have enough named activities, try to fetch more
        if len(activities) < limit:
            more_activities = await _fetch_more_activities(
                athlete_id_to_use, start_date, api_key, api_limit
            )
            activities.extend(more_activities)

    # Limit to requested count
    activities = activities[:limit]

    return _format_activities_response(activities, athlete_id_to_use, include_unnamed)


@mcp.tool()
async def get_activity_details(activity_id: str, api_key: str | None = None) -> str:
    """Get detailed information for a specific activity from Intervals.icu

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    # Call the Intervals.icu API
    result = await make_intervals_request(url=f"/activity/{activity_id}", api_key=api_key)

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activity details: {error_message}"

    # Format the response
    if not result:
        return f"No details found for activity {activity_id}."

    # If result is a list, use the first item if available
    activity_data = result[0] if isinstance(result, list) and result else result
    if not isinstance(activity_data, dict):
        return f"Invalid activity format for activity {activity_id}."

    # Return a more detailed view of the activity
    detailed_view = format_activity_summary(activity_data)

    # Add additional details if available
    if "zones" in activity_data:
        zones = activity_data["zones"]
        detailed_view += "\nPower Zones:\n"
        for zone in zones.get("power", []):
            detailed_view += f"Zone {zone.get('number')}: {zone.get('secondsInZone')} seconds\n"

        detailed_view += "\nHeart Rate Zones:\n"
        for zone in zones.get("hr", []):
            detailed_view += f"Zone {zone.get('number')}: {zone.get('secondsInZone')} seconds\n"

    return detailed_view


@mcp.tool()
async def get_activity_intervals(activity_id: str, api_key: str | None = None) -> str:
    """Get interval data for a specific activity from Intervals.icu

    This endpoint returns detailed metrics for each interval in an activity, including power, heart rate,
    cadence, speed, and environmental data. It also includes grouped intervals if applicable.

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    # Call the Intervals.icu API
    result = await make_intervals_request(url=f"/activity/{activity_id}/intervals", api_key=api_key)

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching intervals: {error_message}"

    # Format the response
    if not result:
        return f"No interval data found for activity {activity_id}."

    # If the result is empty or doesn't contain expected fields
    if not isinstance(result, dict) or not any(
        key in result for key in ["icu_intervals", "icu_groups"]
    ):
        return f"No interval data or unrecognized format for activity {activity_id}."

    # Format the intervals data
    return format_intervals(result)


@mcp.tool()
async def get_activity_streams(
    activity_id: str,
    api_key: str | None = None,
    stream_types: str | None = None,
) -> str:
    """Get stream data for a specific activity from Intervals.icu

    This endpoint returns time-series data for an activity, including metrics like power, heart rate,
    cadence, altitude, distance, temperature, and velocity data.

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
        stream_types: Comma-separated list of stream types to retrieve (optional, defaults to all available types)
                     Available types: time, watts, heartrate, cadence, altitude, distance,
                     core_temperature, skin_temperature, velocity_smooth
    """
    # Build query parameters
    params = {}
    if stream_types:
        params["types"] = stream_types
    else:
        # Default to common stream types if none specified
        params["types"] = "time,watts,heartrate,cadence,altitude,distance,velocity_smooth"

    # Call the Intervals.icu API
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/streams",
        api_key=api_key,
        params=params,
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activity streams: {error_message}"

    # Format the response
    if not result:
        return f"No stream data found for activity {activity_id}."

    # Ensure result is a list
    streams = result if isinstance(result, list) else []

    if not streams:
        return f"No stream data found for activity {activity_id}."

    # Format the streams data
    streams_summary = f"Activity Streams for {activity_id}:\n\n"

    for stream in streams:
        if not isinstance(stream, dict):
            continue

        stream_type = stream.get("type", "unknown")
        stream_name = stream.get("name", stream_type)
        data = stream.get("data", [])
        value_type = stream.get("valueType", "")

        streams_summary += f"Stream: {stream_name} ({stream_type})\n"
        streams_summary += f"  Value Type: {value_type}\n"
        streams_summary += f"  Data Points: {len(data)}\n"

        # Show first few and last few data points for preview
        if data:
            if len(data) <= 10:
                streams_summary += f"  Values: {data}\n"
            else:
                preview_start = data[:5]
                preview_end = data[-5:]
                streams_summary += f"  First 5 values: {preview_start}\n"
                streams_summary += f"  Last 5 values: {preview_end}\n"

        streams_summary += "\n"

    return streams_summary


@mcp.tool()
async def get_activity_messages(activity_id: str, api_key: str | None = None) -> str:
    """Get messages (notes/comments) for a specific activity from Intervals.icu

    Args:
        activity_id: The Intervals.icu activity ID
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/messages",
        api_key=api_key,
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error fetching activity messages: {error_message}"

    if not result:
        return f"No messages found for activity {activity_id}."

    messages = result if isinstance(result, list) else []
    if not messages:
        return f"No messages found for activity {activity_id}."

    output = f"Messages for activity {activity_id}:\n\n"
    for msg in messages:
        if isinstance(msg, dict):
            output += format_activity_message(msg) + "\n\n"

    return output


@mcp.tool()
async def add_activity_message(
    activity_id: str,
    content: str,
    api_key: str | None = None,
) -> str:
    """Add a message (note/comment) to an activity on Intervals.icu

    Args:
        activity_id: The Intervals.icu activity ID
        content: The message text to add
        api_key: The Intervals.icu API key (optional, will use API_KEY from .env if not provided)
    """
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/messages",
        api_key=api_key,
        method="POST",
        data={"content": content},
    )

    if isinstance(result, dict) and "error" in result:
        error_message = result.get("message", "Unknown error")
        return f"Error adding message to activity: {error_message}"

    if not result or not isinstance(result, dict):
        return "Error: Unexpected response when adding message."

    msg_id = result.get("id")
    if msg_id is not None:
        return f"Successfully added message (ID: {msg_id}) to activity {activity_id}."
    return f"Message appears to have been added to activity {activity_id}, but no ID was returned. Please verify manually."


# ----------------------------------------------------------------------------
# Activity-level performance, search, and bulk-fetch tools (Tier 3).
# ----------------------------------------------------------------------------

# Imports kept local to avoid touching the top-of-file import block.
from intervals_mcp_server.utils.formatting import (  # noqa: E402  pylint: disable=wrong-import-position
    format_activity_search_hit,
    format_best_efforts,
    format_hr_curve,
    format_interval_match,
    format_interval_stats,
    format_pace_curve,
    format_power_curve,
    format_power_vs_hr,
    format_weather_summary,
)


@mcp.tool()
async def get_activity_best_efforts(activity_id: str, api_key: str | None = None) -> str:
    """Find best efforts in an activity (durations + averages).

    Args:
        activity_id: Intervals.icu activity ID.
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/best-efforts", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching best efforts: {result.get('message')}"
    return format_best_efforts(result if isinstance(result, (dict, list)) else {})


@mcp.tool()
async def get_activity_power_curve(
    activity_id: str,
    api_key: str | None = None,
    summary_only: bool = True,
) -> str:
    """Get the activity's power curve. summary_only emits coach-canonical buckets.

    Args:
        activity_id: Intervals.icu activity ID.
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        summary_only: When True (default) emit ~10 coach-canonical durations;
            False emits every (secs, value) pair from the API response.
    """
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/power-curve.json", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching power curve: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No power curve for activity {activity_id}."
    return format_power_curve(result, summary_only=summary_only)


@mcp.tool()
async def get_activity_hr_curve(
    activity_id: str,
    api_key: str | None = None,
    summary_only: bool = True,
) -> str:
    """Get the activity's HR curve. See get_activity_power_curve."""
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/hr-curve.json", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching hr curve: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No HR curve for activity {activity_id}."
    return format_hr_curve(result, summary_only=summary_only)


@mcp.tool()
async def get_activity_pace_curve(
    activity_id: str,
    api_key: str | None = None,
    summary_only: bool = True,
) -> str:
    """Get the activity's pace curve (values in m/s, rendered with min/km)."""
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/pace-curve.json", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching pace curve: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No pace curve for activity {activity_id}."
    return format_pace_curve(result, summary_only=summary_only)


@mcp.tool()
async def get_activity_power_vs_hr(
    activity_id: str,
    api_key: str | None = None,
    summary_only: bool = True,
) -> str:
    """Get the activity's power-vs-HR data (efficiency / cardiac-drift).

    Args:
        activity_id: Intervals.icu activity ID.
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        summary_only: When True (default) emit ~10 down-sampled HR/power pairs.
    """
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/power-vs-hr.json", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching power vs hr: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No power-vs-HR data for activity {activity_id}."
    return format_power_vs_hr(result, summary_only=summary_only)


@mcp.tool()
async def get_activity_interval_stats(
    activity_id: str,
    api_key: str | None = None,
    start_secs: int | None = None,
    end_secs: int | None = None,
) -> str:
    """Compute interval-like stats over a slice of an activity.

    Args:
        activity_id: Intervals.icu activity ID.
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        start_secs: Start offset in seconds (optional).
        end_secs: End offset in seconds (optional).
    """
    params: dict[str, Any] = {}
    if start_secs is not None:
        params["start_secs"] = start_secs
    if end_secs is not None:
        params["end_secs"] = end_secs
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/interval-stats",
        api_key=api_key,
        params=params or None,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching interval stats: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No interval stats for activity {activity_id}."
    return format_interval_stats(result)


@mcp.tool()
async def get_activity_weather_summary(activity_id: str, api_key: str | None = None) -> str:
    """Get the activity's weather summary (temp, wind, humidity, precip)."""
    result = await make_intervals_request(
        url=f"/activity/{activity_id}/weather-summary", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching weather summary: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No weather data for activity {activity_id}."
    return format_weather_summary(result)


@mcp.tool()
async def get_activities_by_ids(
    ids: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Fetch multiple activities by id in a single round-trip.

    Args:
        ids: Comma-separated list of activity IDs (e.g. "i1,i2,i3").
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities/{ids}", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching activities: {result.get('message')}"
    activities = result if isinstance(result, list) else []
    if not activities:
        return f"No activities found for ids {ids}.\n"
    return _format_activities_response(activities, athlete_id_to_use, include_unnamed=True)


@mcp.tool()
async def search_activities(
    query: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    limit: int = 20,
) -> str:
    """Search activities by name (case-insensitive) or tag (#tag-name).

    Args:
        query: Search query. Prefix with "#" for exact tag match.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        limit: Max results to return (default 20).
    """
    return await _search_activities(
        athlete_id, api_key, query, limit, endpoint="search", full=False
    )


@mcp.tool()
async def search_activities_full(
    query: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    limit: int = 20,
) -> str:
    """Search activities and return full activity records (heavier than search_activities)."""
    return await _search_activities(
        athlete_id, api_key, query, limit, endpoint="search-full", full=True
    )


async def _search_activities(
    athlete_id: str | None,
    api_key: str | None,
    query: str,
    limit: int,
    endpoint: str,
    full: bool,
) -> str:
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities/{endpoint}",
        api_key=api_key,
        params={"q": query, "limit": limit},
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error searching activities: {result.get('message')}"
    hits = result if isinstance(result, list) else []
    if not hits:
        return f"No matches for {query!r}.\n"
    lines = [f"Activity search results ({len(hits)}):", ""]
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        if full:
            lines.append(format_activity_summary(hit).strip())
            lines.append("")
        else:
            lines.append(format_activity_search_hit(hit))
    return "\n".join(lines)


@mcp.tool()
async def interval_search_activities(
    min_secs: int,
    max_secs: int,
    min_intensity: int,
    max_intensity: int,
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sport_type: str | None = None,
) -> str:
    """Find activities containing intervals matching duration + intensity bounds.

    Args:
        min_secs: Minimum interval duration in seconds.
        max_secs: Maximum interval duration in seconds.
        min_intensity: Minimum intensity %.
        max_intensity: Maximum intensity %.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        start_date: Optional YYYY-MM-DD.
        end_date: Optional YYYY-MM-DD.
        sport_type: Optional sport filter (e.g. "Ride", "Run").
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    params: dict[str, Any] = {
        "minSecs": min_secs,
        "maxSecs": max_secs,
        "minIntensity": min_intensity,
        "maxIntensity": max_intensity,
    }
    if start_date is not None:
        params["oldest"] = start_date
    if end_date is not None:
        params["newest"] = end_date
    if sport_type is not None:
        params["type"] = sport_type

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities/interval-search",
        api_key=api_key,
        params=params,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error searching intervals: {result.get('message')}"
    matches = result if isinstance(result, list) else []
    if not matches:
        return "No matching intervals found.\n"
    lines = [f"Matching intervals ({len(matches)}):", ""]
    for match in matches:
        if isinstance(match, dict):
            lines.append(format_interval_match(match))
    return "\n".join(lines)


@mcp.tool()
async def get_activities_around(
    activity_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    route_id: int | None = None,
    limit: int = 30,
) -> str:
    """List activities near another activity, closest first.

    Args:
        activity_id: The activity at the centre (not included in results).
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        route_id: Optional route filter — only return activities on this route.
        limit: Max activities to return (default 30).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg
    params: dict[str, Any] = {"activity_id": activity_id, "limit": limit}
    if route_id is not None:
        params["route_id"] = route_id
    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/activities-around",
        api_key=api_key,
        params=params,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching activities around: {result.get('message')}"
    activities = result if isinstance(result, list) else []
    if not activities:
        return f"No activities found near {activity_id}.\n"
    return _format_activities_response(activities, athlete_id_to_use, include_unnamed=True)
