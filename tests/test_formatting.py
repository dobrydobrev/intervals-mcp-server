"""
Unit tests for formatting utilities in intervals_mcp_server.utils.formatting.

These tests verify that the formatting functions produce expected output strings for activities, workouts, wellness entries, events, and intervals.
"""

import json
from intervals_mcp_server.utils.formatting import (
    format_activity_summary,
    format_athlete_profile,
    format_athlete_summary,
    format_event_details,
    format_event_summary,
    format_fitness_model_events,
    format_intervals,
    format_sport_settings_details,
    format_sport_settings_summary,
    format_training_plan,
    format_wellness_entry,
    format_workout,
)
from tests.sample_data import INTERVALS_DATA


def test_format_activity_summary():
    """
    Test that format_activity_summary returns a string containing the activity name and ID.
    """
    data = {
        "name": "Morning Ride",
        "id": 1,
        "type": "Ride",
        "startTime": "2024-01-01T08:00:00Z",
        "distance": 1000,
        "duration": 3600,
    }
    result = format_activity_summary(data)
    assert "Activity: Morning Ride" in result
    assert "ID: 1" in result


def test_format_workout():
    """
    Test that format_workout returns a string containing the workout name and interval count.
    """
    workout = {
        "name": "Workout1",
        "description": "desc",
        "sport": "Ride",
        "duration": 3600,
        "tss": 50,
        "intervals": [1, 2, 3],
    }
    result = format_workout(workout)
    assert "Workout: Workout1" in result
    assert "Intervals: 3" in result


def test_format_wellness_entry():
    """
    Test that format_wellness_entry returns a string containing the date and fitness (CTL).
    """
    with open("tests/ressources/wellness_entry.json", "r", encoding="utf-8") as f:
        entry = json.load(f)
    result = format_wellness_entry(entry)

    with open("tests/ressources/wellness_entry_formatted.txt", "r", encoding="utf-8") as f:
        expected_result = f.read()
    assert result == expected_result


def test_format_wellness_entry_include_all_fields():
    """
    Test that format_wellness_entry with include_all_fields=True includes additional unknown fields.
    """
    entry = {
        "id": "2024-06-01",
        "ctl": 80,
        "weight": 75,
        "customField1": "hello",
        "customField2": 42,
        "updated": "2024-06-01T10:00:00Z",
    }
    result = format_wellness_entry(entry, include_all_fields=True)
    assert "Date: 2024-06-01" in result
    assert "Fitness (CTL): 80" in result
    assert "Weight: 75 kg" in result
    assert "Other Fields:" in result
    assert "customField1: hello" in result
    assert "customField2: 42" in result
    # "updated" is a known built-in field, should not appear in Other Fields
    assert "updated:" not in result


def test_format_wellness_entry_no_extra_fields_by_default():
    """
    Test that format_wellness_entry without include_all_fields does not include additional fields.
    """
    entry = {
        "id": "2024-06-01",
        "ctl": 80,
        "customField1": "hello",
    }
    result = format_wellness_entry(entry)
    assert "Other Fields:" not in result
    assert "customField1" not in result


def test_format_wellness_entry_macros_populated():
    """
    Test that format_wellness_entry renders native nutrition macros
    (carbohydrates, protein, fatTotal) in grams when present.
    """
    entry = {
        "id": "2026-04-08",
        "carbohydrates": 310,
        "protein": 145,
        "fatTotal": 72,
    }
    result = format_wellness_entry(entry)
    assert "Nutrition & Hydration:" in result
    assert "- Carbohydrates: 310 g" in result
    assert "- Protein: 145 g" in result
    assert "- Fat: 72 g" in result


def test_format_wellness_entry_macros_null_hidden():
    """
    Test that format_wellness_entry hides macro lines when the fields are null,
    preserving backward compatibility with older wellness records.
    """
    entry = {
        "id": "2026-04-08",
        "ctl": 80,
        "carbohydrates": None,
        "protein": None,
        "fatTotal": None,
    }
    result = format_wellness_entry(entry)
    assert "Carbohydrates" not in result
    assert "Protein" not in result
    # "Fat" could legitimately appear inside e.g. "Body Fat" elsewhere, so
    # anchor the negative assertion on the line-prefix form we would emit.
    assert "- Fat:" not in result


def test_format_event_summary():
    """
    Test that format_event_summary returns a string containing the event date and type.
    """
    event = {
        "start_date_local": "2024-01-01",
        "id": "e1",
        "name": "Event1",
        "description": "desc",
        "race": True,
    }
    summary = format_event_summary(event)
    assert "Date: 2024-01-01" in summary
    assert "Type: Race" in summary


