"""BMI trend charts with Matplotlib and a dependency-free Tkinter fallback."""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk
from typing import Any, Iterable


@dataclass(frozen=True)
class TrendPoint:
    recorded_at: datetime
    bmi: float


def prepare_trend_points(records: Iterable[Any]) -> tuple[TrendPoint, ...]:
    """Validate and convert database records into chronological chart points."""
    points: list[TrendPoint] = []
    for record in records:
        try:
            recorded_at = datetime.fromisoformat(str(record["recorded_at"]))
            bmi = float(record["bmi"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("A saved BMI record contains invalid chart data.") from error
        if not math.isfinite(bmi) or bmi <= 0:
            raise ValueError("A saved BMI record contains an invalid BMI value.")
        points.append(TrendPoint(recorded_at=recorded_at, bmi=bmi))

    if not points:
        raise ValueError("At least one saved BMI record is required for a trend chart.")
    return tuple(sorted(points, key=lambda point: point.recorded_at))


def open_bmi_trend(
    parent: tk.Misc,
    user_name: str,
    records: Iterable[Any],
) -> str:
    """Open the best available chart and return the backend description."""
    points = prepare_trend_points(records)
    try:
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg,
            NavigationToolbar2Tk,
        )
        from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
        from matplotlib.figure import Figure
    except (ImportError, OSError):
        _open_tkinter_chart(parent, user_name, points)
        return "built-in Tkinter chart"

    graph_window = tk.Toplevel(parent)
    graph_window.title(f"BMI Trend - {user_name}")
    graph_window.geometry("800x520")
    graph_window.minsize(620, 420)

    dates = [point.recorded_at for point in points]
    bmis = [point.bmi for point in points]
    figure = Figure(figsize=(8, 4.8), dpi=100, layout="constrained")
    axis = figure.add_subplot()
    axis.plot(dates, bmis, color="#4F46E5", marker="o", linewidth=2)
    axis.axhspan(18.5, 25.0, color="#DCFCE7", alpha=0.75, label="Normal range")
    axis.axhline(18.5, color="#64748B", linewidth=0.8, linestyle="--")
    axis.axhline(25.0, color="#64748B", linewidth=0.8, linestyle="--")
    axis.axhline(30.0, color="#B91C1C", linewidth=0.8, linestyle="--")
    axis.set_title(f"BMI trend for {user_name}", fontsize=14, fontweight="bold")
    axis.set_xlabel("Date")
    axis.set_ylabel("BMI")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best")

    locator = AutoDateLocator()
    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(ConciseDateFormatter(locator))
    canvas = FigureCanvasTkAgg(figure, master=graph_window)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, graph_window, pack_toolbar=False)
    toolbar.update()
    toolbar.pack(side=tk.BOTTOM, fill=tk.X)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    return "Matplotlib chart"


