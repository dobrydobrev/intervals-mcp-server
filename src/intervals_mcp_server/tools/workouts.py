"""
Workout-library MCP tools for Intervals.icu.

These are the coach's reusable building blocks — the workouts stored in the
athlete's library (separate from calendar events). CRUD over
``/athlete/{id}/workouts``.

For ``payload`` on create/update see the same DSL documented on
``add_or_update_event``: a Workout has ``name``, ``description``, ``type``,
``moving_time``, ``distance``, and a ``workout_doc`` containing ``steps``.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_workout
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def list_workouts(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """List all the workouts in the athlete's library.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/workouts", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching workouts: {result.get('message')}"
    workouts = result if isinstance(result, list) else []
    if not workouts:
        return f"No workouts in library for athlete {athlete_id_to_use}.\n"
    lines = [f"Workouts ({len(workouts)}):", ""]
    for workout in workouts:
        if isinstance(workout, dict):
            lines.append(format_workout(workout).strip())
            lines.append("")
    return "\n".join(lines)


@mcp.tool()
async def get_workout(
    workout_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Get a single workout from the athlete's library.

    Args:
        workout_id: Intervals.icu workout ID.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/workouts/{workout_id}", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching workout: {result.get('message')}"
    if not isinstance(result, dict):
        return f"No workout found for id {workout_id}."
    return format_workout(result)


@mcp.tool()
async def create_workout(
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Create a new workout in the athlete's library.

    Args:
        payload: Workout dict — must include ``folder_id`` and at minimum
            ``name``, ``type``, and a ``workout_doc`` with ``steps``. Step
            grammar is identical to ``add_or_update_event``'s ``workout_doc``.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/workouts",
        api_key=api_key,
        method="POST",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error creating workout: {result.get('message')}"
    if isinstance(result, dict):
        return "Workout created:\n" + format_workout(result)
    return f"Workout created for athlete {athlete_id_to_use}."


@mcp.tool()
async def update_workout(
    workout_id: str,
    payload: dict[str, Any],
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Update an existing workout in the athlete's library.

    Args:
        workout_id: Intervals.icu workout ID.
        payload: Partial workout dict — only fields you set are updated.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/workouts/{workout_id}",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error updating workout: {result.get('message')}"
    if isinstance(result, dict):
        return "Workout updated:\n" + format_workout(result)
    return f"Workout {workout_id} updated."


@mcp.tool()
async def delete_workout(
    workout_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Delete a workout from the athlete's library.

    Args:
        workout_id: Intervals.icu workout ID.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/workouts/{workout_id}",
        api_key=api_key,
        method="DELETE",
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error deleting workout: {result.get('message')}"
    return f"Workout {workout_id} deleted."
