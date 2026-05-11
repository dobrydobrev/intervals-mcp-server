"""
Workout-folder / training-plan MCP tools for Intervals.icu.

Folders organise the workout library into reusable collections; a folder with
``type=PLAN`` is a training plan that can be rolled out onto the athlete's
calendar.
"""

from typing import Any

from intervals_mcp_server.api.client import make_intervals_request
from intervals_mcp_server.config import get_config
from intervals_mcp_server.utils.formatting import format_folder_summary
from intervals_mcp_server.utils.validation import resolve_athlete_id

# Import mcp instance from shared module for tool registration
from intervals_mcp_server.mcp_instance import mcp  # noqa: F401

config = get_config()


@mcp.tool()
async def list_folders(
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """List all the athlete's workout folders and plans.

    Args:
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/folders", api_key=api_key
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error fetching folders: {result.get('message')}"
    folders = result if isinstance(result, list) else []
    return format_folder_summary(folders)


@mcp.tool()
async def create_folder(
    name: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    folder_type: str = "FOLDER",
    description: str | None = None,
    activity_types: list[str] | None = None,
) -> str:
    """Create a new workout folder or training plan.

    Args:
        name: Folder name.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        folder_type: "FOLDER" (default) or "PLAN".
        description: Optional description.
        activity_types: Optional list of sports the folder applies to (e.g. ["Ride", "Run"]).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    payload: dict[str, Any] = {"name": name, "type": folder_type}
    if description is not None:
        payload["description"] = description
    if activity_types is not None:
        payload["activity_types"] = activity_types

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/folders",
        api_key=api_key,
        method="POST",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error creating folder: {result.get('message')}"
    if isinstance(result, dict):
        return f"Folder created: id={result.get('id')} name={result.get('name')!r}"
    return f"Folder {name!r} created for athlete {athlete_id_to_use}."


@mcp.tool()
async def update_folder(
    folder_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
    name: str | None = None,
    description: str | None = None,
    activity_types: list[str] | None = None,
) -> str:
    """Update a workout folder or plan.

    Args:
        folder_id: Folder ID.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
        name: New name (optional).
        description: New description (optional).
        activity_types: New activity types list (optional).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if activity_types is not None:
        payload["activity_types"] = activity_types

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/folders/{folder_id}",
        api_key=api_key,
        method="PUT",
        data=payload,
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error updating folder: {result.get('message')}"
    return f"Folder {folder_id} updated."


@mcp.tool()
async def delete_folder(
    folder_id: str,
    athlete_id: str | None = None,
    api_key: str | None = None,
) -> str:
    """Delete a workout folder or plan (and all workouts inside it).

    Args:
        folder_id: Folder ID.
        athlete_id: Intervals.icu athlete ID (defaults to ATHLETE_ID env var).
        api_key: Intervals.icu API key (defaults to API_KEY env var).
    """
    athlete_id_to_use, error_msg = resolve_athlete_id(athlete_id, config.athlete_id)
    if error_msg:
        return error_msg

    result = await make_intervals_request(
        url=f"/athlete/{athlete_id_to_use}/folders/{folder_id}",
        api_key=api_key,
        method="DELETE",
    )
    if isinstance(result, dict) and "error" in result:
        return f"Error deleting folder: {result.get('message')}"
    return f"Folder {folder_id} deleted."
