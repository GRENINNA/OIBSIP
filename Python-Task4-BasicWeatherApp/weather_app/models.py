"""Typed data models and unit conversions used by the weather app."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


def celsius_to_fahrenheit(value: float) -> float:
    return (value * 9 / 5) + 32


def metres_per_second_to_mph(value: float) -> float:
    return value * 2.2369362921


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ResolvedLocation:
    name: str
    country: str
    coordinates: Coordinates

    @property
    def display_name(self) -> str:
        return f"{self.name}, {self.country}" if self.country else self.name


@dataclass(frozen=True)
class CurrentWeather:
    location: ResolvedLocation
    observed_at: datetime
    temperature_c: float
    feels_like_c: float
    humidity: int
    description: str
    wind_mps: float
    icon_url: str


@dataclass(frozen=True)
class ForecastPoint:
    forecast_at: datetime
    temperature_c: float
    minimum_c: float
    maximum_c: float
    humidity: int
    description: str
    wind_mps: float
    precipitation_probability: float
    icon_url: str


@dataclass(frozen=True)
class DailyForecast:
    forecast_date: date
    minimum_c: float
    maximum_c: float
    humidity: int
    description: str
    precipitation_probability: float
    icon_url: str


@dataclass(frozen=True)
class WeatherReport:
    current: CurrentWeather
    hourly: tuple[ForecastPoint, ...]
    daily: tuple[DailyForecast, ...]
    provider_notice: str = ""

    @property
    def icon_urls(self) -> set[str]:
        urls = {self.current.icon_url}
        urls.update(point.icon_url for point in self.hourly)
        urls.update(day.icon_url for day in self.daily)
        return {url for url in urls if url}