def test_format_event_details():
    """
    Test that format_event_details returns a string containing event and workout details.
    """
    event = {
        "id": "e1",
        "date": "2024-01-01",
        "name": "Event1",
        "description": "desc",
        "workout": {
            "id": "w1",
            "sport": "Ride",
            "duration": 3600,
            "tss": 50,
            "intervals": [1, 2],
        },
        "race": True,
        "priority": "A",
        "result": "1st",
        "calendar": {"name": "Main"},
    }
    details = format_event_details(event)
    assert "Event Details:" in details
    assert "Workout Information:" in details


def test_format_intervals():
    """
    Test that format_intervals returns a string containing interval analysis and the interval label.
    """
    result = format_intervals(INTERVALS_DATA)
    assert "Intervals Analysis:" in result
    assert "Rep 1" in result


def test_format_athlete_summary():
    athlete = {
        "id": "i1",
        "firstname": "Ada",
        "lastname": "Lovelace",
        "sex": "F",
        "icu_weight": 60.0,
        "icu_resting_hr": 48,
        "timezone": "Europe/Sofia",
        "country": "BG",
        "training_plan_id": 99,
        "training_plan_start_date": "2026-01-01",
        "icu_type_settings": [{"type": "Ride"}, {"type": "Run"}],
        "bio": "test",
    }
    out = format_athlete_summary(athlete)
    assert "Ada Lovelace" in out
    assert "ID: i1" in out
    assert "60.0 kg" in out
    assert "48 bpm" in out
    assert "Ride" in out and "Run" in out
    assert "Europe/Sofia" in out


def test_format_athlete_profile():
    profile = {
        "athlete": {"id": "i1", "firstname": "X", "lastname": "Y"},
        "sharedFolders": [{"id": 1, "name": "Base"}],
        "customItems": [{"id": 2, "name": "Notes"}],
    }
    out = format_athlete_profile(profile)
    assert "Athlete Profile:" in out
    assert "X Y" in out
    assert "Shared folders (1)" in out
    assert "Base" in out
    assert "Notes" in out


def test_format_training_plan():
    plan = {
        "athlete_id": "i1",
        "training_plan_id": 12,
        "training_plan_start_date": "2026-01-01",
        "training_plan_last_applied": "2026-01-02T10:00:00Z",
        "timezone": "UTC",
        "training_plan_alias": "Build 1",
        "training_plan": {"id": 12, "name": "Build Phase"},
    }
    out = format_training_plan(plan)
    assert "Training Plan:" in out
    assert "Build Phase" in out
    assert "Build 1" in out
    assert "2026-01-01" in out


def test_format_fitness_model_events_empty():
    assert "No fitness-model events" in format_fitness_model_events([])


def test_format_fitness_model_events_some():
    events = [
        {"start_date_local": "2026-01-01", "category": "WORKOUT", "name": "VO2"},
        {"date": "2026-01-02", "type": "RACE", "name": "Cat 3 crit"},
    ]
    out = format_fitness_model_events(events)
    assert "VO2" in out
    assert "Cat 3 crit" in out
    assert "2026-01-02" in out


def test_format_sport_settings_summary():
    settings = [
        {"id": "Ride", "types": ["Ride"], "ftp": 280, "lthr": 165, "max_hr": 188},
        {"id": "Run", "types": ["Run"], "ftp": None, "lthr": 165},
    ]
    out = format_sport_settings_summary(settings)
    assert "Sport Settings (2)" in out
    assert "FTP=280" in out
    assert "Run" in out


def test_format_sport_settings_details():
    settings = {
        "id": "Ride",
        "athlete_id": "i1",
        "types": ["Ride"],
        "ftp": 280,
        "indoor_ftp": 270,
        "lthr": 165,
        "max_hr": 188,
        "threshold_pace": 4.5,
        "pace_units": "MINS_KM",
        "w_prime": 18000,
        "p_max": 1100,
        "power_zones": [55, 75, 90, 105, 120],
        "power_zone_names": ["Recovery", "Endurance", "Tempo", "Threshold", "VO2"],
        "hr_zones": [120, 140, 160, 175, 188],
        "sweet_spot_min": 88,
        "sweet_spot_max": 94,
    }
    out = format_sport_settings_details(settings)
    assert "Ride" in out
    assert "FTP: 280W" in out
    assert "VO2=120W" in out
    assert "Sweet spot: 88–94" in out
