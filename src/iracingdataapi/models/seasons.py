from typing import Any

from pydantic import BaseModel

from .cars import CarType, RaceWeekCarClasses
from .common import LicenseGroupType, SimpleEligibility
from .sessions import HeatInfo
from .tracks import SimpleTrackState, Track, TrackType
from .weather import ForecastOptions, SimpleWeather, WeatherSummary


class BaseSeasonIdentifiers(BaseModel):
    """Base class for season and series identification"""

    season_id: int
    season_name: str
    series_id: int
    series_name: str


class BaseRaceWeekConfig(BaseModel):
    """Base class for race week configuration"""

    race_lap_limit: int | None
    race_time_limit: int | None
    race_week_num: int
    restart_type: str
    short_parade_lap: bool
    start_type: str
    start_zone: bool


class BaseQualifyingConfig(BaseModel):
    """Base class for qualifying configuration"""

    qual_attached: bool
    qualify_laps: int | None = None
    qualify_length: int | None = None


class BaseScheduleMetadata(BaseModel):
    """Base class for schedule metadata"""

    schedule_name: str
    start_date: str
    special_event_type: None = None
    week_end_time: str


class BaseSeasonConfig(BaseModel):
    """Base class for common season configuration flags and settings"""

    car_class_ids: list[int]
    car_switching: bool
    car_types: list[CarType]
    caution_laps_do_not_count: bool
    connection_black_flag: bool
    consec_caution_within_nlaps: int
    consec_cautions_single_file: bool
    cross_license: bool
    distributed_matchmaking: bool
    driver_change_rule: int
    driver_changes: bool
    drops: int
    enable_pitlane_collisions: bool
    fixed_setup: bool
    green_white_checkered_limit: int
    grid_by_class: bool
    hardcore_level: int
    has_supersessions: bool
    heat_ses_info: HeatInfo | None = None
    ignore_license_for_practice: bool
    incident_limit: int
    incident_warn_mode: int
    incident_warn_param1: int
    incident_warn_param2: int
    is_heat_racing: bool
    license_group: int
    license_group_types: list[LicenseGroupType]
    lucky_dog: bool
    max_team_drivers: int
    max_weeks: int
    min_team_drivers: int
    multiclass: bool
    must_use_diff_tire_types_in_race: bool
    num_fast_tows: int
    num_opt_laps: int
    official: bool
    op_duration: int
    open_practice_session_type_id: int
    qualifier_must_start_race: bool
    race_week: int
    race_week_to_make_divisions: int
    reg_open_minutes: int | None = None
    reg_user_count: int
    region_competition: bool
    restrict_by_member: bool
    restrict_to_car: bool
    restrict_viewing: bool
    schedule_description: str
    send_to_open_practice: bool
    short_parade_lap: bool
    start_on_qual_tire: bool
    start_zone: bool
    track_types: list[TrackType]
    unsport_conduct_rule_mode: int


class SimpleSeason(BaseModel):
    season_quarter: int
    season_year: int


class Season(SimpleSeason, BaseSeasonIdentifiers):
    driver_changes: bool
    fixed_setup: bool
    license_group: int
    official: bool
    rookie_season: str | None = None


class CarRestriction(BaseModel):
    car_id: int
    max_dry_tire_sets: int
    max_pct_fuel_fill: float
    power_adjust_pct: float
    qual_setup_id: int | None = None
    race_setup_id: int | None = None
    weight_penalty_kg: float


class CurrentWeekSched(BaseModel):
    car_restrictions: list[CarRestriction]
    category_id: int
    precip_chance: int
    race_lap_limit: int | None
    race_time_limit: int | None
    race_week_num: int
    start_type: str
    track: Track


class SeriesSeason(BaseSeasonConfig, BaseSeasonIdentifiers, SimpleSeason):
    active: bool
    allowed_season_members: None = None
    complete: bool
    current_week_sched: CurrentWeekSched | None = None
    elig: SimpleEligibility
    has_mpr: bool
    race_week_car_class_ids: list[RaceWeekCarClasses] | None = None
    season_short_name: str
    start_date: str


