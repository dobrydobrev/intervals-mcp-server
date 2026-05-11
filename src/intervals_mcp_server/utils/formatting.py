"""
Formatting utilities for Intervals.icu MCP Server

This module contains formatting functions for handling data from the Intervals.icu API.
"""

import json
from datetime import datetime
from typing import Any


class _KeyTracker(dict):
    """A dict wrapper that records which keys are accessed."""

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.accessed: set[str] = set()

    def get(self, key: str, default: Any = None) -> Any:
        self.accessed.add(key)
        return super().get(key, default)

    def __getitem__(self, key: str) -> Any:
        self.accessed.add(key)
        return super().__getitem__(key)

    def __contains__(self, key: object) -> bool:
        self.accessed.add(key)
        return super().__contains__(key)


def format_activity_summary(activity: dict[str, Any]) -> str:
    """Format an activity into a readable string."""
    start_time = activity.get("startTime", activity.get("start_date", "Unknown"))

    if isinstance(start_time, str) and len(start_time) > 10:
        # Format datetime if it's a full ISO string
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    rpe = activity.get("perceived_exertion", None)
    if rpe is None:
        rpe = activity.get("icu_rpe", "N/A")
    if isinstance(rpe, (int, float)):
        rpe = f"{rpe}/10"

    feel = activity.get("feel", "N/A")
    if isinstance(feel, int):
        feel = f"{feel}/5"

    return f"""
Activity: {activity.get("name", "Unnamed")}
ID: {activity.get("id", "N/A")}
Type: {activity.get("type", "Unknown")}
Date: {start_time}
Description: {activity.get("description", "N/A")}
Distance: {activity.get("distance", 0)} meters
Duration: {activity.get("duration", activity.get("elapsed_time", 0))} seconds
Moving Time: {activity.get("moving_time", "N/A")} seconds
Elevation Gain: {activity.get("elevationGain", activity.get("total_elevation_gain", 0))} meters
Elevation Loss: {activity.get("total_elevation_loss", "N/A")} meters

Power Data:
Average Power: {activity.get("avgPower", activity.get("icu_average_watts", activity.get("average_watts", "N/A")))} watts
Weighted Avg Power: {activity.get("icu_weighted_avg_watts", "N/A")} watts
Training Load: {activity.get("trainingLoad", activity.get("icu_training_load", "N/A"))}
FTP: {activity.get("icu_ftp", "N/A")} watts
Kilojoules: {activity.get("icu_joules", "N/A")}
Intensity: {activity.get("icu_intensity", "N/A")}
Power:HR Ratio: {activity.get("icu_power_hr", "N/A")}
Variability Index: {activity.get("icu_variability_index", "N/A")}

Heart Rate Data:
Average Heart Rate: {activity.get("avgHr", activity.get("average_heartrate", "N/A"))} bpm
Max Heart Rate: {activity.get("max_heartrate", "N/A")} bpm
LTHR: {activity.get("lthr", "N/A")} bpm
Resting HR: {activity.get("icu_resting_hr", "N/A")} bpm
Decoupling: {activity.get("decoupling", "N/A")}

Other Metrics:
Cadence: {activity.get("average_cadence", "N/A")} rpm
Calories burned: {activity.get("calories", "N/A")} kcal
Average Speed: {activity.get("average_speed", "N/A")} m/s
Max Speed: {activity.get("max_speed", "N/A")} m/s
Average Stride: {activity.get("average_stride", "N/A")}
L/R Balance: {activity.get("avg_lr_balance", "N/A")}
Weight: {activity.get("icu_weight", "N/A")} kg
RPE: {rpe}
Session RPE: {activity.get("session_rpe", "N/A")}
Feel: {feel}

Environment:
Trainer: {activity.get("trainer", "N/A")}
Average Temp: {activity.get("average_temp", "N/A")}°C
Min Temp: {activity.get("min_temp", "N/A")}°C
Max Temp: {activity.get("max_temp", "N/A")}°C
Avg Wind Speed: {activity.get("average_wind_speed", "N/A")} km/h
Headwind %: {activity.get("headwind_percent", "N/A")}%
Tailwind %: {activity.get("tailwind_percent", "N/A")}%

Training Metrics:
Fitness (CTL): {activity.get("icu_ctl", "N/A")}
Fatigue (ATL): {activity.get("icu_atl", "N/A")}
TRIMP: {activity.get("trimp", "N/A")}
Polarization Index: {activity.get("polarization_index", "N/A")}
Power Load: {activity.get("power_load", "N/A")}
HR Load: {activity.get("hr_load", "N/A")}
Pace Load: {activity.get("pace_load", "N/A")}
Efficiency Factor: {activity.get("icu_efficiency_factor", "N/A")}

Device Info:
Device: {activity.get("device_name", "N/A")}
Power Meter: {activity.get("power_meter", "N/A")}
File Type: {activity.get("file_type", "N/A")}
"""


