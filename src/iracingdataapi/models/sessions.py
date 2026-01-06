from pydantic import BaseModel

from .cars import Car, CarType, HostedCombinedSessionCar, LeagueSessionCar, Livery
from .common import (
    Admin,
    Helmet,
    Image,
    LicenseGroupType,
    Member,
    ServerFarm,
    SessionEligibility,
)
from .leagues import LeagueCar, LeagueSessionWeather
from .members import MemberLicense
from .tracks import Track, TrackState, TrackType
from .weather import Weather


class SessionEventType(BaseModel):
    event_type: int


class SessionSessionType(BaseModel):
    session_type: int


class SessionCar(BaseModel):
    car_class_id: int
    car_class_name: str
    car_id: int
    car_name: str
    max_dry_tire_sets: int
    max_pct_fuel_fill: float
    package_id: int
    power_adjust_pct: float
    qual_setup_filename: str | None = None
    qual_setup_id: int | None = None
    race_setup_filename: str | None = None
    race_setup_id: int | None = None
    weight_penalty_kg: float


class HeatInfo(BaseModel):
    consolation_delta_max_field_size: int
    consolation_delta_session_laps: int
    consolation_delta_session_length_minutes: int
    consolation_first_max_field_size: int
    consolation_first_session_laps: int
    consolation_first_session_length_minutes: int
    consolation_num_position_to_invert: int
    consolation_num_to_consolation: int
    consolation_num_to_main: int
    consolation_run_always: bool
    consolation_scores_champ_points: bool
    created: str
    cust_id: int
    description: str | None = None
    heat_caution_type: int
    heat_info_id: int
    heat_info_name: str
    heat_laps: int
    heat_length_minutes: int
    heat_max_field_size: int
    heat_num_from_each_to_main: int
    heat_num_position_to_invert: int
    heat_scores_champ_points: bool
    heat_session_minutes_estimate: int
    hidden: bool
    main_laps: int
    main_length_minutes: int
    main_max_field_size: int
    main_num_position_to_invert: int
    max_entrants: int
    open_practice: bool
    pre_main_practice_length_minutes: int
    pre_qual_num_to_main: int
    pre_qual_practice_length_minutes: int
    qual_caution_type: int
    qual_laps: int
    qual_length_minutes: int
    qual_num_to_main: int
    qual_open_delay_seconds: int
    qual_scores_champ_points: bool
    qual_scoring: int
    qual_style: int
    race_style: int


class SimpleSession(BaseModel):
    adaptive_ai_difficulty: int | None = None
    adaptive_ai_enabled: bool
    admins: list[Admin]
    ai_avoid_players: bool
    ai_max_skill: int | None = None
    ai_min_skill: int | None = None
    ai_roster_name: str | None = None
    allowed_leagues: list[int]
    allowed_teams: list[int]
    car_types: list[CarType]
    cars: list[Car]
    cars_left: int | None = None
    category: str
    category_id: int
    connection_black_flag: bool
    consec_caution_within_nlaps: int
    consec_cautions_single_file: bool
    damage_model: int
    disallow_virtual_mirror: bool
    do_not_count_caution_laps: bool
    do_not_paint_cars: bool
    driver_change_rule: int
    driver_changes: bool
    elig: SessionEligibility
    enable_pitlane_collisions: bool
    entry_count: int
    event_types: list[SessionEventType]
    farm: ServerFarm
    fixed_setup: bool
    full_course_cautions: bool
    green_white_checkered_limit: int
    hardcore_level: int
    heat_ses_info: HeatInfo | None = None
    host: Admin
    incident_limit: int
    incident_warn_mode: int
    incident_warn_param1: int
    incident_warn_param2: int
    launch_at: str
    league_id: int
    league_season_id: int
    license_group_types: list[LicenseGroupType]
    lone_qualify: bool
    lucky_dog: bool
    max_ai_drivers: int
    max_drivers: int
    max_ir: int
    max_license_level: int
    max_team_drivers: int
    max_visor_tearoffs: int
    min_ir: int
    min_license_level: int
    min_team_drivers: int
    multiclass_type: int
    must_use_diff_tire_types_in_race: bool
    no_lapper_wave_arounds: bool
    num_fast_tows: int
    num_opt_laps: int
    order_id: int
    pace_car_class_id: int | None
    pace_car_id: int | None
    password_protected: bool
    practice_length: int
    private_session_id: int
    qualifier_must_start_race: bool
    qualify_laps: int
    qualify_length: int
    race_laps: int
    race_length: int
    registered_teams: list[int] | None = None
    restarts: int
    restrict_results: bool
    restrict_viewing: bool
    rolling_starts: bool
    session_desc: str | None = None
    session_name: str
    session_type: int
    session_types: list[SessionSessionType]
    short_parade_lap: bool
    start_on_qual_tire: bool
    start_zone: bool
    status: int
    team_entry_count: int
    telemetry_force_to_disk: int
    telemetry_restriction: int
    time_limit: int
    track: Track
    track_state: TrackState
    track_types: list[TrackType]
    unsport_conduct_rule_mode: int
    warmup_length: int
    weather: Weather


