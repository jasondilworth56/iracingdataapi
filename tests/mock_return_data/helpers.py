"""Helper functions to create minimal valid mock data for testing."""


def get_minimal_result_mock(subsession_id=12345):
    """Create minimal Result mock matching API structure."""
    return {
        "subsession_id": subsession_id,
        "can_protest": True,
        "car_classes": [{
            "car_class_id": 1,
            "short_name": "Test",
            "name": "Test Class",
            "strength_of_field": 1000,
            "num_entries": 10,
            "cars_in_class": []
        }],
        "track": {
            "track_id": 1,
            "track_name": "Test Track",
            "config_name": "Test Config"
        },
        "weather": {
            "type": 0,
            "temp_units": 0,
            "temp_value": 78,
            "rel_humidity": 55,
            "fog": 0,
            "wind_dir": 0,
            "wind_units": 0,
            "skies": 0,
            "weather_var_initial": 0,
            "weather_var_ongoing": 0,
            "time_of_day": 2,
            "simulated_start_time": "2025-01-01T12:00:00Z",
            "simulated_time_offsets": [],
            "simulated_time_multiplier": 1
        },
        "session_results": []
    }


def get_minimal_result_search_hosted_mock():
    """Create minimal ResultSearchHosted list mock."""
    return [
        {
            "session_id": 123,
            "subsession_id": 456,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T01:00:00Z",
            "license_category_id": 1,
            "license_category": "road",
            "num_drivers": 10,
            "num_cautions": 0,
            "num_caution_laps": 0,
            "num_lead_changes": 5,
            "event_average_lap": 90000,
            "event_best_lap_time": 85000,
            "event_laps_complete": 20,
            "driver_changes": False,
            "winner_group_id": 1,
            "winner_name": "Winner",
            "winner_ai": False,
            "track": {
                "track_id": 1,
                "track_name": "Test Track",
                "config_name": None
            },
            "private_session_id": 789,
            "session_name": "Test Session",
            "league_id": 0,
            "league_season_id": 0,
            "created": "2025-01-01T00:00:00Z",
            "practice_length": 30,
            "qualify_length": 15,
            "qualify_laps": 0,
            "race_length": 60,
            "race_laps": 0,
            "heat_race": False,
            "host": {
                "cust_id": 999,
                "display_name": "Test Host",
                "helmet": {}
            }
        }
    ]


def get_minimal_result_search_series_mock():
    """Create minimal ResultSearchSeries list mock."""
    return [
        {
            "subsession_id": 123,
            "session_id": 456,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T01:00:00Z",
            "license_category_id": 2,
            "license_category": "road",
            "num_drivers": 20,
            "event_strength_of_field": 2000,
            "event_best_lap_time": 85000,
            "event_average_lap": 90000,
            "event_laps_complete": 10,
            "num_cautions": 0,
            "num_caution_laps": 0,
            "num_lead_changes": 3,
            "track": {
                "track_id": 1,
                "track_name": "Test Track",
                "config_name": None
            },
            "winner_group_id": 1,
            "winner_name": "Winner",
            "winner_ai": False,
            "series_id": 789,
            "series_name": "Test Series",
            "series_short_name": "TS",
            "season_id": 321,
            "season_name": "2025 S1",
            "season_short_name": "25S1",
            "season_year": 2025,
            "season_quarter": 1,
            "race_week_num": 1,
            "official_session": True,
            "driver_changes": False,
            "max_weeks": 12,
            "points_type": "race",
            "event_type": 5,
            "event_type_name": "Race"
        }
    ]


def get_minimal_result_season_results_mock():
    """Create minimal ResultSeasonResults mock."""
    return {
        "success": True,
        "season_id": 123,
        "results": []
    }


