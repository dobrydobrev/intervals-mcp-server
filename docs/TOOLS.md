# Intervals.icu MCP Server — Tool Reference

This is the complete list of MCP tools exposed by the server, grouped by source
module. For setup, see [`README.md`](../README.md); for architecture and
conventions, see [`CLAUDE.md`](../CLAUDE.md).

All tools share a common shape: `athlete_id` and `api_key` are optional and
fall back to the `ATHLETE_ID` / `API_KEY` env vars; date params accept
`YYYY-MM-DD`; PUT/POST bodies use a generic `payload: dict` (the LLM
constructs the JSON) except where the body is small and stable (folders).
All tools return human-formatted strings, not JSON.

## Athlete state — `tools/athlete.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_athlete` | GET `/athlete/{id}` | Identity + training fields + sportSettings. |
| `update_athlete` | PUT `/athlete/{id}` | Update FTP, LTHR, weight, plan, etc. |
| `get_athlete_profile` | GET `/athlete/{id}/profile` | Athlete + shared folders + custom items. |
| `get_training_plan` | GET `/athlete/{id}/training-plan` | Active plan handle. |
| `set_training_plan` | PUT `/athlete/{id}/training-plan` | Change the plan. |
| `apply_plan_changes` | PUT `/athlete/{id}/apply-plan-changes` | Push plan template edits onto the calendar. |
| `get_fitness_model_events` | GET `/athlete/{id}/fitness-model-events` | Events that drive CTL/ATL/TSB. |

## Sport settings — `tools/sport_settings.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `list_sport_settings` | GET `/athlete/{id}/sport-settings` | One record per sport. |
| `get_sport_settings` | GET `/athlete/{id}/sport-settings/{id}` | Full FTP/LTHR/zones for one sport. |
| `create_sport_settings` | POST `/athlete/{id}/sport-settings` | New sport entry. |
| `update_sport_settings` | PUT `/athlete/{id}/sport-settings/{id}` | Update FTP/LTHR/zones. |
| `apply_sport_settings` | PUT `/athlete/{id}/sport-settings/{id}/apply` | Recompute historical zones. |

## Workout library — `tools/workouts.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `list_workouts` | GET `/athlete/{id}/workouts` | The coach's playbook. |
| `get_workout` | GET `/athlete/{id}/workouts/{workoutId}` | One workout. |
| `create_workout` | POST `/athlete/{id}/workouts` | New library workout (uses `WorkoutDoc` step DSL — same as `add_or_update_event`). |
| `update_workout` | PUT `/athlete/{id}/workouts/{workoutId}` | Edit workout. |
| `delete_workout` | DELETE `/athlete/{id}/workouts/{workoutId}` | Remove from library. |

## Folders / plans — `tools/folders.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `list_folders` | GET `/athlete/{id}/folders` | All folders + plans. |
| `create_folder` | POST `/athlete/{id}/folders` | New folder (`folder_type="FOLDER"`) or plan (`folder_type="PLAN"`). |
| `update_folder` | PUT `/athlete/{id}/folders/{folderId}` | Rename / re-scope. |
| `delete_folder` | DELETE `/athlete/{id}/folders/{folderId}` | Delete (including all workouts inside). |

## Events / calendar — `tools/events.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_events` | GET `/athlete/{id}/events` | Range list. |
| `get_event_by_id` | GET `/athlete/{id}/events/{eventId}` | One event. |
| `add_or_update_event` | POST/PUT `/athlete/{id}/events[/{eventId}]` | Create or update one event. |
| `delete_event` | DELETE `/athlete/{id}/events/{eventId}` | Delete one event. |
| `delete_events_by_date_range` | DELETE `/athlete/{id}/events` | Native range delete (defaults `category=WORKOUT`). |
| `bulk_create_events` | POST `/athlete/{id}/events/bulk` | Schedule a full week in one call. |
| `bulk_delete_events` | PUT `/athlete/{id}/events/bulk-delete` | Delete a list of event ids. |
| `duplicate_events` | POST `/athlete/{id}/duplicate-events` | Copy events to a target date. |
| `mark_event_done` | POST `/athlete/{id}/events/{eventId}/mark-done` | Create a manual activity matching the plan. |
| `apply_plan_to_calendar` | POST `/athlete/{id}/events/apply-plan` | Stamp a saved plan. |
| `list_workout_tags` | GET `/athlete/{id}/workout-tags` | Workout-tag vocabulary. |
| `list_event_tags` | GET `/athlete/{id}/event-tags` | Event-tag vocabulary. |

