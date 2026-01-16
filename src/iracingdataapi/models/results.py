from datetime import datetime

from pydantic import BaseModel

from .cars import HostedResultCar, Livery
from .common import AllowedLicense, Helmet, MemberWithHelmet, ServerFarm, SimpleSuit
from .tracks import Track, TrackState, TrackWithConfig
from .weather import SimpleWeather


class BaseEventResult(BaseModel):
    """Base class for event-level result data"""

    event_type: int
    event_type_name: str
    event_strength_of_field: int
    event_best_lap_time: int


class BaseCautionData(BaseModel):
    """Base class for caution statistics"""

    num_cautions: int
    num_caution_laps: int


class BaseRaceMetadata(BaseModel):
    """Base class for common race metadata"""

    num_drivers: int
    num_lead_changes: int
    official_session: bool
    driver_changes: bool


class BaseSessionIdentifiers(BaseModel):
    """Base class for session identification"""

    subsession_id: int
    session_id: int


class BaseSeasonSeriesInfo(BaseModel):
    """Base class for season and series information"""

    season_id: int
    season_quarter: int
    season_year: int
    series_id: int
    series_name: str
    series_short_name: str


class SeriesResult(
    BaseEventResult,
    BaseCautionData,
    BaseRaceMetadata,
    BaseSessionIdentifiers,
    BaseSeasonSeriesInfo,
):
    end_time: datetime
    event_average_lap: int
    event_laps_complete: int
    license_category: str
    license_category_id: int
    race_week_num: int
    start_time: datetime
    track: Track
    winner_ai: bool
    winner_group_id: int
    winner_name: str


class SessionResultDetailBase(BaseModel):
    aggregate_champ_points: int
    ai: bool
    average_lap: int
    best_lap_num: int
    best_lap_time: int
    best_nlaps_num: int
    best_nlaps_time: int
    best_qual_lap_at: datetime
    best_qual_lap_num: int
    best_qual_lap_time: int
    car_class_id: int
    car_class_name: str
    car_class_short_name: str
    car_id: int
    car_name: str
    carcfg: int
    champ_points: int
    class_interval: int
    country_code: str
    display_name: str
    division: int
    drop_race: bool
    finish_position: int
    finish_position_in_class: int
    flair_id: int
    flair_name: str
    friend: bool
    incidents: int
    interval: int
    laps_complete: int
    laps_lead: int
    league_agg_points: int
    league_points: int
    license_change_oval: int
    license_change_road: int
    livery: Livery
    max_pct_fuel_fill: float
    new_cpi: float
    new_license_level: int
    new_sub_level: int
    new_ttrating: int
    newi_rating: int
    old_cpi: float
    old_license_level: int
    old_sub_level: int
    old_ttrating: int
    oldi_rating: int
    opt_laps_complete: int
    position: int
    qual_lap_time: int
    reason_out: str
    reason_out_id: int
    starting_position: int
    starting_position_in_class: int
    suit: SimpleSuit
    watched: bool
    weight_penalty_kg: float


class SessionResultDetailDriver(SessionResultDetailBase):
    cust_id: int
    flair_shortname: str
    helmet: Helmet
    team_id: int


class SessionResultDetail(SessionResultDetailBase):
    cust_id: int | None = None
    division_name: str | None = None
    driver_results: list[SessionResultDetailDriver] | None = None
    flair_shortname: str | None = None
    helmet: Helmet | None = None
    team_id: int | None = None


class HostedResult(BaseModel):
    session_id: int
    subsession_id: int
    start_time: datetime
    end_time: datetime
    license_category_id: int
    num_drivers: int
    num_cautions: int
    num_caution_laps: int
    num_lead_changes: int
    event_average_lap: int
    event_best_lap_time: int
    event_laps_complete: int
    driver_changes: bool
    winner_group_id: int
    winner_ai: bool
    track: TrackWithConfig
    private_session_id: int
    session_name: str
    league_id: int
    league_season_id: int
    created: datetime
    practice_length: int
    qualify_length: int
    qualify_laps: int
    race_length: int
    race_laps: int
    heat_race: bool
    host: MemberWithHelmet
    cars: list[HostedResultCar]