def get_minimal_season_list_mock():
    """Create minimal SeasonList mock."""
    return {
        "season_quarter": 1,
        "seasons": [
            {
                "season_id": 123,
                "season_name": "2025 Season 1",
                "series_id": 456,
                "series_name": "Test Series",
                "season_year": 2025,
                "season_quarter": 1,
                "license_group": 2,
                "fixed_setup": False,
                "official": True,
                "driver_changes": False,
                "active": True,
                "race_week": 1,
                "track_id": 789,
                "car_class_ids": [1, 2, 3],
                "car_types": [{
                    "car_type": "gt3"
                }]
            }
        ]
    }


def get_minimal_race_guide_mock():
    """Create minimal RaceGuide mock."""
    return {
        "subscribed": False,
        "sessions": [
            {
                "season_id": 123,
                "start_time": "2025-01-01T00:00:00+00:00",
                "super_session": False,
                "series_id": 456,
                "race_week_num": 1,
                "end_time": "2025-01-01T01:00:00+00:00",
                "session_id": 789,
                "entry_count": 20
            }
        ]
    }


def get_minimal_series_past_seasons_mock():
    """Create minimal SeriesPastSeasons mock wrapped in series key."""
    return {
        "series": {
            "series_id": 456,
            "series_name": "Test Series",
            "series_short_name": "TS",
            "category_id": 2,
            "category": "road",
            "active": True,
            "official": True,
            "fixed_setup": False,
            "license_group": 2,
            "license_group_types": [],
            "allowed_licenses": [],
            "seasons": [
                {
                    "season_id": 123,
                    "season_name": "2024 Season 4",
                    "season_short_name": "24S4",
                    "series_id": 456,
                    "season_year": 2024,
                    "season_quarter": 4,
                    "active": False,
                    "official": True,
                    "fixed_setup": False,
                    "driver_changes": False,
                    "license_group": 2
                }
            ]
        }
    }


def get_minimal_series_seasons_mock():
    """Create minimal SeriesSeason mock."""
    return [
        {
            "season_id": 123,
            "series_id": 456,
            "season_name": "2025 Season 1",
            "season_short_name": "25S1",
            "season_year": 2025,
            "season_quarter": 1,
            "license_group": 2,
            "fixed_setup": False,
            "official": True,
            "active": True,
            "complete": False,
            "driver_changes": False,
            "driver_change_rule": 0,
            "max_team_drivers": 6,
            "min_team_drivers": 1,
            "drops": 4,
            "race_week": 1,
            "race_week_to_make_divisions": 4,
            "max_weeks": 12,
            "multiclass": False,
            "grid_by_class": False,
            "incident_limit": 17,
            "incident_warn_mode": 0,
            "incident_warn_param1": 0,
            "incident_warn_param2": 0,
            "green_white_checkered_limit": 1,
            "caution_laps_do_not_count": False,
            "lucky_dog": False,
            "short_parade_lap": False,
            "start_zone": False,
            "start_on_qual_tire": False,
            "qualifier_must_start_race": False,
            "enable_pitlane_collisions": False,
            "must_use_diff_tire_types_in_race": False,
            "op_duration": 0,
            "open_practice_session_type_id": 0,
            "num_opt_laps": 0,
            "send_to_open_practice": False,
            "ignore_license_for_practice": False,
            "cross_license": False,
            "restrict_to_car": False,
            "restrict_by_member": False,
            "restrict_viewing": False,
            "is_heat_racing": False,
            "has_supersessions": False,
            "hardcore_level": 0,
            "unsport_conduct_rule_mode": 0,
            "start_date": "2025-01-01T00:00:00+00:00",
            "schedule_description": "Test Schedule",
            "reg_user_count": 0,
            "car_class_ids": [],
            "car_types": [],
            "license_group_types": [],
            "track_types": [],
            "schedules": []
        }
    ]


