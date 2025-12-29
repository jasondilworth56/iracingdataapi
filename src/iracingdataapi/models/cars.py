from pydantic import BaseModel


class CarRule(BaseModel):
    rule_category: str
    text: str


class CarAsset(BaseModel):
    car_id: int
    car_rules: list[CarRule]
    detail_copy: str
    detail_screen_shot_images: str
    detail_techspecs_copy: str
    folder: str
    gallery_images: str | None
    gallery_prefix: None = None
    group_image: str | None
    group_name: None = None
    large_image: str
    logo: str | None
    small_image: str
    sponsor_logo: str | None
    template_path: str | None


class CarConfigDef(BaseModel):
    carcfg: int
    cfg_subdir: str | None
    custom_paint_ext: str | None
    name: str


class CarConfig(BaseModel):
    carcfg: int
    track_id: int | None = None
    track_type: int | None = None


class CarType(BaseModel):
    car_type: str


class PaintRule(BaseModel):
    AllowNumberColorChanges: bool
    AllowNumberFontChanges: bool
    Color1: str
    Color2: str
    Color3: str
    NumberColor1: str
    NumberColor2: str
    NumberColor3: str
    NumberFont: str
    PaintCarAvailable: bool
    PaintWheelAvailable: bool
    RimType: str
    RimTypeAvailable: bool
    RulesExplanation: str
    Sponsor1: str
    Sponsor1Available: bool
    Sponsor2: str
    Sponsor2Available: bool
    WheelColor: str


class RestrictedPaintRule(BaseModel):
    RestrictCustomPaint: bool | None = None


class SimpleCar(BaseModel):
    car_dirpath: str
    car_id: int
    rain_enabled: bool
    retired: bool


class LeagueSessionCar(BaseModel):
    car_class_id: int
    car_class_name: str
    car_id: int
    car_name: str
    max_dry_tire_sets: int
    max_pct_fuel_fill: int
    package_id: int
    power_adjust_pct: float
    qual_setup_filename: str | None = None
    qual_setup_id: int | None = None
    race_setup_filename: str | None = None
    race_setup_id: int | None = None
    weight_penalty_kg: int


class HostedCombinedSessionCar(BaseModel):
    car_id: int
    car_name: str
    package_id: int


class Car(SimpleCar):
    ai_enabled: bool
    allow_number_colors: bool
    allow_number_font: bool
    allow_sponsor1: bool
    allow_sponsor2: bool
    allow_wheel_color: bool
    award_exempt: bool
    car_config_defs: list[CarConfigDef]
    car_configs: list[CarConfig]
    car_make: str | None = None
    car_model: str | None = None
    car_name: str
    car_name_abbreviated: str
    car_types: list[CarType]
    car_weight: int
    categories: list[str]
    created: str
    first_sale: str
    folder: str
    forum_url: str | None = None
    free_with_subscription: bool
    has_headlights: bool
    has_multiple_dry_tire_types: bool
    has_rain_capable_tire_types: bool
    hp: int
    is_ps_purchasable: bool
    logo: str | None
    max_power_adjust_pct: int
    max_weight_penalty_kg: int
    min_power_adjust_pct: int
    package_id: int
    paint_rules: dict[str, PaintRule] | RestrictedPaintRule | None = None
    patterns: int
    price: float
    price_display: str | None = None
    search_filters: str
    site_url: str | None = None
    sku: int
    small_image: str
    sponsor_logo: str | None


class HostedResultCar(BaseModel):
    car_id: int
    car_name: str
    car_class_id: int
    car_class_name: str
    car_class_short_name: str
    car_name_abbreviated: str


class CarWithAsset(Car, CarAsset):
    pass


class CarInClass(BaseModel):
    car_id: int
    car_name: str


class FavoriteCar(CarInClass):
    car_image: str


class SimpleCarClass(BaseModel):
    car_class_id: int
    name: str
    relative_speed: int
    short_name: str


class CarClass(SimpleCarClass):
    cars_in_class: list[SimpleCar]
    cust_id: int
    rain_enabled: bool


class RaceWeekCarClasses(BaseModel):
    car_class_ids: list[int]
    race_week_num: int


class Livery(BaseModel):
    car_id: int
    car_number: str
    color1: str
    color2: str
    color3: str
    number_color1: str
    number_color2: str
    number_color3: str
    number_font: int
    number_slant: int
    pattern: int
    rim_type: int
    sponsor1: int
    sponsor2: int
    wheel_color: str | None = None