def format_workout(workout: dict[str, Any]) -> str:
    """Format a workout into a readable string.

    Tolerates both the hand-curated test shape (``sport``, ``duration``, ``tss``,
    ``intervals``) and the Intervals.icu API shape (``type``, ``moving_time``,
    ``icu_training_load``, ``workout_doc``).
    """
    sport = workout.get("sport") or workout.get("type") or "Unknown"
    duration = workout.get("duration") or workout.get("moving_time") or 0
    load = workout.get("tss")
    if load is None:
        load = workout.get("icu_training_load", "N/A")
    intervals: Any = workout.get("intervals")
    if intervals is None:
        doc = workout.get("workout_doc") or {}
        if isinstance(doc, dict):
            intervals = doc.get("steps") or []
        else:
            intervals = []
    step_count = len(intervals) if isinstance(intervals, list) else 0
    return f"""
Workout: {workout.get("name", "Unnamed")}
ID: {workout.get("id", "N/A")}
Description: {workout.get("description", "No description")}
Sport: {sport}
Duration: {duration} seconds
TSS: {load}
Intervals: {step_count}
"""


def _format_training_metrics(entries: dict[str, Any]) -> list[str]:
    """Format training metrics section."""
    training_metrics = []
    for k, label in [
        ("ctl", "Fitness (CTL)"),
        ("atl", "Fatigue (ATL)"),
        ("rampRate", "Ramp Rate"),
        ("ctlLoad", "CTL Load"),
        ("atlLoad", "ATL Load"),
    ]:
        if entries.get(k) is not None:
            training_metrics.append(f"- {label}: {entries[k]}")
    return training_metrics


def _format_sport_info(entries: dict[str, Any]) -> list[str]:
    """Format sport-specific info section."""
    sport_info_list = []
    if entries.get("sportInfo"):
        for sport in entries.get("sportInfo", []):
            if isinstance(sport, dict) and sport.get("eftp") is not None:
                sport_info_list.append(f"- {sport.get('type')}: eFTP = {sport['eftp']}")
    return sport_info_list


def _format_vital_signs(entries: dict[str, Any]) -> list[str]:
    """Format vital signs section."""
    vital_signs = []
    for k, label, unit in [
        ("weight", "Weight", "kg"),
        ("restingHR", "Resting HR", "bpm"),
        ("hrv", "HRV", ""),
        ("hrvSDNN", "HRV SDNN", ""),
        ("avgSleepingHR", "Average Sleeping HR", "bpm"),
        ("spO2", "SpO2", "%"),
        ("systolic", "Systolic BP", ""),
        ("diastolic", "Diastolic BP", ""),
        ("respiration", "Respiration", "breaths/min"),
        ("bloodGlucose", "Blood Glucose", "mmol/L"),
        ("lactate", "Lactate", "mmol/L"),
        ("vo2max", "VO2 Max", "ml/kg/min"),
        ("bodyFat", "Body Fat", "%"),
        ("abdomen", "Abdomen", "cm"),
        ("baevskySI", "Baevsky Stress Index", ""),
    ]:
        if entries.get(k) is not None:
            value = entries[k]
            if k == "systolic" and entries.get("diastolic") is not None:
                vital_signs.append(
                    f"- Blood Pressure: {entries['systolic']}/{entries['diastolic']} mmHg"
                )
            elif k not in ("systolic", "diastolic"):
                vital_signs.append(f"- {label}: {value}{(' ' + unit) if unit else ''}")
    return vital_signs


def _format_sleep_recovery(entries: dict[str, Any]) -> list[str]:
    """Format sleep and recovery section."""
    sleep_lines = []
    sleep_hours = None
    if entries.get("sleepSecs") is not None:
        sleep_hours = f"{entries['sleepSecs'] / 3600:.2f}"
    elif entries.get("sleepHours") is not None:
        sleep_hours = f"{entries['sleepHours']}"
    if sleep_hours is not None:
        sleep_lines.append(f"  Sleep: {sleep_hours} hours")

    if entries.get("sleepQuality") is not None:
        quality_value = entries["sleepQuality"]
        quality_labels = {1: "Great", 2: "Good", 3: "Average", 4: "Poor"}
        quality_text = quality_labels.get(quality_value, str(quality_value))
        sleep_lines.append(f"  Sleep Quality: {quality_value} ({quality_text})")

    if entries.get("sleepScore") is not None:
        sleep_lines.append(f"  Device Sleep Score: {entries['sleepScore']}/100")

    if entries.get("readiness") is not None:
        sleep_lines.append(f"  Readiness: {entries['readiness']}/10")

    return sleep_lines


def _format_menstrual_tracking(entries: dict[str, Any]) -> list[str]:
    """Format menstrual tracking section."""
    menstrual_lines = []
    if entries.get("menstrualPhase") is not None:
        menstrual_lines.append(f"  Menstrual Phase: {str(entries['menstrualPhase']).capitalize()}")
    if entries.get("menstrualPhasePredicted") is not None:
        menstrual_lines.append(
            f"  Predicted Phase: {str(entries['menstrualPhasePredicted']).capitalize()}"
        )
    return menstrual_lines


