from pydantic import BaseModel, Field


class SimpleTrack(BaseModel):
    track_id: int
    track_name: str


class TrackWithConfig(SimpleTrack):
    config_name: str | None = None


class Track(TrackWithConfig):
    category: str | None = None
    category_id: int | None = None


class FavoriteTrack(TrackWithConfig):
    track_logo: str


class SimpleTrackState(BaseModel):
    leave_marbles: bool
    practice_rubber: int | None = None


class TrackState(SimpleTrackState):
    practice_rubber: int
    qualify_rubber: int
    race_rubber: int
    warmup_rubber: int


class TrackMapLayers(BaseModel):
    active: str
    background: str
    inactive: str
    pitroad: str
    start_finish: str = Field(..., alias="start-finish")
    turns: str


class TrackAsset(BaseModel):
    coordinates: str
    detail_copy: str | None = None
    detail_techspecs_copy: str | None = None
    detail_video: None = None
    folder: str
    gallery_images: str | None = None
    gallery_prefix: str | None = None
    large_image: str
    logo: str
    north: str | None = None
    num_svg_images: int
    small_image: str
    track_id: int
    track_map: str
    track_map_layers: TrackMapLayers


class TrackWithAsset(Track, TrackAsset):
    pass


class TrackType(BaseModel):
    track_type: str


class TrackGetResponseItem(BaseModel):
    ai_enabled: bool
    allow_pitlane_collisions: bool
    allow_rolling_start: bool
    allow_standing_start: bool
    award_exempt: bool
    banking: str | None = None
    category: str
    category_id: int
    closes: str
    config_name: str | None = None
    corners_per_lap: int
    created: str
    first_sale: str
    folder: str
    free_with_subscription: bool
    fully_lit: bool
    grid_stalls: int
    has_opt_path: bool
    has_short_parade_lap: bool
    has_start_zone: bool
    has_svg_map: bool
    is_dirt: bool
    is_oval: bool
    is_ps_purchasable: bool
    lap_scoring: int
    latitude: float
    location: str
    logo: str
    longitude: float
    max_cars: int
    night_lighting: bool
    nominal_lap_time: float | None = None
    number_pitstalls: int
    opens: str
    package_id: int
    pit_road_speed_limit: int | None = None
    price: float
    price_display: str | None = None
    priority: int
    purchasable: bool
    qualify_laps: int
    rain_enabled: bool
    restart_on_left: bool
    retired: bool
    search_filters: str
    site_url: str | None = None
    sku: int
    small_image: str
    solo_laps: int
    start_on_left: bool
    supports_grip_compound: bool
    tech_track: bool
    time_zone: str
    track_config_length: float
    track_dirpath: str
    track_id: int
    track_name: str
    track_type: int
    track_type_text: str
    track_types: list[TrackType]