class EventOptions(BaseModel):
    allow_wave_arounds: bool
    cautions_enabled: bool
    qualify_scoring_type: int
    restart_type: int
    short_parade_lap: bool
    single_file_consec_cautions: bool
    standing_start: bool
    starting_grid_type: int


class EventSession(BaseModel):
    laps: int
    minutes: int
    start_time_offset: int
    type: int
    type_name: str
    unlimited_laps: bool
    unlimited_time: bool


class RaceTimeDescriptor(BaseModel):
    day_offset: list[int] | None = None
    first_session_time: str | None = None
    repeat_minutes: int | None = None
    repeating: bool
    session_minutes: int
    session_times: list[str] | None = None
    start_date: str | None = None
    super_session: bool


class ScheduleForecastOptions(ForecastOptions):
    allow_fog: bool


class ScheduleWeatherSummary(BaseModel):
    max_precip_rate: float
    max_precip_rate_desc: str
    precip_chance: int
    skies_high: int
    skies_low: int
    temp_high: float
    temp_low: float
    temp_units: int
    wind_dir: int
    wind_high: float
    wind_low: float
    wind_units: int


class ScheduleWeather(SimpleWeather):
    allow_fog: bool
    forecast_options: ScheduleForecastOptions
    precip_option: int
    rel_humidity: int
    simulated_start_time: str
    simulated_time_multiplier: int
    simulated_time_offsets: list[int]
    skies: int
    temp_units: int
    temp_value: int
    time_of_day: int
    track_water: int
    version: int
    weather_summary: ScheduleWeatherSummary
    wind_dir: int
    wind_units: int
    wind_value: int


class Schedule(
    BaseSeasonIdentifiers,
    BaseRaceWeekConfig,
    BaseQualifyingConfig,
    BaseScheduleMetadata,
):
    car_restrictions: list[CarRestriction]
    category: str
    category_id: int
    enable_pitlane_collisions: bool
    event_options: EventOptions
    event_sessions: list[EventSession]
    full_course_cautions: bool
    practice_length: int
    qual_time_descriptors: list[Any]  # TODO: Correctly define
    race_time_descriptors: list[RaceTimeDescriptor]
    race_week_car_classes: list[Any]  # TODO: Correctly define
    track: Track
    track_state: SimpleTrackState
    warmup_length: int
    weather: ScheduleWeather


class RaceWeekCar(BaseModel):
    car_id: int
    car_name: str
    car_name_abbreviated: str


class SeriesSeasonScheduleWeather(BaseModel):
    fog: int | None = None
    rel_humidity: int
    skies: int
    temp_units: int
    temp_value: int
    type: int | None = None
    version: int
    weather_summary: WeatherSummary | None = None
    wind_dir: int
    wind_units: int
    wind_value: int
    forecast_options: ForecastOptions | None = None
    simulated_start_time: str
    simulated_time_multiplier: int
    simulated_time_offsets: list[int]
    time_of_day: int
    weather_url: str | None = None


class SeriesSeasonsResponseItemSchedule(
    BaseSeasonIdentifiers,
    BaseRaceWeekConfig,
    BaseQualifyingConfig,
    BaseScheduleMetadata,
):
    car_restrictions: list[CarRestriction]
    category: str
    category_id: int
    enable_pitlane_collisions: bool
    full_course_cautions: bool
    practice_length: int | None = None
    race_time_descriptors: list[RaceTimeDescriptor]
    race_week_car_class_ids: list[int]
    race_week_cars: list[RaceWeekCar]
    track: Track
    track_state: SimpleTrackState
    warmup_length: int | None = None
    weather: SeriesSeasonScheduleWeather


class SeriesSeasonsResponseItem(BaseSeasonConfig, SimpleSeason):
    season_id: int
    season_name: str

    series_id: int
    active: bool
    allowed_season_members: None = None
    complete: bool
    next_race_session: None = None
    schedules: list[SeriesSeasonsResponseItemSchedule]
    score_as_carclassid: int | None = None
    season_short_name: str
    start_date: str