def _format_subjective_feelings(entries: dict[str, Any]) -> list[str]:
    """Format subjective feelings section."""
    subjective_lines = []
    for k, label in [
        ("soreness", "Soreness"),
        ("fatigue", "Fatigue"),
        ("stress", "Stress"),
        ("mood", "Mood"),
        ("motivation", "Motivation"),
        ("injury", "Injury Level"),
    ]:
        if entries.get(k) is not None:
            subjective_lines.append(f"  {label}: {entries[k]}/10")
    return subjective_lines


def _format_nutrition_hydration(entries: dict[str, Any]) -> list[str]:
    """Format nutrition and hydration section.

    Handles both legacy fields (kcalConsumed, hydrationVolume) and the native
    macro fields from the Intervals.icu API (carbohydrates, protein,
    fatTotal). All fields are rendered conditionally — a null/missing value
    hides the corresponding line for backward compatibility with older
    wellness records.
    """
    nutrition_lines = []
    for k, label, unit in [
        ("kcalConsumed", "Calories Consumed", ""),
        ("carbohydrates", "Carbohydrates", "g"),
        ("protein", "Protein", "g"),
        ("fatTotal", "Fat", "g"),
        ("hydrationVolume", "Hydration Volume", ""),
    ]:
        if entries.get(k) is not None:
            suffix = f" {unit}" if unit else ""
            nutrition_lines.append(f"- {label}: {entries[k]}{suffix}")

    if entries.get("hydration") is not None:
        nutrition_lines.append(f"  Hydration Score: {entries['hydration']}/10")

    return nutrition_lines


def _format_other_fields(entries: dict[str, Any], known_keys: set[str]) -> list[str]:
    """Format any fields not already handled by the standard formatting sections."""
    other_lines = []
    for key, value in entries.items():
        if key not in known_keys and value is not None:
            if isinstance(value, (dict, list)):
                other_lines.append(f"- {key}: {json.dumps(value)}")
            else:
                other_lines.append(f"- {key}: {value}")
    return other_lines


def format_wellness_entry(entries: dict[str, Any], include_all_fields: bool = False) -> str:
    """Format wellness entry data into a readable string.

    Formats various wellness metrics including training metrics, vital signs,
    sleep data, menstrual tracking, subjective feelings, nutrition, and activity.

    Args:
        entries: Dictionary containing wellness data fields such as:
            - Training metrics: ctl, atl, rampRate, ctlLoad, atlLoad
            - Vital signs: weight, restingHR, hrv, hrvSDNN, avgSleepingHR, spO2,
              systolic, diastolic, respiration, bloodGlucose, lactate, vo2max,
              bodyFat, abdomen, baevskySI
            - Sleep: sleepSecs, sleepHours, sleepQuality, sleepScore, readiness
            - Menstrual: menstrualPhase, menstrualPhasePredicted
            - Subjective: soreness, fatigue, stress, mood, motivation, injury
            - Nutrition: kcalConsumed, carbohydrates, protein, fatTotal, hydrationVolume, hydration
            - Activity: steps
            - Other: comments, locked, date
        include_all_fields: If True, any fields not covered by the standard
            sections are appended under an "Other Fields" heading (default False).

    Returns:
        A formatted string representation of the wellness entry.
    """
    if include_all_fields:
        entries = _KeyTracker(entries)
        # Mark metadata/internal keys so they don't appear in "Other Fields"
        entries.get("date")
        entries.get("updated")
        entries.get("tempWeight")
        entries.get("tempRestingHR")

    lines = ["Wellness Data:"]
    lines.append(f"Date: {entries.get('id', 'N/A')}")
    lines.append("")

    training_metrics = _format_training_metrics(entries)
    if training_metrics:
        lines.append("Training Metrics:")
        lines.extend(training_metrics)
        lines.append("")

    sport_info_list = _format_sport_info(entries)
    if sport_info_list:
        lines.append("Sport-Specific Info:")
        lines.extend(sport_info_list)
        lines.append("")

    vital_signs = _format_vital_signs(entries)
    if vital_signs:
        lines.append("Vital Signs:")
        lines.extend(vital_signs)
        lines.append("")

    sleep_lines = _format_sleep_recovery(entries)
    if sleep_lines:
        lines.append("Sleep & Recovery:")
        lines.extend(sleep_lines)
        lines.append("")

    menstrual_lines = _format_menstrual_tracking(entries)
    if menstrual_lines:
        lines.append("Menstrual Tracking:")
        lines.extend(menstrual_lines)
        lines.append("")

    subjective_lines = _format_subjective_feelings(entries)
    if subjective_lines:
        lines.append("Subjective Feelings:")
        lines.extend(subjective_lines)
        lines.append("")

    nutrition_lines = _format_nutrition_hydration(entries)
    if nutrition_lines:
        lines.append("Nutrition & Hydration:")
        lines.extend(nutrition_lines)
        lines.append("")

    if entries.get("steps") is not None:
        lines.append("Activity:")
        lines.append(f"- Steps: {entries['steps']}")
        lines.append("")

    if entries.get("comments"):
        lines.append(f"Comments: {entries['comments']}")
    if "locked" in entries:
        lines.append(f"Status: {'Locked' if entries.get('locked') else 'Unlocked'}")

    if include_all_fields:
        other_lines = _format_other_fields(entries, entries.accessed)
        if other_lines:
            lines.append("")
            lines.append("Other Fields:")
            lines.extend(other_lines)

    return "\n".join(lines)


