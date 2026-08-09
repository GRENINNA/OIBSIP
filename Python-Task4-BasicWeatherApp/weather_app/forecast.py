"""Parse WeatherAPI.com current, hourly, and daily forecast data."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .errors import ResponseFormatError
from .models import (
    Coordinates,
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    ResolvedLocation,
    WeatherReport,
)


JsonObject = dict[str, Any]


def _icon_url(condition: Any) -> str:
    if not isinstance(condition, dict):
        raise ResponseFormatError("Weather condition details were missing.")
    value = str(condition.get("icon", "")).strip()
    if value.startswith("//"):
        return f"https:{value}"
    if value.startswith("http://"):
        return f"https://{value[7:]}"
    return value


def _condition_text(condition: Any) -> str:
    if not isinstance(condition, dict):
        raise ResponseFormatError("Weather condition details were missing.")
    value = str(condition.get("text", "")).strip()
    if not value:
        raise ResponseFormatError("Weather condition text was missing.")
    return value


def _local_datetime(value: Any) -> datetime:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ResponseFormatError("A weather timestamp was invalid.") from error


def _probability(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value) / 100.0))
    except (TypeError, ValueError) as error:
        raise ResponseFormatError("A precipitation probability was invalid.") from error


def parse_current_weather(payload: JsonObject) -> CurrentWeather:
    """Convert WeatherAPI.com's location and current objects into a model."""
    try:
        location_payload = payload["location"]
        current_payload = payload["current"]
        condition = current_payload["condition"]
        location = ResolvedLocation(
            name=str(location_payload["name"]),
            country=str(location_payload.get("country", "")),
            coordinates=Coordinates(
                latitude=float(location_payload["lat"]),
                longitude=float(location_payload["lon"]),
            ),
        )
        return CurrentWeather(
            location=location,
            observed_at=_local_datetime(current_payload["last_updated"]),
            temperature_c=float(current_payload["temp_c"]),
            feels_like_c=float(current_payload["feelslike_c"]),
            humidity=int(current_payload["humidity"]),
            description=_condition_text(condition),
            wind_mps=float(current_payload.get("wind_kph", 0.0)) / 3.6,
            icon_url=_icon_url(condition),
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResponseFormatError):
            raise
        raise ResponseFormatError(
            "Current weather data was incomplete or invalid."
        ) from error


def parse_next_six_hours(
    payload: JsonObject, observed_at: datetime
) -> tuple[ForecastPoint, ...]:
    """Return the next six one-hour forecast entries after observation time."""
    try:
        forecast_days = payload["forecast"]["forecastday"]
        if not isinstance(forecast_days, list):
            raise TypeError("forecastday is not a list")
        end_time = observed_at + timedelta(hours=6)
        points: list[ForecastPoint] = []
        for forecast_day in forecast_days:
            for hour in forecast_day.get("hour", []):
                forecast_at = _local_datetime(hour["time"])
                if not observed_at < forecast_at <= end_time:
                    continue
                condition = hour["condition"]
                points.append(
                    ForecastPoint(
                        forecast_at=forecast_at,
                        temperature_c=float(hour["temp_c"]),
                        minimum_c=float(hour["temp_c"]),
                        maximum_c=float(hour["temp_c"]),
                        humidity=int(hour["humidity"]),
                        description=_condition_text(condition),
                        wind_mps=float(hour.get("wind_kph", 0.0)) / 3.6,
                        precipitation_probability=_probability(
                            hour.get("chance_of_rain", 0)
                        ),
                        icon_url=_icon_url(condition),
                    )
                )
        return tuple(sorted(points, key=lambda point: point.forecast_at)[:6])
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResponseFormatError):
            raise
        raise ResponseFormatError(
            "Hourly forecast data was incomplete or invalid."
        ) from error


def parse_daily_forecasts(payload: JsonObject) -> tuple[DailyForecast, ...]:
    """Return up to five daily summaries supplied by the account's plan."""
    try:
        forecast_days = payload["forecast"]["forecastday"]
        if not isinstance(forecast_days, list):
            raise TypeError("forecastday is not a list")
        days: list[DailyForecast] = []
        for forecast_day in forecast_days[:5]:
            day = forecast_day["day"]
            condition = day["condition"]
            days.append(
                DailyForecast(
                    forecast_date=date.fromisoformat(str(forecast_day["date"])),
                    minimum_c=float(day["mintemp_c"]),
                    maximum_c=float(day["maxtemp_c"]),
                    humidity=int(round(float(day["avghumidity"]))),
                    description=_condition_text(condition),
                    precipitation_probability=_probability(
                        day.get("daily_chance_of_rain", 0)
                    ),
                    icon_url=_icon_url(condition),
                )
            )
        return tuple(days)
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResponseFormatError):
            raise
        raise ResponseFormatError(
            "Daily forecast data was incomplete or invalid."
        ) from error


def build_weather_report(
    payload: JsonObject, provider_notice: str = ""
) -> WeatherReport:
    current = parse_current_weather(payload)
    daily = parse_daily_forecasts(payload)
    if not provider_notice and len(daily) < 5:
        provider_notice = (
            f"WeatherAPI.com returned {len(daily)} forecast day(s) for this account."
        )
    return WeatherReport(
        current=current,
        hourly=parse_next_six_hours(payload, current.observed_at),
        daily=daily,
        provider_notice=provider_notice,
    )
