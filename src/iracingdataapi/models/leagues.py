from typing import Any

from pydantic import BaseModel

from .cars import CarInClass
from .common import Helmet, Image, Member, MemberWithHelmet, Tags
from .members import MemberLicense
from .weather import SimpleWeather


class LeagueOwner(BaseModel):
    car_number: None = None
    cust_id: int
    display_name: str
    helmet: Helmet
    nick_name: None = None


class LeagueApplication(MemberWithHelmet):
    admins: list[Member]
    application_id: int
    initiated: str
    league_id: int


class LeaguePendingRequest(MemberWithHelmet):
    initiated: str
    league_id: int
    revoked: bool


class RosterItem(MemberWithHelmet):
    admin: bool
    car_number: str | None
    league_mail_opt_out: bool
    league_member_since: str
    league_pm_opt_out: bool
    nick_name: str | None
    licenses: list[MemberLicense] = []
    owner: bool


class LeagueCar(BaseModel):
    car_class_id: int
    car_class_name: str
    car_id: int
    car_name: str


class SimpleLeague(BaseModel):
    about: str | None = None
    created: str
    is_admin: bool
    is_member: bool
    league_id: int
    league_name: str
    owner: LeagueOwner
    owner_id: int
    recruiting: bool
    roster_count: int
    url: str | None = None


class LeagueDirectoryItem(SimpleLeague):
    pending_application: bool
    pending_invitation: bool


class League(SimpleLeague):
    hidden: bool
    image: Image
    is_applicant: bool
    is_ignored: bool
    is_invite: bool
    is_owner: bool
    league_applications: list[LeagueApplication]
    message: str | None = None
    pending_requests: list[LeaguePendingRequest]
    private_results: bool
    private_roster: bool
    private_schedule: bool
    private_wall: bool
    roster: list[RosterItem]
    tags: Tags


class LeaguePointsSystem(BaseModel):
    description: str
    iracing_system: bool
    league_id: int
    name: str
    points_system_id: int
    retired: bool


class LeagueMembership(BaseModel):
    admin: bool
    car_number: str | None
    league_id: int
    league_mail_opt_out: bool
    league_name: str
    league_pm_opt_out: bool
    nick_name: None = None
    owner: bool


class LeagueSessionWeather(SimpleWeather):
    weather_var_initial: int
    weather_var_ongoing: int


class DriverStanding(BaseModel):
    average_finish: int
    average_start: int
    base_points: int
    car_number: str | None
    driver: MemberWithHelmet
    driver_nickname: str | None
    negative_adjustments: int
    position: int
    positive_adjustments: int
    rownum: int
    total_adjustments: int
    total_points: int
    wins: int


class LeagueStandings(BaseModel):
    driver_standings: list[DriverStanding]
    driver_standings_csv_url: str
    team_standings: list[Any]  # TODO: Define TeamStanding model if needed
    team_standings_csv_url: str


class LeagueCarClass(BaseModel):
    car_class_id: int
    cars_in_class: list[CarInClass]
    name: str


class LeagueSeason(BaseModel):
    active: bool
    driver_points_car_classes: list[LeagueCarClass]
    hidden: bool
    league_id: int
    no_drops_on_or_after_race_num: int
    num_drops: int
    points_cars: list[CarInClass]
    points_system_desc: str
    points_system_id: int
    points_system_name: str
    season_id: int
    season_name: str
    team_points_car_classes: list[LeagueCarClass]
