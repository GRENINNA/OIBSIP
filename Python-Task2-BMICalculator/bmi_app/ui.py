"""Tkinter interface for the BMI calculator."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from .chart import open_bmi_trend
from .database import DATABASE_PATH, BMIDatabase
from .logic import BMIResult, calculate_bmi


APP_TITLE = "BMI Calculator"


class BMIApp:
    """Coordinate the BMI form, history table, and trend graph."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.database: BMIDatabase | None = None
        self.current_result: BMIResult | None = None

        self.user_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.result_var = tk.StringVar(value="Enter your details, then calculate your BMI.")
        self.status_var = tk.StringVar(value="Ready")

        self._configure_window()
        self._configure_styles()
        self._build_interface()
        self._initialize_database()

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("920x680")
        self.root.minsize(780, 600)
        self.root.configure(bg="#F3F4F6")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#F3F4F6")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure(
            "Title.TLabel",
            background="#F3F4F6",
            foreground="#111827",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#F3F4F6",
            foreground="#4B5563",
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background="#FFFFFF",
            foreground="#111827",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "CardText.TLabel",
            background="#FFFFFF",
            foreground="#374151",
            font=("Segoe UI", 10),
        )
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=22, style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        ttk.Label(container, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Calculate, save, and follow BMI measurements for multiple people.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        self._build_measurement_card(container)
        self._build_history_card(container)
        self._build_footer(container)

        self.root.bind("<Return>", lambda _event: self.calculate())
        self.weight_entry.focus_set()

    def _build_measurement_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        card.columnconfigure(1, weight=1)
        card.columnconfigure(3, weight=1)

        ttk.Label(card, text="New measurement", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )
        ttk.Label(card, text="Name", style="CardText.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.user_box = ttk.Combobox(card, textvariable=self.user_var)
        self.user_box.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=5)
        self.user_box.bind("<<ComboboxSelected>>", self._user_selected)

        ttk.Label(card, text="Weight (kg)", style="CardText.TLabel").grid(
            row=1, column=2, sticky="w", padx=(0, 8), pady=5
        )
        self.weight_entry = ttk.Entry(card, textvariable=self.weight_var)
        self.weight_entry.grid(row=1, column=3, sticky="ew", pady=5)

        ttk.Label(card, text="Height (m)", style="CardText.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.height_entry = ttk.Entry(card, textvariable=self.height_var)
        self.height_entry.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=5)

        ttk.Button(
            card,
            text="Calculate BMI",
            command=self.calculate,
            style="Primary.TButton",
        ).grid(row=2, column=2, sticky="ew", padx=(0, 8), pady=5)
        self.save_button = ttk.Button(card, text="Save record", command=self.save)
        self.save_button.grid(row=2, column=3, sticky="ew", pady=5)

        self.result_label = tk.Label(
            card,
            textvariable=self.result_var,
            bg="#F9FAFB",
            fg="#374151",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            padx=14,
            pady=12,
        )
        self.result_label.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(14, 0))

    def _build_history_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=3, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(2, weight=1)

        heading = ttk.Frame(card, style="Card.TFrame")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Saved history", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(heading, text="Refresh", command=self.refresh_history).grid(
            row=0, column=1, padx=(8, 0)
        )
        self.graph_button = ttk.Button(heading, text="View BMI trend", command=self.show_graph)
        self.graph_button.grid(row=0, column=2, padx=(8, 0))

        ttk.Label(
            card,
            text="Choose or type a name above, then refresh to view that person's records.",
            style="CardText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        table_frame = ttk.Frame(card, style="Card.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("date", "weight", "height", "bmi", "category")
        self.history_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "date": "Recorded",
            "weight": "Weight (kg)",
            "height": "Height (m)",
            "bmi": "BMI",
            "category": "Category",
        }
        widths = {"date": 180, "weight": 105, "height": 105, "bmi": 80, "category": 115}
        for column in columns:
            self.history_table.heading(column, text=headings[column])
            self.history_table.column(
                column,
                width=widths[column],
                minwidth=70,
                anchor="center",
                stretch=True,
            )

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.history_table.yview
        )
        self.history_table.configure(yscrollcommand=scrollbar.set)
        self.history_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_footer(self, container: ttk.Frame) -> None:
        footer = ttk.Frame(container, style="App.TFrame")
        footer.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="BMI is a screening measure, not a medical diagnosis.",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="e")

    def _initialize_database(self) -> None:
        try:
            self.database = BMIDatabase()
            self.refresh_users()
            self.status_var.set(f"History database: {DATABASE_PATH.name}")
        except (sqlite3.Error, OSError) as error:
            self._handle_database_error("initialize the history database", error)
            self.save_button.state(["disabled"])
            self.graph_button.state(["disabled"])

    def _read_inputs(self, require_name: bool = False) -> tuple[str, float, float]:
        name = self.user_var.get().strip()
        if require_name and not name:
            raise ValueError("Enter a name before saving or viewing history.")
        if len(name) > 100:
            raise ValueError("Name must be 100 characters or fewer.")

        weight_text = self.weight_var.get().strip()
        height_text = self.height_var.get().strip()
        if not weight_text or not height_text:
            raise ValueError("Enter both weight in kilograms and height in metres.")
        try:
            weight = float(weight_text)
            height = float(height_text)
        except ValueError as error:
            raise ValueError(
                "Weight and height must be numeric values (for example, 70 and 1.75)."
            ) from error
        return name, weight, height

    def calculate(self) -> BMIResult | None:
        try:
            _name, weight, height = self._read_inputs()
            result = calculate_bmi(weight, height)
        except ValueError as error:
            self.current_result = None
            self.result_var.set("Please correct the entered values.")
            self.result_label.configure(fg="#B91C1C")
            self.status_var.set(str(error))
            messagebox.showerror("Invalid input", str(error), parent=self.root)
            return None

        self.current_result = result
        self._display_result(result)
        self.status_var.set("BMI calculated. Select “Save record” to add it to history.")
        return result

    def save(self) -> None:
        if self.database is None:
            messagebox.showerror(
                "Database unavailable",
                "The history database is unavailable. You can still calculate BMI.",
                parent=self.root,
            )
            return
        try:
            name, weight, height = self._read_inputs(require_name=True)
            result = calculate_bmi(weight, height)
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self.root)
            self.status_var.set(str(error))
            return

        try:
            self.database.save_record(name, weight, height, result)
            self.current_result = result
            self._display_result(result)
            self.refresh_users()
            self.refresh_history()
            self.status_var.set(f"BMI record saved for {name}.")
        except (sqlite3.Error, OSError) as error:
            self._handle_database_error("save the BMI record", error)

    def _display_result(self, result: BMIResult) -> None:
        self.result_var.set(f"BMI: {result.bmi:.2f}  •  {result.category}")
        self.result_label.configure(fg=result.color)

    def refresh_users(self) -> None:
        if self.database is None:
            return
        try:
            current_name = self.user_var.get()
            self.user_box.configure(values=self.database.get_users())
            self.user_var.set(current_name)
        except (sqlite3.Error, OSError) as error:
            self._handle_database_error("load saved users", error)

    def refresh_history(self) -> None:
        for item in self.history_table.get_children():
            self.history_table.delete(item)

        name = self.user_var.get().strip()
        if not name:
            self.status_var.set("Enter or choose a name to view saved history.")
            return
        if self.database is None:
            return
        try:
            records = self.database.get_records(name)
        except (sqlite3.Error, OSError) as error:
            self._handle_database_error("load BMI history", error)
            return

        for record in reversed(records):
            self.history_table.insert(
                "",
                "end",
                values=(
                    self._format_timestamp(record["recorded_at"]),
                    f"{record['weight_kg']:.2f}",
                    f"{record['height_m']:.2f}",
                    f"{record['bmi']:.2f}",
                    record["category"],
                ),
            )
        self.status_var.set(f"{len(records)} saved record(s) found for {name}.")

    def show_graph(self) -> None:
        name = self.user_var.get().strip()
        if not name:
            messagebox.showerror(
                "Name required",
                "Enter or choose a name before opening the trend graph.",
                parent=self.root,
            )
            return
        if self.database is None:
            return
        try:
            records = self.database.get_records(name)
        except (sqlite3.Error, OSError) as error:
            self._handle_database_error("load data for the trend graph", error)
            return
        if not records:
            messagebox.showinfo(
                "No history",
                f"No saved BMI records were found for {name}.",
                parent=self.root,
            )
            return

        try:
            backend = open_bmi_trend(self.root, name, records)
        except (ValueError, tk.TclError) as error:
            messagebox.showerror(
                "Could not open chart",
                str(error),
                parent=self.root,
            )
            self.status_var.set("Could not open the BMI trend chart.")
            return
        self.status_var.set(f"Opened {backend} for {name}.")

    def _user_selected(self, _event: tk.Event[tk.Misc]) -> None:
        self.refresh_history()

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        try:
            return datetime.fromisoformat(timestamp).strftime("%d %b %Y, %H:%M")
        except ValueError:
            return timestamp

    def _handle_database_error(self, action: str, error: Exception) -> None:
        self.status_var.set(f"Database error: could not {action}.")
        messagebox.showerror(
            "Database error",
            f"Could not {action}.\n\nDatabase error: {error}",
            parent=self.root,
        )
