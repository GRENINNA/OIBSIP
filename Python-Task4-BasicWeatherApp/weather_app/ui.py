"""Responsive Tkinter interface for current weather and forecasts."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk

from .api import WeatherClient
from .errors import WeatherAppError
from .icons import WeatherIconRepository
from .location import DetectedLocation, IPInfoClient
from .models import (
    CurrentWeather,
    DailyForecast,
    ForecastPoint,
    WeatherReport,
    celsius_to_fahrenheit,
    metres_per_second_to_mph,
)


APP_TITLE = "Weather Now"


class WeatherApp:
    """Coordinate form input, background requests, and weather rendering."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.report: WeatherReport | None = None
        self.unit = "C"
        self.icons = WeatherIconRepository()
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.api_key_var = tk.StringVar(value=os.getenv("WEATHERAPI_KEY", ""))
        self.location_var = tk.StringVar()
        self.error_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Enter a city or ZIP code to begin.")
        self.location_name_var = tk.StringVar(value="No weather loaded")
        self.observed_var = tk.StringVar(
            value="Add a WeatherAPI.com key and search for a location."
        )
        self.temperature_var = tk.StringVar(value="—")
        self.condition_var = tk.StringVar(value="Current conditions will appear here")
        self.details_var = tk.StringVar(value="Humidity —   •   Wind —   •   Feels like —")

        self._configure_window()
        self._configure_styles()
        self._build_interface()
        self.root.after(100, self._poll_results)

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("1120x820")
        self.root.minsize(920, 700)
        self.root.configure(bg="#EAF2F8")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#EAF2F8")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("Forecast.TFrame", background="#F8FAFC", relief="solid", borderwidth=1)
        style.configure(
            "Title.TLabel",
            background="#EAF2F8",
            foreground="#0F172A",
            font=("Segoe UI", 24, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#EAF2F8",
            foreground="#475569",
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background="#FFFFFF",
            foreground="#0F172A",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "CardText.TLabel",
            background="#FFFFFF",
            foreground="#475569",
            font=("Segoe UI", 10),
        )
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook", background="#EAF2F8", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(16, 8))

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=22, style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(5, weight=1)

        header = ttk.Frame(container, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.unit_button = ttk.Button(header, text="Use °F", command=self.toggle_unit)
        self.unit_button.grid(row=0, column=1, sticky="e")
        ttk.Label(
            container,
            text="Live current conditions and WeatherAPI.com forecasts.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        self._build_search_card(container)

        self.error_label = tk.Label(
            container,
            textvariable=self.error_var,
            bg="#FEE2E2",
            fg="#991B1B",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=12,
            pady=8,
        )
        self.error_label.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self.error_label.grid_remove()

        self._build_current_card(container)
        self._build_forecast_notebook(container)

        footer = ttk.Frame(container, style="App.TFrame")
        footer.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="Weather data: WeatherAPI.com",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="e")

        self.root.bind("<Return>", lambda _event: self.fetch_weather())
        self.location_entry.focus_set()

    def _build_search_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=16, style="Card.TFrame")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="WeatherAPI.com API key", style="CardText.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )
        self.api_key_entry = ttk.Entry(card, textvariable=self.api_key_var, show="•")
        self.api_key_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(card, text="City or ZIP code", style="CardText.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )
        self.location_entry = ttk.Entry(card, textvariable=self.location_var)
        self.location_entry.grid(row=1, column=1, sticky="ew", pady=4)
        self.fetch_button = ttk.Button(
            card,
            text="Get Weather",
            command=self.fetch_weather,
            style="Primary.TButton",
        )
        self.fetch_button.grid(row=1, column=2, padx=(10, 0), pady=4)
        self.locate_button = ttk.Button(
            card, text="Use My Location", command=self.detect_location
        )
        self.locate_button.grid(row=1, column=3, padx=(8, 0), pady=4)

        ttk.Label(
            card,
            text="Enter a city, postal code, or coordinates — for example Delhi, 602024, or 28.61,77.21.",
            style="CardText.TLabel",
        ).grid(row=2, column=1, columnspan=3, sticky="w", pady=(4, 0))

    def _build_current_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        card.columnconfigure(1, weight=1)

        self.current_icon = tk.Label(
            card,
            text="☁",
            bg="#FFFFFF",
            fg="#64748B",
            font=("Segoe UI Symbol", 44),
            width=3,
        )
        self.current_icon.grid(row=0, column=0, rowspan=4, padx=(0, 18))
        ttk.Label(card, textvariable=self.location_name_var, style="CardTitle.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(card, textvariable=self.observed_var, style="CardText.TLabel").grid(
            row=1, column=1, sticky="w", pady=(2, 4)
        )
        self.temperature_label = tk.Label(
            card,
            textvariable=self.temperature_var,
            bg="#FFFFFF",
            fg="#0F172A",
            font=("Segoe UI", 25, "bold"),
        )
        self.temperature_label.grid(row=0, column=2, rowspan=2, sticky="e", padx=(20, 0))
        ttk.Label(card, textvariable=self.condition_var, style="CardTitle.TLabel").grid(
            row=2, column=1, sticky="w"
        )
        ttk.Label(card, textvariable=self.details_var, style="CardText.TLabel").grid(
            row=3, column=1, columnspan=2, sticky="w", pady=(4, 0)
        )

    def _build_forecast_notebook(self, container: ttk.Frame) -> None:
        notebook = ttk.Notebook(container)
        notebook.grid(row=5, column=0, sticky="nsew")
        self.hourly_frame = ttk.Frame(notebook, padding=14, style="Card.TFrame")
        self.daily_frame = ttk.Frame(notebook, padding=14, style="Card.TFrame")
        notebook.add(self.hourly_frame, text="Next 6 Hours")
        notebook.add(self.daily_frame, text="Daily Forecast")
        self._show_forecast_placeholder()

    def fetch_weather(self) -> None:
        location = self.location_var.get().strip()
        api_key = self.api_key_var.get().strip()
        if not location:
            self._show_error("Enter a city name or ZIP code.")
            return
        if not api_key:
            self._show_error("Enter your WeatherAPI.com API key first.")
            return

        self._clear_error()
        self._set_busy(True, f"Loading weather for {location}…")
        threading.Thread(
            target=self._weather_worker,
            args=(api_key, location),
            daemon=True,
        ).start()

    def _weather_worker(self, api_key: str, location: str) -> None:
        try:
            report = WeatherClient(api_key).get_weather(location)
            self.icons.prefetch(report.icon_urls)
            self.result_queue.put(("weather", report))
        except WeatherAppError as error:
            self.result_queue.put(("error", str(error)))
        except Exception:
            self.result_queue.put(
                ("error", "An unexpected error occurred while loading the weather.")
            )

    def detect_location(self) -> None:
        self._clear_error()
        self._set_busy(True, "Detecting your approximate city from your IP address…")
        threading.Thread(target=self._location_worker, daemon=True).start()

    def _location_worker(self) -> None:
        try:
            detected = IPInfoClient().detect()
            self.result_queue.put(("location", detected))
        except WeatherAppError as error:
            self.result_queue.put(("error", str(error)))
        except Exception:
            self.result_queue.put(
                ("error", "An unexpected error occurred during location detection.")
            )

    def _poll_results(self) -> None:
        try:
            while True:
                result_type, payload = self.result_queue.get_nowait()
                self._handle_result(result_type, payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_results)

    def _handle_result(self, result_type: str, payload: object) -> None:
        self._set_busy(False)
        if result_type == "error":
            self._show_error(str(payload))
            return
        if result_type == "location" and isinstance(payload, DetectedLocation):
            self.location_var.set(payload.weather_query)
            self.status_var.set(f"Detected {payload.display_name}. Loading weather…")
            self.root.after_idle(self.fetch_weather)
            return
        if result_type == "weather" and isinstance(payload, WeatherReport):
            self.report = payload
            self._render_report()
            status = (
                f"Weather updated at "
                f"{payload.current.observed_at.strftime('%I:%M %p')} local time."
            )
            if payload.provider_notice:
                status = f"{status} {payload.provider_notice}"
            self.status_var.set(status)

    def toggle_unit(self) -> None:
        self.unit = "F" if self.unit == "C" else "C"
        self.unit_button.configure(text="Use °C" if self.unit == "F" else "Use °F")
        if self.report is not None:
            self._render_report()

    def _render_report(self) -> None:
        if self.report is None:
            return
        current = self.report.current
        self.location_name_var.set(current.location.display_name)
        self.observed_var.set(
            f"Observed {current.observed_at.strftime('%A, %d %B at %I:%M %p')}"
        )
        celsius = f"{current.temperature_c:.1f}°C"
        fahrenheit = f"{celsius_to_fahrenheit(current.temperature_c):.1f}°F"
        self.temperature_var.set(
            f"{fahrenheit} / {celsius}" if self.unit == "F" else f"{celsius} / {fahrenheit}"
        )
        self.condition_var.set(current.description)
        self.details_var.set(
            f"Feels like {self._temperature(current.feels_like_c)}   •   "
            f"Humidity {current.humidity}%   •   Wind {self._wind(current.wind_mps)}"
        )
        self._set_icon(self.current_icon, current.icon_url, (100, 100), "☁")
        self._render_hourly(self.report.hourly)
        self._render_daily(self.report.daily)

    def _render_hourly(self, points: tuple[ForecastPoint, ...]) -> None:
        self._clear_children(self.hourly_frame)
        if not points:
            ttk.Label(
                self.hourly_frame,
                text="No forecast intervals were returned for the next six hours.",
                style="CardText.TLabel",
            ).grid(row=0, column=0, sticky="w")
            return
        for column, point in enumerate(points):
            self.hourly_frame.columnconfigure(column, weight=1)
            card = ttk.Frame(self.hourly_frame, padding=16, style="Forecast.TFrame")
            card.grid(row=0, column=column, sticky="nsew", padx=6)
            self._forecast_label(card, point.forecast_at.strftime("%I:%M %p"), 0, bold=True)
            icon = tk.Label(card, text="☁", bg="#F8FAFC", font=("Segoe UI Symbol", 26))
            icon.grid(row=1, column=0, pady=3)
            self._set_icon(icon, point.icon_url, (64, 64), "☁")
            self._forecast_label(card, self._temperature(point.temperature_c), 2, bold=True)
            self._forecast_label(card, point.description, 3)
            self._forecast_label(
                card,
                f"Rain {point.precipitation_probability:.0%}  •  Wind {self._wind(point.wind_mps)}",
                4,
            )

    def _render_daily(self, days: tuple[DailyForecast, ...]) -> None:
        self._clear_children(self.daily_frame)
        if not days:
            ttk.Label(
                self.daily_frame,
                text="No daily forecast data was returned.",
                style="CardText.TLabel",
            ).grid(row=0, column=0, sticky="w")
            return
        for column, day in enumerate(days):
            self.daily_frame.columnconfigure(column, weight=1)
            card = ttk.Frame(self.daily_frame, padding=12, style="Forecast.TFrame")
            card.grid(row=0, column=column, sticky="nsew", padx=4)
            self._forecast_label(card, day.forecast_date.strftime("%A"), 0, bold=True)
            self._forecast_label(card, day.forecast_date.strftime("%d %b"), 1)
            icon = tk.Label(card, text="☁", bg="#F8FAFC", font=("Segoe UI Symbol", 24))
            icon.grid(row=2, column=0, pady=2)
            self._set_icon(icon, day.icon_url, (58, 58), "☁")
            self._forecast_label(
                card,
                f"{self._temperature(day.maximum_c)} / {self._temperature(day.minimum_c)}",
                3,
                bold=True,
            )
            self._forecast_label(card, day.description, 4)
            self._forecast_label(
                card,
                f"Rain {day.precipitation_probability:.0%}  •  Humidity {day.humidity}%",
                5,
            )

    @staticmethod
    def _forecast_label(
        parent: ttk.Frame, text: str, row: int, bold: bool = False
    ) -> None:
        tk.Label(
            parent,
            text=text,
            bg="#F8FAFC",
            fg="#0F172A" if bold else "#475569",
            font=("Segoe UI", 10, "bold" if bold else "normal"),
            wraplength=170,
        ).grid(row=row, column=0, pady=2)

    def _set_icon(
        self,
        label: tk.Label,
        icon_url: str,
        size: tuple[int, int],
        fallback: str,
    ) -> None:
        photo = self.icons.photo(icon_url, size)
        if photo is None:
            label.configure(image="", text=fallback)
            label.image = None  # type: ignore[attr-defined]
        else:
            label.configure(image=photo, text="")
            label.image = photo  # type: ignore[attr-defined]

    def _temperature(self, celsius: float) -> str:
        if self.unit == "F":
            return f"{celsius_to_fahrenheit(celsius):.0f}°F"
        return f"{celsius:.0f}°C"

    def _wind(self, metres_per_second: float) -> str:
        if self.unit == "F":
            return f"{metres_per_second_to_mph(metres_per_second):.1f} mph"
        return f"{metres_per_second:.1f} m/s"

    def _show_forecast_placeholder(self) -> None:
        for frame in (self.hourly_frame, self.daily_frame):
            ttk.Label(
                frame,
                text="Forecast data will appear after a successful search.",
                style="CardText.TLabel",
            ).grid(row=0, column=0, sticky="w")

    @staticmethod
    def _clear_children(frame: ttk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        state = ["disabled"] if busy else ["!disabled"]
        self.fetch_button.state(state)
        self.locate_button.state(state)
        if status:
            self.status_var.set(status)

    def _show_error(self, message: str) -> None:
        self.error_var.set(message)
        self.error_label.grid()
        self.status_var.set("Request could not be completed.")

    def _clear_error(self) -> None:
        self.error_var.set("")
        self.error_label.grid_remove()