## Activities — `tools/activities.py`

### Reads & messages

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_activities` | GET `/athlete/{id}/activities` | Range list with named-only filter and auto-extend. |
| `get_activity_details` | GET `/activity/{id}` | Full record. |
| `get_activity_intervals` | GET `/activity/{id}/intervals` | Interval breakdown. |
| `get_activity_streams` | GET `/activity/{id}/streams.json` | Per-sample streams. |
| `get_activity_messages` | GET `/activity/{id}/messages` | List comments. |
| `add_activity_message` | POST `/activity/{id}/messages` | Post a comment. |

### Performance analysis (curves take `summary_only=True` by default)

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_activity_best_efforts` | GET `/activity/{id}/best-efforts` | Duration + average for each effort. |
| `get_activity_power_curve` | GET `/activity/{id}/power-curve.json` | Per-activity power curve. |
| `get_activity_hr_curve` | GET `/activity/{id}/hr-curve.json` | Per-activity HR curve. |
| `get_activity_pace_curve` | GET `/activity/{id}/pace-curve.json` | Per-activity pace curve (m/s + min/km). |
| `get_activity_power_vs_hr` | GET `/activity/{id}/power-vs-hr.json` | Decoupling / efficiency. |
| `get_activity_interval_stats` | GET `/activity/{id}/interval-stats` | Stats over a `[start_secs, end_secs]` slice. |
| `get_activity_weather_summary` | GET `/activity/{id}/weather-summary` | Temp / wind / humidity / precip. |

### Search / lookup

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_activities_by_ids` | GET `/athlete/{id}/activities/{ids}` | Bulk fetch by comma-separated id list. |
| `search_activities` | GET `/athlete/{id}/activities/search` | Name search (or `#tag` for exact tag). |
| `search_activities_full` | GET `/athlete/{id}/activities/search-full` | Same query, full activity payloads. |
| `interval_search_activities` | GET `/athlete/{id}/activities/interval-search` | Find sessions with intervals matching duration + intensity. |
| `get_activities_around` | GET `/athlete/{id}/activities-around` | Activities near another activity, closest first. |

## Athlete-level performance curves — `tools/curves.py`

All curve tools default to `summary_only=True` (coach-canonical buckets); pass
`summary_only=False` to get the full `secs[]` / `values[]` arrays.

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_athlete_power_curves` | GET `/athlete/{id}/power-curves.json` | Best power over the range, per sport. |
| `get_athlete_hr_curves` | GET `/athlete/{id}/hr-curves.json` | Best HR over the range. |
| `get_athlete_pace_curves` | GET `/athlete/{id}/pace-curves.json` | Best pace over the range (m/s + min/km). |
| `get_mmp_model` | GET `/athlete/{id}/mmp-model` | CP / W' / Pmax model used by `%MMP` steps. |

## Wellness — `tools/wellness.py`

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_wellness_data` | GET `/athlete/{id}/wellness` | Date-range read. |
| `get_wellness_day` | GET `/athlete/{id}/wellness/{date}` | Single-day read. |
| `set_wellness_day` | PUT `/athlete/{id}/wellness/{date}` | Log/update one day (sleep, HRV, soreness, etc.). |
| `bulk_update_wellness` | PUT `/athlete/{id}/wellness-bulk` | Update many days at once. |

## Custom items — `tools/custom_items.py`

Athlete-scoped custom fields and charts. Useful for coach-side state storage
(notes attached to the athlete that the LLM can write and read later).

| Tool | Endpoint | Purpose |
|---|---|---|
| `get_custom_items` | GET `/athlete/{id}/custom-item` | List items. |
| `get_custom_item_by_id` | GET `/athlete/{id}/custom-item/{itemId}` | Read one. |
| `create_custom_item` | POST `/athlete/{id}/custom-item` | Create. |
| `update_custom_item` | PUT `/athlete/{id}/custom-item/{itemId}` | Update. |
| `delete_custom_item` | DELETE `/athlete/{id}/custom-item/{itemId}` | Delete. |

## Bucket reference

Coach-canonical durations used by `summary_only=True` (defined in
`utils/formatting.py`):

- Power: 1s, 5s, 15s, 30s, 1m, 2m, 5m, 10m, 20m, 60m
- HR: 5s, 30s, 1m, 5m, 20m, 60m
- Pace: 15s, 1m, 5m, 20m, 60m

The formatter picks the nearest entry in the response's `secs[]` array for
each bucket — it does not interpolate. Pass `summary_only=False` to get every
returned data point as a compact list.