class HostedSession(SimpleSession):
    count_by_car_class_id: dict[str, int]
    count_by_car_id: dict[str, int]
    open_reg_expires: str
    pits_in_use: int
    session_full: bool
    session_id: int
    subsession_id: int


class HostedCombinedSession(SimpleSession):
    cars: list[HostedCombinedSessionCar]

    alt_asset_id: int | None = None
    available_reserved_broadcaster_slots: int
    available_spectator_slots: int
    broadcaster: bool
    can_broadcast: bool
    can_join: bool
    can_spot: bool
    can_watch: bool
    end_time: str
    friends: list[Member]
    is_heat_racing: bool
    max_users: int
    num_broadcasters: int
    num_spectator_slots: int
    num_spectators: int
    num_spotters: int
    populated: bool
    sess_admin: bool
    subsession_id: int
    watched: list[Member]


class LeagueSession(SimpleSession):
    admin: bool
    alt_asset_id: int | None = None
    available_reserved_broadcaster_slots: int
    available_spectator_slots: int
    broadcaster: bool
    can_broadcast: bool
    can_join: bool
    can_spot: bool
    can_watch: bool
    cars: list[LeagueSessionCar]
    end_time: str
    image: Image | None = None
    is_heat_racing: bool
    league_name: str
    league_season_name: str | None = None
    max_users: int
    num_broadcasters: int
    num_drivers: int
    num_spectator_slots: int
    num_spectators: int
    num_spotters: int
    populated: bool
    owner: bool
    race_length_type: int | None = None


class LeagueSessionTrackState(TrackState):
    practice_grip_compound: int
    qualify_grip_compound: int
    race_grip_compound: int
    warmup_grip_compound: int


class LeagueSeasonSession(BaseModel):
    cars: list[LeagueCar]
    driver_changes: bool
    entry_count: int
    has_results: bool
    launch_at: str
    league_id: int
    league_season_id: int
    lone_qualify: bool
    pace_car_class_id: None = None
    pace_car_id: None = None
    password_protected: bool
    practice_length: int
    private_session_id: int
    qualify_laps: int
    qualify_length: int
    race_laps: int
    race_length: int
    session_id: int | None = None
    status: int
    subsession_id: int | None = None
    team_entry_count: int
    time_limit: int
    track: Track
    track_state: LeagueSessionTrackState
    weather: LeagueSessionWeather
    winner_id: int | None = None
    winner_name: str | None = None


class RaceGuideSession(BaseModel):
    end_time: str
    entry_count: int
    race_week_num: int
    season_id: int
    series_id: int
    session_id: int | None = None
    start_time: str
    super_session: bool


class Subsession(BaseModel):
    event_type: int
    race_week_num: int
    season_id: int
    session_id: int
    start_time: str
    subsession_id: int


class Entry(BaseModel):
    car_class_id: int
    car_class_name: str
    car_id: int
    car_name: str
    country_code: str
    crew_allowed: int
    crew_password_protected: bool
    cust_id: int
    display_name: str
    elig: SessionEligibility
    event_type: int
    event_type_name: str
    farm_display_name: str
    flair_id: int
    flair_name: str
    flair_shortname: str
    helmet: Helmet
    license: MemberLicense
    license_order: int
    livery: Livery
    reg_status: str
    session_id: int
    subsession_id: int
    trusted_spotter: bool
