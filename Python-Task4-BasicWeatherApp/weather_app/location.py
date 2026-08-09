"""Optional IP-based location detection through IPinfo."""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from .errors import NetworkError, ResponseFormatError, ServiceError


IPINFO_URL = "https://ipinfo.io/json"


@dataclass(frozen=True)
class DetectedLocation:
    city: str
    region: str
    country: str

    @property
    def weather_query(self) -> str:
        return f"{self.city},{self.country}" if self.country else self.city

    @property
    def display_name(self) -> str:
        parts = [part for part in (self.city, self.region, self.country) if part]
        return ", ".join(parts)


class IPInfoClient:
    """Detect an approximate city from the user's public IP address."""

    def __init__(
        self,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: int = 8,
    ) -> None:
        self.token = token if token is not None else os.getenv("IPINFO_TOKEN", "")
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "ModularWeatherApp/1.0")
        self.timeout = timeout

    def detect(self) -> DetectedLocation:
        params = {"token": self.token} if self.token else None
        try:
            response = self.session.get(IPINFO_URL, params=params, timeout=self.timeout)
        except requests.Timeout as error:
            raise NetworkError("Automatic location detection timed out.") from error
        except requests.RequestException as error:
            raise NetworkError(
                "Could not connect to the automatic location service."
            ) from error

        if response.status_code == 429:
            raise ServiceError("The IP location request limit was reached.")
        if not 200 <= response.status_code < 300:
            raise ServiceError(
                "Automatic location detection is unavailable. Enter a city manually."
            )
        try:
            payload = response.json()
        except ValueError as error:
            raise ResponseFormatError("The IP location response was unreadable.") from error

        city = str(payload.get("city", "")).strip()
        if not city:
            raise ResponseFormatError(
                "IPinfo did not return a city. Enter one manually or configure IPINFO_TOKEN."
            )
        return DetectedLocation(
            city=city,
            region=str(payload.get("region", "")).strip(),
            country=str(payload.get("country", "")).strip(),
        )
