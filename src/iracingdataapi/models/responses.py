from typing import Any, Optional

from pydantic import BaseModel

from .cars import Car, CarAsset, CarClass, CarInClass, CarWithAsset
from .common import Owner, SimpleSuit, Tags, TeamMembership, ValueWhenPair
from .constants import Category, Division, EventType
from .laps import ChartLap, Lap
from .leagues import (
    League,
    LeagueDirectoryItem,
    LeagueMembership,
    LeaguePointsSystem,
    LeagueSeason,
    LeagueStandings,
    RosterItem,
)
from .lookups import Flair, LookupCountry, LookupDriver, LookupLicense
from .members import (
    DriverFromCSV,
    Member,
    MemberActivity,
    MemberAward,
    MemberAwardBase,
    MemberFollowCounts,
    MemberInfo,
    MemberLicenseHistoryItem,
    MemberProfileMemberInfo,
    MemberRecentEvent,
)
from .results import HostedResult, Result, ResultEventLog, SeasonResult, SeriesResult
from .seasons import Schedule, Season, SeriesSeason, SeriesSeasonsResponseItem
from .series import BaseSeries, PastSeasonSeries, SeriesAsset, SeriesWithAsset
from .sessions import (
    Entry,
    HostedCombinedSession,
    HostedSession,
    LeagueSeasonSession,
    LeagueSession,
    RaceGuideSession,
    Subsession,
)
from .stats import (
    Best,
    CareerStat,
    RecapStats,
    SeasonDriverStandings,
    SeasonQualifyResult,
    SeasonTeamStandings,
    SeasonTTResult,
    SeasonTTStandings,
    SeriesStatsSeriesResponseItem,
    StatRecentRace,
    StatThisYear,
    StatWorldRecord,
    YearStat,
)
from .tracks import TrackAsset, TrackGetResponseItem, TrackWithAsset

CarAssetsResponse = dict[str, CarAsset]


CarGetResponse = list[Car]


CarWithAssetResponse = list[CarWithAsset]


CarclassGetResponse = list[CarClass]


ConstantsCategoriesResponse = list[Category]


ConstantsDivisionsResponse = list[Division]


ConstantsEventTypesResponse = list[EventType]


DriverListResponse = list[DriverFromCSV]


class HostedCombinedSessionsResponse(BaseModel):
    sequence: int
    sessions: list[HostedCombinedSession]
    subscribed: bool
    success: bool


class HostedSessionsResponse(BaseModel):
    sessions: list[HostedSession]
    subscribed: bool
    success: bool


class LeagueCustLeagueSessionsResponse(BaseModel):
    mine: bool
    sequence: int
    sessions: list[LeagueSession]
    subscribed: bool
    success: bool


class LeagueDirectoryResponse(BaseModel):
    lowerbound: int
    results_page: list[LeagueDirectoryItem]
    row_count: int
    success: bool
    upperbound: int


LeagueGetResponse = League


class LeagueGetPointsSystemsResponse(BaseModel):
    league_id: int
    points_systems: list[LeaguePointsSystem]
    season_id: int | None = None
    subscribed: bool
    success: bool


LeagueMembershipResponse = list[LeagueMembership]


class LeagueRosterResponse(BaseModel):
    private_roster: bool
    roster: list[RosterItem]


class LeagueSeasonSessionsResponse(BaseModel):
    league_id: int
    season_id: int
    sessions: list[LeagueSeasonSession]
    subscribed: bool
    success: bool


class LeagueSeasonStandingsResponse(BaseModel):
    car_class_id: int
    car_id: int
    league_id: int
    season_id: int
    standings: LeagueStandings
    success: bool


class LeagueSeasonsResponse(BaseModel):
    league_id: int
    retired: bool
    seasons: list[LeagueSeason]
    subscribed: bool
    success: bool


LookupCountriesResponse = list[LookupCountry]


LookupDriversResponse = list[LookupDriver]


class LookupFlairsResponse(BaseModel):
    flairs: list[Flair]
    success: bool


LookupGetResponse = list[Any]  # TODO: Define correctly


LookupLicensesResponse = list[LookupLicense]


class MemberAwardInstancesResponse(BaseModel):
    achievement: bool
    award_count: int
    award_id: int
    awards: list[MemberAwardBase]
    cust_id: int
    description: str | None = None
    group_name: str | None = None
    has_pdf: bool
    icon_background_color: str | None = None
    icon_url_large: str | None = None
    icon_url_small: str | None = None
    icon_url_unawarded: str | None = None
    name: str | None = None
    weight: int


MemberAwardsResponse = list[MemberAward]


class MemberChartDataResponse(BaseModel):
    blackout: bool
    category_id: int
    chart_type: int
    cust_id: int
    data: list[ValueWhenPair]
    success: bool


class MemberGetResponse(BaseModel):
    cust_ids: list[int]
    members: list[Member]
    success: bool


