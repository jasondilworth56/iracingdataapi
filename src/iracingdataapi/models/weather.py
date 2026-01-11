from pydantic import BaseModel


class WeatherSummary(BaseModel):
    max_precip_rate: float | None = None
    max_precip_rate_desc: str
    precip_chance: float
    skies_high: int | None = None
    skies_low: int | None = None
    temp_high: float | None = None
    temp_low: float | None = None
    temp_units: int | None = None
    wind_dir: int | None = None
    wind_high: float | None = None
    wind_low: float | None = None
    wind_units: int | None = None


class ForecastOptions(BaseModel):
    forecast_type: int
    precipitation: int
    skies: int
    stop_precip: int
    temperature: int
    weather_seed: int
    wind_dir: int
    wind_speed: int


class SimpleWeather(BaseModel):
    allow_fog: bool
    fog: int | None = None
    precip_option: int
    rel_humidity: int
    skies: int
    temp_units: int
    temp_value: int
    track_water: int
    type: int | None = None
    version: int
    weather_summary: WeatherSummary | None = None
    wind_dir: int
    wind_units: int
    wind_value: int


class Weather(SimpleWeather):
    forecast_options: ForecastOptions | None = None
    simulated_start_time: str
    simulated_time_multiplier: int
    simulated_time_offsets: list[int]
    time_of_day: int
    weather_url: str | None = None