def format_event_summary(event: dict[str, Any]) -> str:
    """Format a basic event summary into a readable string."""

    # Update to check for "date" if "start_date_local" is not provided
    event_date = event.get("start_date_local", event.get("date", "Unknown"))
    event_type = "Workout" if event.get("workout") else "Race" if event.get("race") else "Other"
    event_name = event.get("name", "Unnamed")
    event_id = event.get("id", "N/A")
    event_desc = event.get("description", "No description")

    return f"""Date: {event_date}
ID: {event_id}
Type: {event_type}
Name: {event_name}
Description: {event_desc}"""


def format_event_details(event: dict[str, Any]) -> str:
    """Format detailed event information into a readable string."""

    event_details = f"""Event Details:

ID: {event.get("id", "N/A")}
Date: {event.get("date", "Unknown")}
Name: {event.get("name", "Unnamed")}
Description: {event.get("description", "No description")}"""

    # Check if it's a workout-based event
    if "workout" in event and event["workout"]:
        workout = event["workout"]
        event_details += f"""

Workout Information:
Workout ID: {workout.get("id", "N/A")}
Sport: {workout.get("sport", "Unknown")}
Duration: {workout.get("duration", 0)} seconds
TSS: {workout.get("tss", "N/A")}"""

        # Include interval count if available
        if "intervals" in workout and isinstance(workout["intervals"], list):
            event_details += f"""
Intervals: {len(workout["intervals"])}"""

    # Check if it's a race
    if event.get("race"):
        event_details += f"""

Race Information:
Priority: {event.get("priority", "N/A")}
Result: {event.get("result", "N/A")}"""

    # Include calendar information
    if "calendar" in event:
        cal = event["calendar"]
        event_details += f"""

Calendar: {cal.get("name", "N/A")}"""

    return event_details


def format_activity_message(message: dict[str, Any]) -> str:
    """Format an activity message/note into a readable string."""
    created = message.get("created", "Unknown")
    if isinstance(created, str) and len(created) > 10:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    return f"""Author: {message.get("name", "Unknown")}
Date: {created}
Type: {message.get("type", "TEXT")}
Content: {message.get("content", "")}"""


def format_custom_item_details(item: dict[str, Any]) -> str:
    """Format detailed custom item information into a readable string."""
    lines = ["Custom Item Details:", ""]
    lines.append(f"ID: {item.get('id', 'N/A')}")
    lines.append(f"Name: {item.get('name', 'N/A')}")
    lines.append(f"Type: {item.get('type', 'N/A')}")

    if item.get("description"):
        lines.append(f"Description: {item['description']}")
    if item.get("visibility"):
        lines.append(f"Visibility: {item['visibility']}")
    if item.get("index") is not None:
        lines.append(f"Index: {item['index']}")
    if item.get("hide_script") is not None:
        lines.append(f"Hide Script: {item['hide_script']}")
    if item.get("content"):
        lines.append(f"Content: {json.dumps(item['content'], indent=2)}")

    return "\n".join(lines)