def _open_tkinter_chart(
    parent: tk.Misc,
    user_name: str,
    points: tuple[TrendPoint, ...],
) -> None:
    """Open a responsive Canvas chart that requires no third-party library."""
    graph_window = tk.Toplevel(parent)
    graph_window.title(f"BMI Trend - {user_name}")
    graph_window.geometry("860x560")
    graph_window.minsize(640, 430)
    graph_window.configure(bg="#F3F4F6")

    container = ttk.Frame(graph_window, padding=18)
    container.pack(fill=tk.BOTH, expand=True)
    ttk.Label(
        container,
        text=f"BMI trend for {user_name}",
        font=("Segoe UI", 15, "bold"),
    ).pack(anchor="w")
    ttk.Label(
        container,
        text="Built-in chart mode - Matplotlib is not available to this Python interpreter.",
        foreground="#4B5563",
    ).pack(anchor="w", pady=(2, 10))

    canvas = tk.Canvas(
        container,
        background="#FFFFFF",
        highlightbackground="#CBD5E1",
        highlightthickness=1,
    )
    canvas.pack(fill=tk.BOTH, expand=True)

    legend = ttk.Frame(container)
    legend.pack(fill=tk.X, pady=(8, 0))
    _legend_item(legend, "Underweight", "#DBEAFE").pack(side=tk.LEFT, padx=(0, 12))
    _legend_item(legend, "Normal", "#DCFCE7").pack(side=tk.LEFT, padx=(0, 12))
    _legend_item(legend, "Overweight", "#FFEDD5").pack(side=tk.LEFT, padx=(0, 12))
    _legend_item(legend, "Obese", "#FEE2E2").pack(side=tk.LEFT, padx=(0, 12))
    ttk.Button(legend, text="Close", command=graph_window.destroy).pack(side=tk.RIGHT)

    def draw_chart(_event: tk.Event[tk.Misc] | None = None) -> None:
        canvas.delete("all")
        width = max(canvas.winfo_width(), 620)
        height = max(canvas.winfo_height(), 330)
        left, right, top, bottom = 72, width - 28, 28, height - 70
        plot_width = max(right - left, 1)
        plot_height = max(bottom - top, 1)

        values = [point.bmi for point in points]
        raw_min = min(min(values), 18.5)
        raw_max = max(max(values), 30.0)
        padding = max(2.0, (raw_max - raw_min) * 0.12)
        minimum = max(0.0, raw_min - padding)
        maximum = raw_max + padding
        value_range = max(maximum - minimum, 1.0)

        def y_position(value: float) -> float:
            return bottom - ((value - minimum) / value_range) * plot_height

        bands = (
            (minimum, min(18.5, maximum), "#EFF6FF"),
            (max(18.5, minimum), min(25.0, maximum), "#F0FDF4"),
            (max(25.0, minimum), min(30.0, maximum), "#FFF7ED"),
            (max(30.0, minimum), maximum, "#FEF2F2"),
        )
        for lower, upper, colour in bands:
            if upper > lower:
                canvas.create_rectangle(
                    left,
                    y_position(upper),
                    right,
                    y_position(lower),
                    fill=colour,
                    outline="",
                )

        for index in range(6):
            value = minimum + value_range * index / 5
            y = y_position(value)
            canvas.create_line(left, y, right, y, fill="#E2E8F0")
            canvas.create_text(
                left - 10,
                y,
                text=f"{value:.1f}",
                anchor="e",
                fill="#475569",
                font=("Segoe UI", 9),
            )

        for boundary in (18.5, 25.0, 30.0):
            if minimum <= boundary <= maximum:
                y = y_position(boundary)
                canvas.create_line(
                    left,
                    y,
                    right,
                    y,
                    fill="#64748B",
                    dash=(5, 4),
                    width=1,
                )

        canvas.create_line(left, top, left, bottom, fill="#334155", width=2)
        canvas.create_line(left, bottom, right, bottom, fill="#334155", width=2)
        canvas.create_text(
            18,
            (top + bottom) / 2,
            text="BMI",
            angle=90,
            fill="#0F172A",
            font=("Segoe UI", 10, "bold"),
        )

        if len(points) == 1:
            x_positions = [(left + right) / 2]
        else:
            x_positions = [
                left + plot_width * index / (len(points) - 1)
                for index in range(len(points))
            ]
        y_positions = [y_position(point.bmi) for point in points]

        if len(points) > 1:
            line_coordinates: list[float] = []
            for x, y in zip(x_positions, y_positions):
                line_coordinates.extend((x, y))
            canvas.create_line(
                *line_coordinates,
                fill="#4F46E5",
                width=3,
                smooth=False,
            )

        labelled_indexes = _label_indexes(len(points), maximum_labels=6)
        for index, (point, x, y) in enumerate(zip(points, x_positions, y_positions)):
            canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill="#4F46E5",
                outline="#FFFFFF",
                width=2,
            )
            if len(points) <= 12 or index in labelled_indexes:
                canvas.create_text(
                    x,
                    y - 13,
                    text=f"{point.bmi:.2f}",
                    anchor="s",
                    fill="#312E81",
                    font=("Segoe UI", 9, "bold"),
                )
            if index in labelled_indexes:
                canvas.create_text(
                    x,
                    bottom + 12,
                    text=point.recorded_at.strftime("%d %b\n%Y"),
                    anchor="n",
                    justify=tk.CENTER,
                    fill="#475569",
                    font=("Segoe UI", 8),
                )

        canvas.create_text(
            (left + right) / 2,
            height - 9,
            text="Measurement date",
            anchor="s",
            fill="#0F172A",
            font=("Segoe UI", 10, "bold"),
        )

    canvas.bind("<Configure>", draw_chart)
    graph_window.after_idle(draw_chart)


def _legend_item(parent: ttk.Frame, text: str, colour: str) -> ttk.Frame:
    item = ttk.Frame(parent)
    tk.Label(item, background=colour, width=2, relief="solid", borderwidth=1).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    ttk.Label(item, text=text).pack(side=tk.LEFT)
    return item


def _label_indexes(count: int, maximum_labels: int) -> set[int]:
    if count <= maximum_labels:
        return set(range(count))
    return {
        round(index * (count - 1) / (maximum_labels - 1))
        for index in range(maximum_labels)
    }