def get_minimal_team_mock():
    """Create minimal Team mock."""
    return {
        "team_id": 123,
        "owner_id": 456,
        "team_name": "Test Team",
        "created": "2025-01-01T00:00:00+00:00",
        "recruiting": False,
        "suit": {
            "pattern": 1,
            "color1": "ffffff",
            "color2": "000000",
            "color3": "ff0000"
        },
        "owner": {
            "cust_id": 456,
            "display_name": "Team Owner",
            "helmet": {
                "pattern": 1,
                "color1": "ffffff",
                "color2": "000000",
                "color3": "ff0000",
                "face_type": 1,
                "helmet_type": 1
            }
        },
        "roster": [],
        "pending_invites": [],
        "is_admin": False,
        "is_owner": False,
        "is_member": False
    }


def get_minimal_member_recap_mock():
    """Create minimal MemberRecap mock."""
    return {
        "year": 2025,
        "season": 1,
        "cust_id": 123,
        "success": True,
        "stats": {
            "starts": 10,
            "wins": 2,
            "top5": 5,
            "poles": 1,
            "avg_start_position": 5,
            "avg_finish_position": 4,
            "laps": 100,
            "laps_led": 20,
            "avg_incidents": 2.5,
            "avg_points": 85,
            "win_percentage": 20.0,
            "top5_percentage": 50.0,
            "laps_led_percentage": 20.0,
            "poles_percentage": 10.0,
            "favorite_car": {
                "car_id": 1,
                "car_name": "Test Car",
                "car_image": "test_car.jpg"
            },
            "favorite_track": {
                "track_id": 1,
                "track_name": "Test Track",
                "track_logo": "test_track.jpg"
            }
        }
    }


def get_minimal_season_driver_standings_mock():
    """Create minimal list of SeasonDriverStanding mocks."""
    return [
        {
            "rank": 1,
            "cust_id": 123,
            "display_name": "Test Driver",
            "division": 1,
            "country_code": "US",
            "country": "United States",
            "flair_id": 1,
            "flair_name": "Test Flair",
            "license": {
                "category_id": 2,
                "category": "road",
                "license_level": 10,
                "safety_rating": 3.5,
                "cpi": 50.0,
                "irating": 2000,
                "tt_rating": 1500,
                "mpr_num_races": 10,
                "color": "#FF0000",
                "group_name": "D",
                "group_id": 5
            },
            "helmet": {
                "pattern": 1,
                "color1": "ffffff",
                "color2": "000000",
                "color3": "ff0000",
                "face_type": 1,
                "helmet_type": 1
            },
            "weeks_counted": 8,
            "starts": 10,
            "wins": 2,
            "top5": 5,
            "top25_percent": 7,
            "poles": 1,
            "avg_start_position": 5.0,
            "avg_finish_position": 3.0,
            "avg_field_size": 20.0,
            "laps": 200,
            "laps_led": 50,
            "incidents": 10,
            "points": 500,
            "raw_points": 520.5,
            "week_dropped": False
        }
    ]


def get_minimal_season_qualify_results_mock():
    """Create minimal list of SeasonQualifyResult mocks."""
    return [
        {
            "rank": 1,
            "cust_id": 123,
            "display_name": "Test Driver",
            "country_code": "US",
            "country": "United States",
            "flair_id": 1,
            "flair_name": "Test Flair",
            "license": {
                "category_id": 2,
                "category": "road",
                "license_level": 10,
                "safety_rating": 3.5,
                "irating": 1500,
                "color": "#FF0000",
                "group_name": "D",
                "group_id": 5
            },
            "helmet": {
                "pattern": 1,
                "color1": "ffffff",
                "color2": "000000",
                "color3": "ff0000",
                "face_type": 1,
                "helmet_type": 1
            },
            "best_qual_lap_time": 85000,
            "week": 1
        }
    ]