def format_intervals(intervals_data: dict[str, Any]) -> str:
    """Format intervals data into a readable string with all available fields.

    Args:
        intervals_data: The intervals data from the Intervals.icu API

    Returns:
        A formatted string representation of the intervals data
    """
    # Format basic intervals information
    result = f"""Intervals Analysis:

ID: {intervals_data.get("id", "N/A")}
Analyzed: {intervals_data.get("analyzed", "N/A")}

"""

    # Format individual intervals
    if "icu_intervals" in intervals_data and intervals_data["icu_intervals"]:
        result += "Individual Intervals:\n\n"

        for i, interval in enumerate(intervals_data["icu_intervals"], 1):
            result += f"""[{i}] {interval.get("label", f"Interval {i}")} ({interval.get("type", "Unknown")})
Duration: {interval.get("elapsed_time", 0)} seconds (moving: {interval.get("moving_time", 0)} seconds)
Distance: {interval.get("distance", 0)} meters
Start-End Indices: {interval.get("start_index", 0)}-{interval.get("end_index", 0)}

Power Metrics:
  Average Power: {interval.get("average_watts", 0)} watts ({interval.get("average_watts_kg", 0)} W/kg)
  Max Power: {interval.get("max_watts", 0)} watts ({interval.get("max_watts_kg", 0)} W/kg)
  Weighted Avg Power: {interval.get("weighted_average_watts", 0)} watts
  Intensity: {interval.get("intensity", 0)}
  Training Load: {interval.get("training_load", 0)}
  Joules: {interval.get("joules", 0)}
  Joules > FTP: {interval.get("joules_above_ftp", 0)}
  Power Zone: {interval.get("zone", "N/A")} ({interval.get("zone_min_watts", 0)}-{interval.get("zone_max_watts", 0)} watts)
  W' Balance: Start {interval.get("wbal_start", 0)}, End {interval.get("wbal_end", 0)}
  L/R Balance: {interval.get("avg_lr_balance", 0)}
  Variability: {interval.get("w5s_variability", 0)}
  Torque: Avg {interval.get("average_torque", 0)}, Min {interval.get("min_torque", 0)}, Max {interval.get("max_torque", 0)}

Heart Rate & Metabolic:
  Heart Rate: Avg {interval.get("average_heartrate", 0)}, Min {interval.get("min_heartrate", 0)}, Max {interval.get("max_heartrate", 0)} bpm
  Decoupling: {interval.get("decoupling", 0)}
  DFA α1: {interval.get("average_dfa_a1", 0)}
  Respiration: {interval.get("average_respiration", 0)} breaths/min
  EPOC: {interval.get("average_epoc", 0)}
  SmO2: {interval.get("average_smo2", 0)}% / {interval.get("average_smo2_2", 0)}%
  THb: {interval.get("average_thb", 0)} / {interval.get("average_thb_2", 0)}

Speed & Cadence:
  Speed: Avg {interval.get("average_speed", 0)}, Min {interval.get("min_speed", 0)}, Max {interval.get("max_speed", 0)} m/s
  GAP: {interval.get("gap", 0)} m/s
  Cadence: Avg {interval.get("average_cadence", 0)}, Min {interval.get("min_cadence", 0)}, Max {interval.get("max_cadence", 0)} rpm
  Stride: {interval.get("average_stride", 0)}

Elevation & Environment:
  Elevation Gain: {interval.get("total_elevation_gain", 0)} meters
  Altitude: Min {interval.get("min_altitude", 0)}, Max {interval.get("max_altitude", 0)} meters
  Gradient: {interval.get("average_gradient", 0)}%
  Temperature: {interval.get("average_temp", 0)}°C (Weather: {interval.get("average_weather_temp", 0)}°C, Feels like: {interval.get("average_feels_like", 0)}°C)
  Wind: Speed {interval.get("average_wind_speed", 0)} km/h, Gust {interval.get("average_wind_gust", 0)} km/h, Direction {interval.get("prevailing_wind_deg", 0)}°
  Headwind: {interval.get("headwind_percent", 0)}%, Tailwind: {interval.get("tailwind_percent", 0)}%

"""

    # Format interval groups
    if "icu_groups" in intervals_data and intervals_data["icu_groups"]:
        result += "Interval Groups:\n\n"

        for i, group in enumerate(intervals_data["icu_groups"], 1):
            result += f"""Group: {group.get("id", f"Group {i}")} (Contains {group.get("count", 0)} intervals)
Duration: {group.get("elapsed_time", 0)} seconds (moving: {group.get("moving_time", 0)} seconds)
Distance: {group.get("distance", 0)} meters
Start-End Indices: {group.get("start_index", 0)}-N/A

Power: Avg {group.get("average_watts", 0)} watts ({group.get("average_watts_kg", 0)} W/kg), Max {group.get("max_watts", 0)} watts
W. Avg Power: {group.get("weighted_average_watts", 0)} watts, Intensity: {group.get("intensity", 0)}
Heart Rate: Avg {group.get("average_heartrate", 0)}, Max {group.get("max_heartrate", 0)} bpm
Speed: Avg {group.get("average_speed", 0)}, Max {group.get("max_speed", 0)} m/s
Cadence: Avg {group.get("average_cadence", 0)}, Max {group.get("max_cadence", 0)} rpm

"""

    return result


def _opt(value: Any, suffix: str = "") -> str:
    """Render an optional scalar with a trailing unit suffix, or 'N/A'."""
    if value is None or value == "":
        return "N/A"
    return f"{value}{suffix}"


def format_athlete_summary(athlete: dict[str, Any]) -> str:
    """Format core athlete identity + training-relevant fields."""
    name = athlete.get("name") or " ".join(
        filter(None, [athlete.get("firstname"), athlete.get("lastname")])
    ) or "Unknown"
    weight = athlete.get("icu_weight") or athlete.get("weight")
    types = athlete.get("icu_type_settings") or []
    sport_names: set[str] = set()
    for entry in types:
        if isinstance(entry, dict):
            sport = entry.get("type")
            if isinstance(sport, str) and sport:
                sport_names.add(sport)
    sports = ", ".join(sorted(sport_names)) or "N/A"

    return f"""Athlete: {name}
ID: {_opt(athlete.get("id"))}
Sex: {_opt(athlete.get("sex"))}
Weight: {_opt(weight, " kg")}
Height: {_opt(athlete.get("height"), " m")}
Resting HR: {_opt(athlete.get("icu_resting_hr"), " bpm")}
Timezone: {_opt(athlete.get("timezone"))}
Country: {_opt(athlete.get("country"))}
Training plan: {_opt(athlete.get("training_plan_id"))}
Plan start: {_opt(athlete.get("training_plan_start_date"))}
Configured sports: {sports}
Bio: {_opt(athlete.get("bio"))}
"""


