"""
Athlete-state MCP tools for Intervals.icu.

This module exposes the foundational read/write tools an AI coach needs to
understand the athlete: athlete object, profile, training-plan handle, and the
fitness-model event list.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import (
    format_athlete_profile,
    format_athlete_summary,
    format_fitness_model_events,
    format_training_plan,
)
from intervals_mcp_server.utils.validation import resolve_athlete_id, resolve_date_params

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def get_athlete(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get the athlete record (identity, training fields, sportSettings, custom_items).

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching athlete: {result.get('message')}"
    if not isinstance(result, dict):
        return f"Invalid athlete response for {athlete_id_to_use}."
    return format_athlete_summary(result)


@mcp.tool()
async def update_athlete(
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Update the athlete record (FTP, LTHR, weight, plan, etc.).

    Args:
        payload: Dict matching the Intervals.icu AthleteUpdateDTO shape. Only
            include fields you want to change.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error updating athlete: {result.get('message')}"
    if isinstance(result, dict):
        return "Updated athlete:\n" + format_athlete_summary(result)
    return f"Updated athlete {athlete_id_to_use}."


@mcp.tool()
async def get_athlete_profile(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get the athlete profile (athlete + shared folders + custom items).

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/profile", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching athlete profile: {result.get('message')}"
    if not isinstance(result, dict):
        return f"Invalid profile response for {athlete_id_to_use}."
    return format_athlete_profile(result)


@mcp.tool()
async def get_training_plan(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get the athlete's active training plan.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/training-plan", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching training plan: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No training plan set for athlete {athlete_id_to_use}."
    return format_training_plan(result)


@mcp.tool()
async def set_training_plan(
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Change the athlete's training plan.

    Args:
        payload: Dict matching the Intervals.icu AthleteTrainingPlanUpdate shape
            (e.g. {"training_plan_id": 123, "training_plan_start_date": "2026-01-01"}).
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/training-plan",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error setting training plan: {result.get('message')}"
    if isinstance(result, dict):
        return "Training plan updated:\n" + format_training_plan(result)
    return f"Training plan updated for athlete {athlete_id_to_use}."


@mcp.tool()
async def apply_plan_changes(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Apply any pending changes from the athlete's current plan template to their calendar.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/apply-plan-changes",
        api_key=api_key,
        method="PUT",
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error applying plan changes: {result.get('message')}"
    return f"Plan changes applied to calendar for athlete {athlete_id_to_use}."


@mcp.tool()
async def get_fitness_model_events(
    athlete_id: str | None = None,
    api_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """List events that influence the athlete's fitness calculation in date order.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        start_date: Optional YYYY-MM-DD; defaults to 30 days ago.
        end_date: Optional YYYY-MM-DD; defaults to today.
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    start, end = resolve_date_params(start_date, end_date)
    params = {"oldest": start, "newest": end}

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/fitness-model-events",
        api_key=api_key,
        params=params,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching fitness-model events: {result.get('message')}"
    events = result if isinstance(result, list) else []
    return format_fitness_model_events(events)
