from typing import Any, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

from .common import MemberWithHelmet, Suit
from .tracks import Track


class MemberAwardBase(BaseModel):
    achievement: bool
    award_count: int
    award_date: str | None = None
    award_id: int
    award_order: int
    awarded_description: str | None = None
    cust_id: int
    display_date: str | None = None
    member_award_id: int
    subsession_id: int | None = None
    viewed: bool | None = None


class MemberAward(MemberAwardBase):
    description: str | None = None
    group_name: str
    has_pdf: bool
    icon_background_color: str | None = None
    icon_url_large: str
    icon_url_small: str
    icon_url_unawarded: str
    name: str
    progress: int | None = None
    progress_label: str | None = None
    progress_text: str | None = None
    progress_text_label: str | None = None
    threshold: int | None = None
    weight: int


class Member(MemberWithHelmet):
    ai: bool
    flair_id: int
    flair_name: str
    flair_shortname: str
    last_login: str
    member_since: str


class MemberAccount(BaseModel):
    country_rules: None = None
    ir_credits: int
    ir_dollars: int
    status: str


class MemberPackage(BaseModel):
    content_ids: list[int]
    package_id: int


class SimpleMemberLicense(BaseModel):
    category: str
    category_id: int
    color: str = ""
    group_name: str
    irating: int
    license_level: int
    safety_rating: float


class StatMemberLicense(SimpleMemberLicense):
    group_id: int
    tt_rating: int


class MemberLicense(StatMemberLicense):
    category_name: str
    cpi: float
    mpr_num_races: int
    mpr_num_tts: int
    pro_promotable: bool = False
    seq: int


class DriverFromCSV(BaseModel):
    driver: str
    custid: int
    location: str
    club_name: str
    starts: int
    wins: int
    avg_start_pos: int
    avg_finish_pos: int
    avg_points: int
    top25pcnt: int
    laps: int
    lapslead: int
    avg_inc: float
    class_: str = Field(alias="class")
    irating: int
    ttrating: int
    tot_clubpoints: int
    champpoints: int


class SimpleMemberInfo(MemberWithHelmet):
    flair_id: int
    flair_name: str
    flair_shortname: str
    last_login: str
    member_since: str


class MemberInfo(SimpleMemberInfo):
    account: MemberAccount
    alpha_tester: bool
    broadcaster: bool
    car_packages: list[MemberPackage]
    connection_type: str
    dev: bool
    download_server: str
    first_name: str
    flags: int
    flags_hex: str
    flair_country_code: str
    has_additional_content: bool
    has_read_comp_rules: bool
    has_read_nda: bool
    has_read_pp: bool
    has_read_tc: bool
    hundred_pct_club: bool
    last_name: str
    last_season: int
    licenses: dict[
        Literal[
            "dirt_oval",
            "dirt_road",
            "formula_car",
            "oval",
            "sports_car",
        ],
        MemberLicense,
    ]
    on_car_name: str
    other_owned_packages: list[int]
    rain_tester: bool
    read_comp_rules: str
    read_pp: str
    read_tc: str
    restrictions: dict[str, Any]  # TODO: Define correctly
    suit: Suit
    track_packages: list[MemberPackage]
    twenty_pct_discount: bool


class MemberProfileMemberInfo(SimpleMemberInfo):
    ai: bool
    country: str
    country_code: str
    licenses: list[MemberLicense]


class MemberActivity(BaseModel):
    consecutive_weeks: int
    most_consecutive_weeks: int
    prev_30days_count: int
    recent_30days_count: int


class MemberFollowCounts(BaseModel):
    followers: int
    follows: int


class MemberLicenseHistoryItem(BaseModel):
    category: str
    category_id: int
    category_name: str
    color: str
    cpi: float
    group_id: int
    group_name: str
    irating: int
    license_level: int
    safety_rating: float
    seq: int
    tt_rating: int


class MiniMemberInfo(MemberWithHelmet):
    ai: bool
    country: str
    country_code: str
    flair_id: int
    flair_name: str
    flair_shortname: str
    last_login: str
    licenses: list[MemberLicense]
    member_since: str


class MemberRecentEvent(BaseModel):
    best_lap_time: int
    car_id: int
    car_name: str
    event_id: int
    event_name: str
    event_type: str
    finish_position: int
    logo_url: Optional[str] = None
    percent_rank: int
    simsession_type: int
    start_time: str
    starting_position: int
    subsession_id: int
    track: Track