class ResultEventLog(BaseModel):
    subsession_id: int
    simsession_number: int
    session_time: int
    event_seq: int
    event_code: int
    group_id: int
    cust_id: int
    lap_number: int
    description: str
    message: str
    display_name: str


class ResultAllowedLicense(AllowedLicense):
    parent_id: int


class ResultCarId(BaseModel):
    car_id: int


class ResultCarClass(BaseModel):
    car_class_id: int
    name: str
    num_entries: int
    short_name: str
    strength_of_field: int


class ResultCarClassExtended(ResultCarClass):
    cars_in_class: list[ResultCarId]


class ResultRaceSummary(BaseCautionData):
    average_lap: int
    field_strength: int
    has_opt_path: bool
    heat_info_id: int | None = None
    laps_complete: int
    num_lead_changes: int
    num_opt_laps: int
    special_event_type: int
    special_event_type_text: str
    subsession_id: int


class WeatherResult(BaseModel):
    avg_cloud_cover_pct: float
    avg_rel_humidity: float
    avg_skies: int
    avg_temp: float
    avg_wind_dir: int
    avg_wind_speed: float
    fog_time_pct: float
    max_cloud_cover_pct: float
    max_fog: float
    max_temp: float
    max_wind_speed: float
    min_cloud_cover_pct: float
    min_temp: float
    min_wind_speed: float
    precip_mm: int
    precip_mm2hr_before_session: int
    precip_time_pct: float
    simulated_start_time: str
    temp_units: int
    wind_units: int


class SessionResult(BaseModel):
    results: list[SessionResultDetail]
    simsession_name: str
    simsession_number: int
    simsession_subtype: int
    simsession_type: int
    simsession_type_name: str
    weather_result: WeatherResult


class SessionSplit(BaseModel):
    event_strength_of_field: int
    subsession_id: int


class ResultWeather(SimpleWeather):
    precip_mm2hr_before_final_session: int
    precip_mm_final_session: int
    precip_time_pct: float
    simulated_start_time: str
    time_of_day: int
    weather_var_initial: int
    weather_var_ongoing: int


class Result(
    BaseEventResult,
    BaseCautionData,
    BaseRaceMetadata,
    BaseSessionIdentifiers,
    BaseSeasonSeriesInfo,
):
    allowed_licenses: list[ResultAllowedLicense] | None = None
    associated_subsession_ids: list[int]
    can_protest: bool
    car_classes: list[ResultCarClassExtended]
    caution_type: int
    cooldown_minutes: int
    corners_per_lap: int
    damage_model: int
    driver_change_param1: int
    driver_change_param2: int
    driver_change_rule: int
    end_time: str
    event_average_lap: int
    event_laps_complete: int
    heat_info_id: int
    host_id: int | None = None
    league_id: int | None = None
    league_name: str | None = None
    league_season_id: int | None = None
    league_season_name: str | None = None
    license_category: str
    license_category_id: int
    limit_minutes: int
    max_team_drivers: int
    max_weeks: int
    min_team_drivers: int
    num_laps_for_qual_average: int
    num_laps_for_solo_average: int
    points_type: str
    private_session_id: int
    race_summary: ResultRaceSummary
    race_week_num: int
    restrict_results: bool | None = None
    results_restricted: bool
    season_name: str
    season_short_name: str
    series_logo: str | None = None
    session_name: str | None = None
    session_results: list[SessionResult]
    session_splits: list[SessionSplit]
    special_event_type: int
    start_time: str
    track: Track
    track_state: TrackState
    weather: ResultWeather


class SeasonResult(
    BaseEventResult, BaseCautionData, BaseRaceMetadata, BaseSessionIdentifiers
):
    car_classes: list[ResultCarClass]
    farm: ServerFarm
    race_week_num: int
    start_time: str
    track: Track
    winner_helmet: Helmet
    winner_id: int
    winner_license_level: int
    winner_name: str
