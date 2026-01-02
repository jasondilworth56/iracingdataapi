from typing import Any

from pydantic import BaseModel

from .tracks import Track


class LabelIntValuePair(BaseModel):
    label: str
    value: int


class ValueWhenPair(BaseModel):
    value: int
    when: str


class SimpleSuit(BaseModel):
    color1: str
    color2: str
    color3: str
    pattern: int


class Suit(SimpleSuit):
    body_type: int


class Helmet(BaseModel):
    color1: str
    color2: str
    color3: str
    face_type: int
    helmet_type: int
    pattern: int


class Member(BaseModel):
    cust_id: int
    display_name: str


class MemberWithHelmet(Member):
    helmet: Helmet


class Admin(MemberWithHelmet):
    pass


class Owner(MemberWithHelmet):
    admin: bool
    owner: bool


class TeamMembership(BaseModel):
    admin: bool
    default_team: bool
    owner: bool
    team_id: int
    team_name: str


class Image(BaseModel):
    large_logo: str | None
    small_logo: str


class ServerFarm(BaseModel):
    display_name: str
    displayed: bool
    farm_id: int
    image_path: str


class AllowedLicense(BaseModel):
    group_name: str
    license_group: int
    max_license_level: int
    min_license_level: int


class LicenseGroupType(BaseModel):
    license_group_type: int


class SimpleEligibility(BaseModel):
    own_car: bool
    own_track: bool


class SessionEligibility(SimpleEligibility):
    can_drive: bool
    can_spot: bool
    can_watch: bool
    has_sess_password: bool
    needs_purchase: bool
    purchase_skus: list[int]
    registered: bool
    session_full: bool


class RaceWeek(BaseModel):
    race_week_num: int
    season_id: int
    track: Track


class Tag(BaseModel):
    tag_id: int
    tag_name: str


class CategorizedItem(BaseModel):
    category_id: int
    limit: int | None
    name: str
    tags: list[Tag]


class PendingRequest(MemberWithHelmet):
    initiated: str
    revoked: bool
    team_id: int


class Tags(BaseModel):
    categorized: list[CategorizedItem]
    not_categorized: list[Tag]
