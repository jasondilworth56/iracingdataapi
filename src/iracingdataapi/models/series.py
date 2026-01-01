from pydantic import BaseModel

from src.iracingdataapi.models.cars import SimpleCarClass
from src.iracingdataapi.models.common import AllowedLicense, LicenseGroupType, RaceWeek
from src.iracingdataapi.models.seasons import Season, SimpleSeason


class SeriesAsset(BaseModel):
    large_image: None = None
    logo: str
    series_copy: str
    series_id: int
    small_image: None = None


class BaseSeries(BaseModel):
    allowed_licenses: list[AllowedLicense]
    category: str
    category_id: int
    eligible: bool
    first_season: SimpleSeason
    forum_url: str | None = None
    max_starters: int
    min_starters: int
    oval_caution_type: int
    road_caution_type: int
    search_filters: str | None = None
    series_id: int
    series_name: str
    series_short_name: str


class SeriesWithAsset(BaseSeries, SeriesAsset):
    pass


class SeriesSeason(Season):
    series_name: None = None
    active: bool
    car_classes: list[SimpleCarClass]
    car_switching: bool
    has_supersessions: bool
    license_group_types: list[LicenseGroupType]
    race_weeks: list[RaceWeek]
    season_short_name: str


class PastSeasonSeries(BaseModel):
    active: bool
    allowed_licenses: list[AllowedLicense]
    category: str
    category_id: int
    fixed_setup: bool
    license_group: int
    license_group_types: list[LicenseGroupType]
    logo: str
    official: bool
    search_filters: str | None = None
    seasons: list[SeriesSeason]
    series_id: int
    series_name: str
    series_short_name: str
