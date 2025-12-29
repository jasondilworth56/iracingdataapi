from pydantic import BaseModel

from src.iracingdataapi.models.common import MemberWithHelmet


class LookupCountry(BaseModel):
    country_code: str
    country_name: str


class LookupDriver(MemberWithHelmet):
    profile_disabled: bool


class Flair(BaseModel):
    country_code: str | None = None
    flair_id: int
    flair_name: str
    flair_shortname: str | None = None
    seq: int


class LicenseLevel(BaseModel):
    color: str
    license: str
    license_group: int
    license_id: int
    license_letter: str
    short_name: str


class LookupLicense(BaseModel):
    group_name: str
    levels: list[LicenseLevel]
    license_group: int
    min_num_races: int | None
    min_num_tt: int | None
    min_sr_to_fast_track: int | None
    participation_credits: int
