from pydantic import BaseModel

from src.iracingdataapi.models.cars import FavoriteCar, SimpleCarClass
from src.iracingdataapi.models.common import AllowedLicense, Helmet, LicenseGroupType
from src.iracingdataapi.models.members import SimpleMemberLicense, StatMemberLicense
from src.iracingdataapi.models.series import RaceWeek
from src.iracingdataapi.models.tracks import FavoriteTrack, SimpleTrack, Track


class SeriesStatSeason(BaseModel):
    active: bool
    car_classes: list[SimpleCarClass]
    car_switching: bool
    driver_changes: bool
    fixed_setup: bool
    has_supersessions: bool
    license_group: int
    license_group_types: list[LicenseGroupType]
    official: bool
    race_weeks: list[RaceWeek]
    season_id: int
    season_name: str
    season_quarter: int
    season_short_name: str
    season_year: int
    series_id: int


class SeriesStatsSeriesResponseItem(BaseModel):
    active: bool
    allowed_licenses: list[AllowedLicense]
    category: str
    category_id: int
    fixed_setup: bool
    license_group: int
    license_group_types: list[LicenseGroupType]
    logo: str | None
    official: bool
    search_filters: str | None = None
    seasons: list[SeriesStatSeason]
    series_id: int
    series_name: str
    series_short_name: str


class Best(BaseModel):
    best_lap_time: int
    end_time: str
    event_type: str
    season_quarter: int
    season_year: int
    subsession_id: int
    track: Track


class CareerStat(BaseModel):
    avg_finish_position: int
    avg_incidents: float
    avg_points: int
    avg_start_position: int
    category: str
    category_id: int
    laps: int
    laps_led: int
    laps_led_percentage: float
    poles: int
    poles_percentage: float
    starts: int
    top5: int
    top5_percentage: float
    win_percentage: float
    wins: int


class YearStat(CareerStat):
    year: int


class RecapStats(BaseModel):
    avg_finish_position: int
    avg_start_position: int
    favorite_car: FavoriteCar | None = None
    favorite_track: FavoriteTrack | None = None
    laps: int
    laps_led: int
    starts: int
    top5: int
    wins: int


class StatLivery(BaseModel):
    car_id: int
    color1: str
    color2: str
    color3: str
    pattern: int


class StatRecentRace(BaseModel):
    car_class_id: int
    car_id: int
    drop_race: bool
    finish_position: int
    incidents: int
    laps: int
    laps_led: int
    license_level: int
    livery: StatLivery
    new_sub_level: int
    newi_rating: int
    old_sub_level: int
    oldi_rating: int
    points: int
    qualifying_time: int
    race_week_num: int
    season_id: int
    season_quarter: int
    season_year: int
    series_id: int
    series_name: str
    session_start_time: str
    start_position: int
    strength_of_field: int
    subsession_id: int
    track: SimpleTrack
    winner_group_id: int
    winner_helmet: Helmet
    winner_license_level: int
    winner_name: str


class StatThisYear(BaseModel):
    num_league_sessions: int
    num_league_wins: int
    num_official_sessions: int
    num_official_wins: int


class SeasonDriverStandings(BaseModel):
    avg_field_size: int
    avg_finish_position: int
    avg_start_position: int
    country: str
    country_code: str
    cust_id: int
    display_name: str
    division: int
    flair_id: int
    flair_name: str
    flair_shortname: str | None = None
    helmet: Helmet
    incidents: int
    laps: int
    laps_led: int
    license: SimpleMemberLicense
    points: int
    poles: int
    rank: int
    raw_points: float
    starts: int
    top25_percent: int
    top5: int
    week_dropped: bool
    weeks_counted: int
    wins: int


class SeasonQualifyResult(BaseModel):
    best_qual_lap_time: int
    country: str
    country_code: str
    cust_id: int
    display_name: str
    flair_id: int
    flair_name: str
    flair_shortname: str | None = None
    helmet: Helmet
    license: SimpleMemberLicense
    rank: int
    week: int


class StatTeamDriver(BaseModel):
    avg_event_field_size: float
    avg_event_finish_position: float
    avg_event_start_position: float
    avg_event_strength_of_field: float
    avg_field_size: float
    avg_finish_position: float
    avg_start_position: float
    avg_strength_of_field: float
    country: str
    country_code: str
    cust_id: int
    display_name: str
    event_poles: int
    event_top10_percent: int
    event_top25_percent: int
    event_top5: int
    event_wins: int
    helmet: Helmet
    incidents: int
    laps: int
    laps_led: int
    license: SimpleMemberLicense
    points: int
    poles: int
    rank: int
    raw_points: int
    starts: int
    top10_percent: int
    top25_percent: int
    top5: int
    week_dropped: bool
    weeks_counted: int
    wins: int


class SeasonTeamStandings(BaseModel):
    avg_event_field_size: float
    avg_event_finish_position: float
    avg_event_start_position: float
    avg_event_strength_of_field: float
    avg_field_size: float
    avg_finish_position: float
    avg_start_position: float
    avg_strength_of_field: float
    cust_id: int
    display_name: str
    drivers: list[StatTeamDriver]
    event_poles: int
    event_top10_percent: int
    event_top25_percent: int
    event_top5: int
    event_wins: int
    incidents: int
    laps: int
    laps_led: int
    points: int
    poles: int
    rank: int
    raw_points: int
    starts: int
    team_id: int
    top10_percent: int
    top25_percent: int
    top5: int
    week_dropped: bool
    weeks_counted: int
    wins: int


class SeasonTTResult(BaseModel):
    best_nlaps_time: int
    country: str
    country_code: str
    cust_id: int
    display_name: str
    division: int
    flair_id: int
    flair_name: str
    flair_shortname: str | None = None
    helmet: Helmet
    license: StatMemberLicense
    points: int
    rank: int
    raw_points: float
    starts: int
    week: int


class SeasonTTStandings(BaseModel):
    avg_field_size: int
    avg_finish_position: int
    avg_start_position: int
    country: str
    country_code: str
    cust_id: int
    display_name: str
    division: int
    flair_id: int
    flair_name: str
    flair_shortname: str | None = None
    helmet: Helmet
    incidents: int
    laps: int
    laps_led: int
    license: StatMemberLicense
    points: int
    poles: int
    rank: int
    raw_points: float
    starts: int
    top25_percent: int
    top5: int
    week_dropped: bool
    weeks_counted: int
    wins: int


class StatWorldRecord(BaseModel):
    cust_id: int
    display_name: str
    car_id: int
    track_id: int
    season_year: int | None = None
    season_quarter: int | None = None
    country_code: str
    region: str
    license: SimpleMemberLicense
    practice_lap_time: int | None = None
    practice_date: str | None = None
    qualify_lap_time: int | None = None
    qualify_date: str | None = None
    tt_lap_time: int | None = None
    tt_date: str | None = None
    race_lap_time: int | None = None
    race_date: str | None = None