def format_athlete_profile(profile: dict[str, Any]) -> str:
    """Format the GET /athlete/{id}/profile response.

    Profile contains the athlete object plus shared folders and custom items.
    """
    athlete = profile.get("athlete") or {}
    shared_folders = profile.get("sharedFolders") or []
    custom_items = profile.get("customItems") or []

    lines = ["Athlete Profile:", "", format_athlete_summary(athlete).rstrip(), ""]
    lines.append(f"Shared folders ({len(shared_folders)}):")
    for folder in shared_folders[:20]:
        if isinstance(folder, dict):
            lines.append(f"  - {folder.get('name', 'Unnamed')} (id={folder.get('id')})")
    lines.append("")
    lines.append(f"Custom items ({len(custom_items)}):")
    for item in custom_items[:20]:
        if isinstance(item, dict):
            lines.append(f"  - {item.get('name', 'Unnamed')} (id={item.get('id')})")
    return "\n".join(lines) + "\n"


def format_training_plan(plan: dict[str, Any]) -> str:
    """Format an AthleteTrainingPlan record."""
    folder = plan.get("training_plan") or {}
    folder_name = folder.get("name") if isinstance(folder, dict) else None
    return f"""Training Plan:
Plan id: {_opt(plan.get("training_plan_id"))}
Alias: {_opt(plan.get("training_plan_alias"))}
Folder: {_opt(folder_name)}
Athlete: {_opt(plan.get("athlete_id"))}
Start date: {_opt(plan.get("training_plan_start_date"))}
Last applied: {_opt(plan.get("training_plan_last_applied"))}
Timezone: {_opt(plan.get("timezone"))}
"""


def format_fitness_model_events(events: list[dict[str, Any]]) -> str:
    """Format the list of fitness-model events (chronological)."""
    if not events:
        return "No fitness-model events in this range.\n"
    lines = [f"Fitness model events ({len(events)}):", ""]
    for event in events:
        if not isinstance(event, dict):
            continue
        date = event.get("start_date_local") or event.get("date") or "?"
        category = event.get("category") or event.get("type") or "?"
        name = event.get("name") or ""
        lines.append(f"- {date}  [{category}]  {name}".rstrip())
    return "\n".join(lines) + "\n"


def format_sport_settings_summary(settings_list: list[dict[str, Any]]) -> str:
    """One-line per sport settings record — id, sport types, FTP/LTHR if present."""
    if not settings_list:
        return "No sport settings configured.\n"
    lines = [f"Sport Settings ({len(settings_list)}):", ""]
    for settings in settings_list:
        if not isinstance(settings, dict):
            continue
        sport_types = settings.get("types") or []
        if isinstance(sport_types, list):
            sport = ", ".join(str(t) for t in sport_types) or "?"
        else:
            sport = str(sport_types)
        lines.append(
            f"- id={settings.get('id', '?')}  sport={sport}  "
            f"FTP={settings.get('ftp', 'N/A')}  LTHR={settings.get('lthr', 'N/A')}  "
            f"MaxHR={settings.get('max_hr', 'N/A')}"
        )
    return "\n".join(lines) + "\n"


def _format_zones(label: str, zones: Any, names: Any, unit: str) -> str:
    """Render zone boundaries with optional names."""
    if not isinstance(zones, list) or not zones:
        return f"{label}: N/A"
    name_list = names if isinstance(names, list) else []
    parts: list[str] = []
    for i, boundary in enumerate(zones):
        name = name_list[i] if i < len(name_list) else f"Z{i + 1}"
        parts.append(f"{name}={boundary}{unit}")
    return f"{label}: " + ", ".join(parts)


def format_sport_settings_details(settings: dict[str, Any]) -> str:
    """Full sport-settings record — zones, thresholds, pace units."""
    sport_types = settings.get("types") or []
    if isinstance(sport_types, list):
        sport = ", ".join(str(t) for t in sport_types) or "Unknown"
    else:
        sport = str(sport_types)

    lines = [
        f"Sport Settings: {sport}",
        f"ID: {_opt(settings.get('id'))}",
        f"Athlete: {_opt(settings.get('athlete_id'))}",
        f"FTP: {_opt(settings.get('ftp'), 'W')}  (indoor: {_opt(settings.get('indoor_ftp'), 'W')})",
        f"LTHR: {_opt(settings.get('lthr'), ' bpm')}  Max HR: {_opt(settings.get('max_hr'), ' bpm')}",
        f"Threshold pace: {_opt(settings.get('threshold_pace'), ' m/s')}",
        f"Pace units: {_opt(settings.get('pace_units'))}",
        f"W': {_opt(settings.get('w_prime'), ' J')}  Pmax: {_opt(settings.get('p_max'), 'W')}",
        _format_zones("Power zones", settings.get("power_zones"), settings.get("power_zone_names"), "W"),
        _format_zones("HR zones", settings.get("hr_zones"), settings.get("hr_zone_names"), " bpm"),
        _format_zones("Pace zones", settings.get("pace_zones"), settings.get("pace_zone_names"), ""),
        f"Sweet spot: {_opt(settings.get('sweet_spot_min'))}–{_opt(settings.get('sweet_spot_max'))}",
    ]
    return "\n".join(lines) + "\n"