MemberInfoResponse = MemberInfo


MemberParticipationCreditsResponse = list[Any]  # TODO: Define correctly


class MemberProfileResponse(BaseModel):
    activity: MemberActivity | None = None
    cust_id: int
    disabled: bool
    follow_counts: MemberFollowCounts
    image_url: str
    is_generic_image: bool
    license_history: list[MemberLicenseHistoryItem]
    member_info: MemberProfileMemberInfo
    recent_awards: list[MemberAward]
    recent_events: list[MemberRecentEvent]
    success: bool


ResultsEventLogResponse = list[ResultEventLog]


class ResultsGetResponse(Result):
    pass


ResultsLapChartDataResponse = list[ChartLap]


ResultsLapDataResponse = list[Lap]


ResultsSearchSeriesResponse = list[SeriesResult]

ResultsSearchHostedResponse = list[HostedResult]


class ResultsSeasonResultsResponse(BaseModel):
    event_type: int | None = None
    race_week_num: None = None
    results_list: list[SeasonResult]
    season_id: int
    success: bool


class SeasonListResponse(BaseModel):
    season_quarter: int
    season_year: int
    seasons: list[Season]


class SeasonRaceGuideResponse(BaseModel):
    block_begin_time: str
    block_end_time: str
    sessions: list[RaceGuideSession]
    subscribed: bool
    success: bool


class SeasonSpectatorSubsessionidsResponse(BaseModel):
    event_types: list[int]
    subsession_ids: list[int]
    success: bool


class SeasonSpectatorSubsessionidsDetailResponse(BaseModel):
    event_types: list[int]
    season_ids: list[int]
    subsessions: list[Subsession]
    success: bool


SeriesAssetsResponse = dict[str, SeriesAsset]


SeriesGetResponse = list[BaseSeries]


SeriesWithAssetResponse = list[SeriesWithAsset]


class SeriesPastSeasonsResponse(BaseModel):
    series: PastSeasonSeries
    series_id: int
    success: bool


class SeriesSeasonListResponse(BaseModel):
    seasons: list[SeriesSeason]


class SeriesSeasonScheduleResponse(BaseModel):
    schedules: list[Schedule]
    season_id: int
    success: bool


SeriesSeasonsResponse = list[SeriesSeasonsResponseItem]


SeriesStatsSeriesResponse = list[SeriesStatsSeriesResponseItem]


class SessionRegDriversListResponse(BaseModel):
    entries: list[Entry]
    subscribed: bool
    subsession_id: int
    success: bool


class StatsMemberBestsResponse(BaseModel):
    bests: list[Best]
    car_id: int
    cars_driven: list[CarInClass]
    cust_id: int


class StatsMemberCareerResponse(BaseModel):
    cust_id: int
    stats: list[CareerStat]


class StatsMemberDivisionResponse(BaseModel):
    division: int
    event_type: int
    projected: bool
    season_id: int
    success: bool


class StatsMemberRecapResponse(BaseModel):
    cust_id: int
    season: Any | None = None  # TODO: Define correctly
    stats: RecapStats
    success: bool
    year: int


class StatsMemberRecentRacesResponse(BaseModel):
    cust_id: int
    races: list[StatRecentRace]


class StatsMemberSummaryResponse(BaseModel):
    cust_id: int
    this_year: StatThisYear


class StatsMemberYearlyResponse(BaseModel):
    cust_id: int
    stats: list[YearStat]


StatsSeasonDriverStandingsResponse = list[SeasonDriverStandings]


StatsSeasonQualifyResultsResponse = list[SeasonQualifyResult]


StatsSeasonSupersessionStandingsResponse = list[ResultEventLog]


StatsSeasonTeamStandingsResponse = list[SeasonTeamStandings]


StatsSeasonTtResultsResponse = list[SeasonTTResult]


StatsSeasonTtStandingsResponse = Optional[list[SeasonTTStandings]]


StatsWorldRecordsResponse = list[StatWorldRecord]


class TeamGetResponse(BaseModel):
    about: str
    created: str
    hidden: bool
    is_admin: bool
    is_applicant: bool
    is_default: bool
    is_ignored: bool
    is_invite: bool
    is_member: bool
    is_owner: bool
    message: str
    owner: Owner
    owner_id: int
    pending_requests: list[Any]  # TODO: Define correctly
    private_wall: bool
    recruiting: bool
    roster: list[Owner]
    roster_count: int
    suit: SimpleSuit
    tags: Tags
    team_applications: list[Any]  # TODO: Define correctly
    team_id: int
    team_name: str
    url: str


TeamMembershipResponse = list[TeamMembership]


TimeAttackMemberSeasonResultsResponse = list[Any]  # TODO: Define correctly


TrackAssetsResponse = dict[str, TrackAsset]


TrackGetResponse = list[TrackGetResponseItem]


TrackWithAssetResponse = list[TrackWithAsset]
