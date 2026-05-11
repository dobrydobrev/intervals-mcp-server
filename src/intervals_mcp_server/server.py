"""
Intervals.icu MCP Server

This module implements a Model Context Protocol (MCP) server for connecting
Claude with the Intervals.icu API. It provides tools for retrieving and managing
athlete data, including activities, events, workouts, and wellness metrics.

Main Features:
    - Activity retrieval and detailed analysis
    - Event management (races, workouts, calendar items)
    - Wellness data tracking and visualization
    - Error handling with user-friendly messages
    - Configurable parameters with environment variable support

Usage:
    This server is designed to be run as a standalone script and exposes several MCP tools
    for use with Claude Desktop or other MCP-compatible clients. The server loads configuration
    from environment variables (optionally via a .env file) and communicates with the Intervals.icu API.

    To run the server:
        $ python src/intervals_mcp_server/server.py

    MCP tools provided:
        Activities: get_activities, get_activity_details, get_activity_intervals,
            get_activity_streams, get_activity_messages, add_activity_message,
            get_activity_best_efforts, get_activity_power_curve,
            get_activity_hr_curve, get_activity_pace_curve, get_activity_power_vs_hr,
            get_activity_interval_stats, get_activity_weather_summary,
            get_activities_by_ids, search_activities, search_activities_full,
            interval_search_activities, get_activities_around.
        Athlete state: get_athlete, update_athlete, get_athlete_profile,
            get_training_plan, set_training_plan, apply_plan_changes,
            get_fitness_model_events.
        Sport settings: list_sport_settings, get_sport_settings,
            create_sport_settings, update_sport_settings, apply_sport_settings.
        Workout library: list_workouts, get_workout, create_workout,
            update_workout, delete_workout.
        Folders / plans: list_folders, create_folder, update_folder, delete_folder.
        Athlete curves: get_athlete_power_curves, get_athlete_hr_curves,
            get_athlete_pace_curves, get_mmp_model.
        Events: get_events, get_event_by_id, add_or_update_event, delete_event,
            delete_events_by_date_range, bulk_create_events, mark_event_done,
            apply_plan_to_calendar, bulk_delete_events, duplicate_events,
            list_workout_tags, list_event_tags.
        Wellness: get_wellness_data, get_wellness_day, set_wellness_day,
            bulk_update_wellness.
        Custom items: get_custom_items, get_custom_item_by_id, create_custom_item,
            update_custom_item, delete_custom_item.

    See README.md and docs/TOOLS.md for the full reference.
"""

import logging

# Import API client and configuration
from intervals_mcp_server.api.client import (
    httpx_client,  # Re-export for backward compatibility with tests
    make_intervals_request,
)
from intervals_mcp_server.config import get_config
from intervals_mcp_server.mcp_instance import mcp

# Import types and validation
from intervals_mcp_server.server_setup import setup_transport, start_server
from intervals_mcp_server.utils.validation import validate_athlete_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("intervals_icu_mcp_server")

# Get configuration instance
config = get_config()

# Import tool modules to register them (tools register themselves via @mcp.tool() decorators)
# Import tool functions for re-export
from intervals_mcp_server.tools.activities import (  # pylint: disable=wrong-import-position  # noqa: E402
    add_activity_message,
    get_activities,
    get_activities_around,
    get_activities_by_ids,
    get_activity_best_efforts,
    get_activity_details,
    get_activity_hr_curve,
    get_activity_interval_stats,
    get_activity_intervals,
    get_activity_messages,
    get_activity_pace_curve,
    get_activity_power_curve,
    get_activity_power_vs_hr,
    get_activity_streams,
    get_activity_weather_summary,
    interval_search_activities,
    search_activities,
    search_activities_full,
)
from intervals_mcp_server.tools.curves import (  # pylint: disable=wrong-import-position  # noqa: E402
    get_athlete_hr_curves,
    get_athlete_pace_curves,
    get_athlete_power_curves,
    get_mmp_model,
)
from intervals_mcp_server.tools.athlete import (  # pylint: disable=wrong-import-position  # noqa: E402
    apply_plan_changes,
    get_athlete,
    get_athlete_profile,
    get_fitness_model_events,
    get_training_plan,
    set_training_plan,
    update_athlete,
)
from intervals_mcp_server.tools.events import (  # pylint: disable=wrong-import-position  # noqa: E402
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
from intervals_mcp_server.tools.folders import (  # pylint: disable=wrong-import-position  # noqa: E402
    create_folder,
    delete_folder,
    list_folders,
    update_folder,
)
from intervals_mcp_server.tools.sport_settings import (  # pylint: disable=wrong-import-position  # noqa: E402
    apply_sport_settings,
    create_sport_settings,
    get_sport_settings,
    list_sport_settings,
    update_sport_settings,
)
from intervals_mcp_server.tools.wellness import (  # pylint: disable=wrong-import-position  # noqa: E402
    bulk_update_wellness,
    get_wellness_data,
    get_wellness_day,
    set_wellness_day,
)
from intervals_mcp_server.tools.workouts import (  # pylint: disable=wrong-import-position  # noqa: E402
    create_workout,
    delete_workout,
    get_workout,
    list_workouts,
    update_workout,
)
from intervals_mcp_server.tools.custom_items import (  # pylint: disable=wrong-import-position  # noqa: E402
    create_custom_item,
    delete_custom_item,
    get_custom_item_by_id,
    get_custom_items,
    update_custom_item,
)

# Re-export make_intervals_request and httpx_client for backward compatibility
# pylint: disable=duplicate-code  # This __all__ list is intentionally similar to tools/__init__.py
__all__ = [
    "make_intervals_request",
    "httpx_client",  # Re-exported for test compatibility
    "add_activity_message",
    "get_activities",
    "get_activity_details",
    "get_activity_intervals",
    "get_activity_messages",
    "get_activity_streams",
    "get_events",
    "get_event_by_id",
    "delete_event",
    "delete_events_by_date_range",
    "add_or_update_event",
    "get_wellness_data",
    "get_custom_items",
    "get_custom_item_by_id",
    "create_custom_item",
    "update_custom_item",
    "delete_custom_item",
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
    # tools/activities.py additions
    "get_activity_best_efforts",
    "get_activity_power_curve",
    "get_activity_hr_curve",
    "get_activity_pace_curve",
    "get_activity_power_vs_hr",
    "get_activity_interval_stats",
    "get_activity_weather_summary",
    "get_activities_by_ids",
    "search_activities",
    "search_activities_full",
    "interval_search_activities",
    "get_activities_around",
    # tools/wellness.py additions
    "get_wellness_day",
    "set_wellness_day",
    "bulk_update_wellness",
]


# Run the server
if __name__ == "__main__":
    # Validate ATHLETE_ID when server starts (not at import time to allow tests)
    validate_athlete_id(config.athlete_id)

    # Setup transport and start server
    selected_transport = setup_transport()
    start_server(mcp, selected_transport)