POWER_BUCKETS_SECS = [1, 5, 15, 30, 60, 120, 300, 600, 1200, 3600]
HR_BUCKETS_SECS = [5, 30, 60, 300, 1200, 3600]
PACE_BUCKETS_SECS = [15, 60, 300, 1200, 3600]


def _human_duration(secs: int) -> str:
    """Format a duration in seconds as a coach-readable label (e.g. '20m', '5s')."""
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    hours = secs // 3600
    rem_min = (secs % 3600) // 60
    return f"{hours}h" if rem_min == 0 else f"{hours}h{rem_min}m"


def _pace_per_km(meters_per_sec: float) -> str:
    """Convert m/s to a min/km label (e.g. '4:12 /km'). Returns '?' for non-positive."""
    if not meters_per_sec or meters_per_sec <= 0:
        return "?"
    total_secs = 1000 / meters_per_sec
    mins = int(total_secs // 60)
    secs = int(round(total_secs - mins * 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d} /km"


def _downsample_pairs(
    secs: list[int], values: list[Any], buckets: list[int]
) -> list[tuple[int, Any]]:
    """Pick the entry in `secs` closest to each bucket; emit (bucket, value) pairs."""
    if not secs or not values:
        return []
    pairs: list[tuple[int, Any]] = []
    for target in buckets:
        # Find closest secs[] entry to target
        best_idx = min(range(len(secs)), key=lambda i: abs(secs[i] - target))
        if best_idx < len(values):
            pairs.append((target, values[best_idx]))
    return pairs


def _curve_meta_line(curve: dict[str, Any]) -> str:
    """Format a curve's label / date-range / activity-count line."""
    label = curve.get("label") or curve.get("filter_label") or curve.get("id") or "?"
    start = curve.get("start_date_local")
    end = curve.get("end_date_local")
    days = curve.get("days")
    range_part = f" {start}..{end}" if start and end else ""
    days_part = f"  ({days}d)" if days is not None else ""
    return f"[{label}]{range_part}{days_part}"


def _format_curve_generic(
    curve: dict[str, Any],
    buckets: list[int],
    summary_only: bool,
    unit: str,
    value_renderer: Any = None,
) -> str:
    """Shared body for power/hr/pace single-curve formatters."""
    secs = curve.get("secs") or []
    values = curve.get("values") or []
    if not isinstance(secs, list) or not isinstance(values, list):
        return "(invalid curve)"
    header = _curve_meta_line(curve)
    if summary_only:
        pairs = _downsample_pairs(secs, values, buckets)
    else:
        pairs = list(zip(secs, values, strict=False))
    rendered: list[str] = [header]
    for duration, value in pairs:
        rendered_value = value_renderer(value) if value_renderer else f"{value}{unit}"
        rendered.append(f"  {_human_duration(duration):>5}: {rendered_value}")
    return "\n".join(rendered)


def format_power_curve(curve: dict[str, Any], summary_only: bool = True) -> str:
    """Format a single power curve. summary_only emits coach-canonical buckets."""
    return _format_curve_generic(curve, POWER_BUCKETS_SECS, summary_only, "W")


def format_hr_curve(curve: dict[str, Any], summary_only: bool = True) -> str:
    """Format a single HR curve."""
    return _format_curve_generic(curve, HR_BUCKETS_SECS, summary_only, " bpm")


def format_pace_curve(curve: dict[str, Any], summary_only: bool = True) -> str:
    """Format a single pace curve. Values are m/s; rendered as min/km."""
    return _format_curve_generic(
        curve, PACE_BUCKETS_SECS, summary_only, " m/s",
        value_renderer=lambda v: f"{v} m/s ({_pace_per_km(v)})",
    )


def format_curve_set(
    curves: list[dict[str, Any]],
    curve_type: str,
    summary_only: bool = True,
) -> str:
    """Format a DataCurveSet (list of curves). curve_type ∈ {"power","hr","pace"}."""
    if not curves:
        return f"No {curve_type} curves in this range.\n"
    formatter = {
        "power": format_power_curve,
        "hr": format_hr_curve,
        "pace": format_pace_curve,
    }.get(curve_type, format_power_curve)
    blocks = [
        f"{curve_type.capitalize()} curves ({len(curves)}):",
        "",
    ]
    for curve in curves:
        if isinstance(curve, dict):
            blocks.append(formatter(curve, summary_only))
            blocks.append("")
    return "\n".join(blocks)


def format_best_efforts(payload: dict[str, Any] | list[dict[str, Any]]) -> str:
    """Format the activity best-efforts response.

    Accepts either a raw list or the BestEfforts {"efforts": [...]} envelope.
    """
    if isinstance(payload, dict):
        efforts = payload.get("efforts") or []
    elif isinstance(payload, list):
        efforts = payload
    else:
        efforts = []
    if not efforts:
        return "No best efforts in this activity.\n"
    lines = [f"Best efforts ({len(efforts)}):", ""]
    for effort in efforts:
        if not isinstance(effort, dict):
            continue
        duration = effort.get("duration") or 0
        avg = effort.get("average", "?")
        distance = effort.get("distance")
        dist_part = f"  dist={distance}m" if distance else ""
        lines.append(f"  {_human_duration(duration):>5}: avg={avg}{dist_part}")
    return "\n".join(lines) + "\n"


def format_power_vs_hr(data: dict[str, Any], summary_only: bool = True) -> str:
    """Format the activity power-vs-HR response.

    Expects fields like hr_values[] and power_values[] (paired by index) and
    optionally `decoupling`. summary_only collapses to ~10 hr buckets.
    """
    hr_values = data.get("hr_values") or data.get("hr") or []
    power_values = data.get("power_values") or data.get("power") or []
    decoupling = data.get("decoupling")
    lines = []
    if decoupling is not None:
        lines.append(f"Aerobic decoupling: {decoupling}")
    if not isinstance(hr_values, list) or not isinstance(power_values, list):
        lines.append("(no paired HR/power data)")
        return "\n".join(lines) + "\n"
    pairs = list(zip(hr_values, power_values, strict=False))
    if summary_only and len(pairs) > 12:
        step = max(1, len(pairs) // 10)
        pairs = pairs[::step][:12]
    lines.append("HR vs Power:")
    for hr, power in pairs:
        lines.append(f"  {hr} bpm  →  {power} W")
    return "\n".join(lines) + "\n"


def format_interval_stats(stats: dict[str, Any]) -> str:
    """Format the interval-stats response (an Interval record)."""
    return f"""Interval stats:
ID: {_opt(stats.get('id'))}
Duration: {_opt(stats.get('elapsed_time'), ' s')} (moving: {_opt(stats.get('moving_time'), ' s')})
Distance: {_opt(stats.get('distance'), ' m')}
Avg power: {_opt(stats.get('average_watts'), ' W')} (w/kg {_opt(stats.get('average_watts_kg'))})
NP/IF: {_opt(stats.get('weighted_average_watts'))} W / {_opt(stats.get('intensity'))}
Avg HR: {_opt(stats.get('average_heartrate'), ' bpm')} max {_opt(stats.get('max_heartrate'), ' bpm')}
Avg speed: {_opt(stats.get('average_speed'), ' m/s')}
Avg cadence: {_opt(stats.get('average_cadence'), ' rpm')}
Elevation gain: {_opt(stats.get('total_elevation_gain'), ' m')}
"""


def format_weather_summary(weather: dict[str, Any]) -> str:
    """Format the activity weather-summary response."""
    return f"""Weather summary:
Avg temp: {_opt(weather.get('average_temp'), '°')} (min {_opt(weather.get('min_temp'), '°')}, max {_opt(weather.get('max_temp'), '°')})
Apparent temp: avg {_opt(weather.get('average_feels_like'), '°')}
Humidity: {_opt(weather.get('average_humidity'), '%')}
Precipitation: {_opt(weather.get('total_precipitation'), ' mm')}
Solar (UV): {_opt(weather.get('average_uv'))}
"""


def format_activity_search_hit(hit: dict[str, Any]) -> str:
    """Format one row of the search-full response."""
    return (
        f"- id={hit.get('id', '?')}  "
        f"{hit.get('start_date_local', hit.get('startTime', '?'))}  "
        f"{hit.get('type', '?')}  {hit.get('name', 'Unnamed')!r}"
    )


def format_interval_match(match: dict[str, Any]) -> str:
    """Format one row of the interval-search response."""
    return (
        f"- activity={match.get('activity_id', '?')}  "
        f"interval#{match.get('interval_index', '?')}  "
        f"dur={_human_duration(match.get('duration', 0) or 0)}  "
        f"power={match.get('average_watts', '?')}W"
    )


def format_mmp_model(model: dict[str, Any]) -> str:
    """Format the MMP / power-duration model used for resolving %MMP steps."""
    return f"""MMP model:
CP: {_opt(model.get('cp'), 'W')}  (FTP est: {_opt(model.get('ftp_est'), 'W')})
W': {_opt(model.get('w_prime'), ' J')}
Pmax: {_opt(model.get('p_max'), 'W')}
Tau: {_opt(model.get('tau'))}
Days used: {_opt(model.get('days'))}
Date range: {_opt(model.get('start_date_local'))} .. {_opt(model.get('end_date_local'))}
"""


def format_folder_summary(folders: list[dict[str, Any]]) -> str:
    """Format a list of workout folders / plans."""
    if not folders:
        return "No folders.\n"
    lines = [f"Folders ({len(folders)}):", ""]
    for folder in folders:
        if not isinstance(folder, dict):
            continue
        sports = folder.get("activity_types") or []
        sport = ", ".join(str(s) for s in sports) if isinstance(sports, list) else str(sports)
        lines.append(
            f"- id={folder.get('id', '?')}  "
            f"name={folder.get('name', 'Unnamed')!r}  "
            f"type={folder.get('type', 'N/A')}  "
            f"workouts={folder.get('num_workouts', 0)}  "
            f"sport={sport or 'N/A'}"
        )
    return "\n".join(lines) + "\n"
