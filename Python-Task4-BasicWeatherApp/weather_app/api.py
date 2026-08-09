"""WeatherAPI.com forecast client and provider-specific error handling."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

from .errors import (
    APIKeyMissingError,
    AuthenticationError,
    LocationNotFoundError,
    NetworkError,
    PlanAccessError,
    RateLimitError,
    ResponseFormatError,
    ServiceError,
)
from .forecast import build_weather_report
from .models import WeatherReport


WEATHERAPI_BASE_URL = "https://api.weatherapi.com/v1"
DEFAULT_TIMEOUT = 10
REQUESTED_FORECAST_DAYS = 5
FREE_PLAN_FORECAST_DAYS = 3


def normalize_api_key(value: str) -> str:
    """Return only the key when a user pastes a key, key value, or API URL."""
    candidate = value.strip().strip("\"'").strip()

    if "://" in candidate:
        parsed = urlparse(candidate)
        query_values = parse_qs(parsed.query).get("key")
        if query_values:
            candidate = query_values[0]

    if candidate.lower().startswith("key="):
        candidate = candidate.split("=", 1)[1].split("&", 1)[0]

    return candidate.strip().strip("\"'").strip()


class WeatherClient:
    """Fetch current, hourly, and daily data from WeatherAPI.com."""

    def __init__(
        self,
        api_key: str,
        session: requests.Session | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = normalize_api_key(api_key)
        if not self.api_key:
            raise APIKeyMissingError(
                "Enter a WeatherAPI.com API key before requesting weather data."
            )
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "ModularWeatherAPIApp/2.0")
        self.timeout = timeout

    def get_weather(self, location_query: str) -> WeatherReport:
        query = location_query.strip()
        if query.lower().startswith("zip:"):
            query = query[4:].strip()
        if not query:
            raise LocationNotFoundError("Enter a city name or postal code.")

        provider_notice = ""
        try:
            payload = self._request_forecast(query, REQUESTED_FORECAST_DAYS)
        except PlanAccessError:
            payload = self._request_forecast(query, FREE_PLAN_FORECAST_DAYS)
            provider_notice = (
                "Your WeatherAPI.com plan returned a 3-day forecast; "
                "five days requires a plan with extended forecast access."
            )
        return build_weather_report(payload, provider_notice=provider_notice)

    def _request_forecast(self, query: str, days: int) -> dict[str, Any]:
        payload = self._request_json(
            f"{WEATHERAPI_BASE_URL}/forecast.json",
            {
                "key": self.api_key,
                "q": query,
                "days": days,
                "aqi": "no",
                "alerts": "no",
            },
        )
        if not isinstance(payload, dict):
            raise ResponseFormatError(
                "WeatherAPI.com returned an unexpected response format."
            )
        return payload

    def _request_json(self, url: str, params: dict[str, Any]) -> Any:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.Timeout as error:
            raise NetworkError(
                "The weather service timed out. Check your connection and try again."
            ) from error
        except requests.RequestException as error:
            raise NetworkError(
                "Could not connect to WeatherAPI.com. Check your internet connection."
            ) from error

        try:
            payload = response.json()
        except ValueError as error:
            raise ResponseFormatError(
                "WeatherAPI.com returned an unreadable response."
            ) from error

        if 200 <= response.status_code < 300:
            return payload

        error_code, detail = self._error_details(payload)
        detail_text = f": {detail}" if detail else ""

        if error_code in {1002, 2006} or response.status_code == 401:
            raise AuthenticationError(
                f"WeatherAPI.com rejected the API key{detail_text}. "
                "Copy only the key shown on your WeatherAPI.com account page."
            )
        if error_code == 2008:
            raise AuthenticationError(
                f"This WeatherAPI.com key has been disabled{detail_text}."
            )
        if error_code == 1006:
            raise LocationNotFoundError(
                "No matching location was found. Check the city or postal code."
            )
        if error_code == 2007 or response.status_code == 429:
            raise RateLimitError(
                "The WeatherAPI.com monthly request quota has been reached."
            )
        if error_code == 2009:
            raise PlanAccessError(
                "The WeatherAPI.com plan does not include the requested forecast range."
            )
        if response.status_code >= 500 or error_code == 9999:
            raise ServiceError(
                "WeatherAPI.com is temporarily unavailable. Please try again later."
            )
        raise ServiceError(
            f"WeatherAPI.com rejected the request "
            f"(HTTP {response.status_code}{detail_text})."
        )

    @staticmethod
    def _error_details(payload: Any) -> tuple[int | None, str]:
        if not isinstance(payload, dict) or not isinstance(payload.get("error"), dict):
            return None, ""
        error_payload = payload["error"]
        try:
            code = int(error_payload.get("code"))
        except (TypeError, ValueError):
            code = None
        message = str(error_payload.get("message", "")).strip().replace("\n", " ")
        return code, message[:180]
