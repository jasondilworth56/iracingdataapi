from pydantic import BaseModel

from .common import Helmet


class Lap(BaseModel):
    ai: bool
    car_number: str
    cust_id: int
    display_name: str
    flags: int
    group_id: int
    helmet: Helmet
    incident: bool
    lap_events: list[str]
    lap_number: int
    lap_time: int
    license_level: int
    name: str
    personal_best_lap: bool
    session_start_time: None = None
    session_time: int
    team_fastest_lap: bool


class ChartLap(Lap):
    fastest_lap: bool
    interval: int | None
    interval_units: str | None
    lap_position: int

    license_level: int
    name: str | None = None
    personal_best_lap: bool
    session_start_time: None = None
    session_time: int
    team_fastest_lap: bool