def get_minimal_season_tt_results_mock():
    """Create minimal list of SeasonTTResult mocks."""
    return [
        {
            "rank": 1,
            "cust_id": 123,
            "display_name": "Test Driver",
            "division": 1,
            "country_code": "US",
            "country": "United States",
            "flair_id": 1,
            "flair_name": "Test Flair",
            "license": {
                "category_id": 2,
                "category": "road",
                "license_level": 10,
                "safety_rating": 3.5,
                "irating": 1500,
                "color": "#FF0000",
                "group_name": "D",
                "group_id": 5
            },
            "helmet": {
                "pattern": 1,
                "color1": "ffffff",
                "color2": "000000",
                "color3": "ff0000",
                "face_type": 1,
                "helmet_type": 1
            },
            "best_tt_lap_time": 85000,
            "best_nlaps_time": 270000,
            "starts": 5,
            "points": 100,
            "raw_points": 105.5,
            "week": 1
        }
    ]


def get_minimal_season_tt_standings_mock():
    """Create minimal list of SeasonTTStanding mocks."""
    return [
        {
            "rank": 1,
            "cust_id": 123,
            "display_name": "Test Driver",
            "division": 1,
            "country_code": "US",
            "country": "United States",
            "flair_id": 1,
            "flair_name": "Test Flair",
            "license": {
                "category_id": 2,
                "category": "road",
                "license_level": 10,
                "safety_rating": 3.5,
                "irating": 1500,
                "color": "#FF0000",
                "group_name": "D",
                "group_id": 5
            },
            "helmet": {
                "pattern": 1,
                "color1": "ffffff",
                "color2": "000000",
                "color3": "ff0000",
                "face_type": 1,
                "helmet_type": 1
            },
            "points": 100,
            "weeks_counted": 8,
            "starts": 10,
            "wins": 3,
            "top5": 6,
            "top25_percent": 8,
            "poles": 2,
            "avg_start_position": 4.5,
            "avg_finish_position": 3.2,
            "avg_field_size": 18.0,
            "week_dropped": False,
            "laps": 100,
            "laps_led": 30,
            "incidents": 5,
            "raw_points": 110.0
        }
    ]


def get_minimal_world_records_mock():
    """Create minimal list of WorldRecord mocks."""
    return [
        {
            "cust_id": 123,
            "display_name": "Test Driver",
            "best_lap_time": 60000,
            "best_lap_number": 5,
            "best_nlaps": 10,
            "best_nlaps_time": 600000,
            "club_name": "Test Club",
            "region": "Test Region",
            "country_code": "US",
            "year": 2025,
            "quarter": 1,
            "week": 1,
            "car_id": 1,
            "car_class_id": 1,
            "category_id": 1,
            "season_id": 1,
            "track_id": 1,
            "license": {
                "seq": 1,
                "category_id": 1,
                "category": "road",
                "license_level": 5,
                "safety_rating": 3.5,
                "cpi": 1000.0,
                "irating": 1500,
                "tt_rating": 1500,
                "mpr_num_races": 10,
                "group_name": "D",
                "group_id": 5
            }
        }
    ]


def get_minimal_lap_data_mock():
    """Get minimal valid LapData list mock data."""
    return [
        {
            "group_id": 1,
            "name": "Test Team",
            "cust_id": 123,
            "display_name": "Test Driver",
            "lap_number": 1,
            "flags": 0,
            "incident": False,
            "session_time": 60000,
            "lap_time": 60000,
            "team_fastest_lap": False,
            "personal_best_lap": False,
            "helmet": {"pattern": 1, "color1": "ffffff", "color2": "000000", "color3": "ff0000", "face_type": 1, "helmet_type": 1},
            "license_level": 5,
            "car_number": "1",
            "lap_events": [],
            "ai": False
        }
    ]


def get_minimal_event_log_mock():
    """Get minimal valid EventLogEntry list mock data."""
    return [
        {
            "subsession_id": 12345,
            "simsession_number": 0,
            "session_time": 60000,
            "event_seq": 1,
            "event_code": 1,
            "group_id": 1,
            "cust_id": 123,
            "display_name": "Test Driver",
            "lap_number": 1,
            "description": "Test event",
            "message": "Test message"
        }
    ]
