"""Download, cache, and convert WeatherAPI.com icon images for Tkinter."""

from __future__ import annotations

from io import BytesIO

import requests
from PIL import Image, ImageTk


class WeatherIconRepository:
    """Cache icon bytes across requests and Tk images across rerenders."""

    def __init__(self, session: requests.Session | None = None, timeout: int = 6) -> None:
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "ModularWeatherAPIApp/2.0")
        self.timeout = timeout
        self._bytes: dict[str, bytes] = {}
        self._photos: dict[tuple[str, tuple[int, int]], ImageTk.PhotoImage] = {}

    def prefetch(self, icon_urls: set[str]) -> None:
        """Download missing icons; safe to call from a worker thread."""
        for url in icon_urls:
            if not url or url in self._bytes:
                continue
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200 and response.content:
                    self._bytes[url] = response.content
            except requests.RequestException:
                continue

    def photo(self, icon_url: str, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        """Create a Tk image on the GUI thread, returning None on invalid image data."""
        key = (icon_url, size)
        if key in self._photos:
            return self._photos[key]
        data = self._bytes.get(icon_url)
        if not data:
            return None
        try:
            image = Image.open(BytesIO(data)).convert("RGBA")
            image = image.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None
        self._photos[key] = photo
        return photo
