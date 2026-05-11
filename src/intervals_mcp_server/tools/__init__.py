"""
MCP tools registry for Intervals.icu MCP Server.

This module registers all available MCP tools with the FastMCP server instance.
"""

from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error

# Import all tools for re-export
# Note: Tools register themselves via @mcp.tool() decorators when imported
from intervals_mcp_server.tools.activities import (  # noqa: F401
    get_activities,
    get_activity_details,
    get_activity_intervals,
    get_activity_streams,
)
from intervals_mcp_server.tools.curves import (  # noqa: F401
    get_athlete_hr_curves,
    get_athlete_pace_curves,
    get_athlete_power_curves,
    get_mmp_model,
)
from intervals_mcp_server.tools.athlete import (  # noqa: F401
    apply_plan_changes,
    get_athlete,
    get_athlete_profile,
    get_fitness_model_events,
    get_training_plan,
    set_training_plan,
    update_athlete,
)
from intervals_mcp_server.tools.events import (  # noqa: F401
    add_or_update_event,
    apply_plan_to_calendar,
    bulk_create_events,
    bulk_delete_events,
    delete_event,
    delete_events_by_date_range,
    duplicate_events,
    get_event_by_id,
    get_events,
    list_event_tags,
    list_workout_tags,
    mark_event_done,
)
from intervals_mcp_server.tools.folders import (  # noqa: F401
    create_folder,
    delete_folder,
    list_folders,
    update_folder,
)
from intervals_mcp_server.tools.sport_settings import (  # noqa: F401
    apply_sport_settings,
    create_sport_settings,
    get_sport_settings,
    list_sport_settings,
    update_sport_settings,
)
from intervals_mcp_server.tools.wellness import get_wellness_data  # noqa: F401
from intervals_mcp_server.tools.workouts import (  # noqa: F401
    create_workout,
    delete_workout,
    get_workout,
    list_workouts,
    update_workout,
)


def register_tools(mcp_instance: FastMCP) -> None:
    """
    Register all MCP tools with the FastMCP server instance.

    This function imports all tool modules, which causes their @mcp.tool()
    decorators to register the tools. The tools need access to the mcp instance,
    so they will be imported after the mcp instance is created.

    Args:
        mcp_instance (FastMCP): The FastMCP server instance to register tools with.
    """
    # Tools are registered via decorators when modules are imported above
    # The mcp_instance parameter is kept for future use if needed
    _ = mcp_instance


__all__ = [
    "register_tools",
    "get_activities",
    "get_activity_details",
    "get_activity_intervals",
    "get_activity_streams",
    "get_events",
    "get_event_by_id",
    "delete_event",
    "delete_events_by_date_range",
    "add_or_update_event",
    "get_wellness_data",
    # tools/athlete.py
    "get_athlete",
    "update_athlete",
    "get_athlete_profile",
    "get_training_plan",
    "set_training_plan",
    "apply_plan_changes",
    "get_fitness_model_events",
    # tools/sport_settings.py
    "list_sport_settings",
    "get_sport_settings",
    "create_sport_settings",
    "update_sport_settings",
    "apply_sport_settings",
    # tools/workouts.py
    "list_workouts",
    "get_workout",
    "create_workout",
    "update_workout",
    "delete_workout",
    # tools/folders.py
    "list_folders",
    "create_folder",
    "update_folder",
    "delete_folder",
    # tools/events.py additions
    "bulk_create_events",
    "mark_event_done",
    "apply_plan_to_calendar",
    "bulk_delete_events",
    "duplicate_events",
    "list_workout_tags",
    "list_event_tags",
    # tools/curves.py
    "get_athlete_power_curves",
    "get_athlete_hr_curves",
    "get_athlete_pace_curves",
    "get_mmp_model",
]
