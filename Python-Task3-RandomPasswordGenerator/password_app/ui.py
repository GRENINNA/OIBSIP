"""Tkinter interface for the secure password generator."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .clipboard import ClipboardUnavailable, copy_password
from .generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    StrengthResult,
    build_character_pools,
    estimate_strength,
    generate_password,
)
from .history import SessionHistory


APP_TITLE = "Secure Password Generator"


class PasswordGeneratorApp:
    """Coordinate password controls, results, clipboard, and session history."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.history = SessionHistory()
        self.clipboard_warning_shown = False

        self.length_var = tk.StringVar(value="16")
        self.uppercase_var = tk.BooleanVar(value=True)
        self.lowercase_var = tk.BooleanVar(value=True)
        self.numbers_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=False)
        self.exclude_ambiguous_var = tk.BooleanVar(value=True)
        self.password_var = tk.StringVar()
        self.strength_var = tk.StringVar(value="Strength: generate a password to check")
        self.status_var = tk.StringVar(value="Choose your settings and generate a password.")

        self._configure_window()
        self._configure_styles()
        self._build_interface()

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("860x700")
        self.root.minsize(720, 620)
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
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#FFFFFF",
            background="#4F46E5",
        )
        style.map("Primary.TButton", background=[("active", "#4338CA")])
        for label, color in (
            ("Weak", "#DC2626"),
            ("Medium", "#D97706"),
            ("Strong", "#16A34A"),
        ):
            style.configure(
                f"{label}.Horizontal.TProgressbar",
                background=color,
                troughcolor="#E5E7EB",
            )

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=22, style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(container, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Create strong passwords with cryptographically secure randomness.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        self._build_settings_card(container)
        self._build_result_card(container)
        self._build_history_card(container)
        self._build_footer(container)

        self.root.bind("<Return>", lambda _event: self.generate())
        self.root.bind("<Control-g>", lambda _event: self.generate())
        self.length_spinbox.focus_set()

    def _build_settings_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        for column in range(1, 4):
            card.columnconfigure(column, weight=1)

        ttk.Label(card, text="Password settings", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )
        ttk.Label(card, text="Length", style="CardText.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 10)
        )
        self.length_spinbox = ttk.Spinbox(
            card,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            increment=1,
            width=8,
            textvariable=self.length_var,
        )
        self.length_spinbox.grid(row=1, column=1, sticky="w", pady=(0, 10))
        ttk.Label(
            card,
            text=f"Minimum {MIN_LENGTH}, maximum {MAX_LENGTH} characters",
            style="CardText.TLabel",
        ).grid(row=1, column=2, columnspan=2, sticky="e", pady=(0, 10))

        ttk.Checkbutton(card, text="Uppercase (A–Z)", variable=self.uppercase_var).grid(
            row=2, column=0, sticky="w", pady=4
        )
        ttk.Checkbutton(card, text="Lowercase (a–z)", variable=self.lowercase_var).grid(
            row=2, column=1, sticky="w", pady=4
        )
        ttk.Checkbutton(card, text="Numbers (0–9)", variable=self.numbers_var).grid(
            row=2, column=2, sticky="w", pady=4
        )
        ttk.Checkbutton(card, text="Symbols (!@#…)", variable=self.symbols_var).grid(
            row=2, column=3, sticky="w", pady=4
        )
        ttk.Checkbutton(
            card,
            text="Exclude ambiguous characters (0, O, 1, l, I)",
            variable=self.exclude_ambiguous_var,
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))

    def _build_result_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Generated password", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )
        self.password_entry = tk.Entry(
            card,
            textvariable=self.password_var,
            state="readonly",
            readonlybackground="#F9FAFB",
            fg="#111827",
            relief="solid",
            borderwidth=1,
            font=("Consolas", 15, "bold"),
        )
        self.password_entry.grid(row=1, column=0, columnspan=3, sticky="ew", ipady=10)

        self.strength_bar = ttk.Progressbar(
            card,
            mode="determinate",
            maximum=120,
            value=0,
            style="Weak.Horizontal.TProgressbar",
        )
        self.strength_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 6))
        self.strength_label = tk.Label(
            card,
            textvariable=self.strength_var,
            bg="#FFFFFF",
            fg="#4B5563",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.strength_label.grid(row=3, column=0, columnspan=3, sticky="w")

        ttk.Button(
            card,
            text="Generate password",
            command=self.generate,
            style="Primary.TButton",
        ).grid(row=4, column=0, sticky="ew", pady=(14, 0), padx=(0, 8))
        self.copy_button = ttk.Button(card, text="Copy to Clipboard", command=self.copy_current)
        self.copy_button.grid(row=4, column=1, sticky="ew", pady=(14, 0), padx=(0, 8))
        ttk.Button(card, text="Clear result", command=self.clear_result).grid(
            row=4, column=2, sticky="ew", pady=(14, 0)
        )
        self.copy_button.state(["disabled"])

    def _build_history_card(self, container: ttk.Frame) -> None:
        card = ttk.Frame(container, padding=18, style="Card.TFrame")
        card.grid(row=4, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(2, weight=1)

        heading = ttk.Frame(card, style="Card.TFrame")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Session history — last 5", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(heading, text="Copy selected", command=self.copy_selected).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(heading, text="Clear history", command=self.clear_history).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Label(
            card,
            text="Kept only in memory and erased when this application closes.",
            style="CardText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.history_list = tk.Listbox(
            card,
            height=5,
            font=("Consolas", 11),
            bg="#F9FAFB",
            fg="#111827",
            selectbackground="#C7D2FE",
            selectforeground="#111827",
            exportselection=False,
            relief="solid",
            borderwidth=1,
        )
        self.history_list.grid(row=2, column=0, sticky="nsew")
        self.history_list.bind("<Double-Button-1>", lambda _event: self.copy_selected())

    def _build_footer(self, container: ttk.Frame) -> None:
        footer = ttk.Frame(container, style="App.TFrame")
        footer.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="Clipboard contents may be readable by other applications.",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="e")

    def _selected_types(self) -> list[str]:
        selections = {
            "uppercase": self.uppercase_var.get(),
            "lowercase": self.lowercase_var.get(),
            "numbers": self.numbers_var.get(),
            "symbols": self.symbols_var.get(),
        }
        return [name for name, enabled in selections.items() if enabled]

    def _read_length(self) -> int:
        try:
            return int(self.length_var.get().strip())
        except ValueError as error:
            raise ValueError("Password length must be a whole number.") from error

    def generate(self) -> None:
        try:
            length = self._read_length()
            selected_types = self._selected_types()
            exclude_ambiguous = self.exclude_ambiguous_var.get()
            pools = build_character_pools(selected_types, exclude_ambiguous)
            password = generate_password(length, selected_types, exclude_ambiguous)
        except ValueError as error:
            self.status_var.set(str(error))
            messagebox.showerror("Invalid settings", str(error), parent=self.root)
            return

        self.password_var.set(password)
        self.copy_button.state(["!disabled"])
        self.history.add(password)
        self._refresh_history()
        self._show_strength(estimate_strength(length, pools))
        if self._copy(password, automatic=True):
            self.status_var.set("Secure password generated and copied to the clipboard.")
        else:
            self.status_var.set("Password generated, but automatic clipboard copy was unavailable.")

    def copy_current(self) -> None:
        if self._copy(self.password_var.get()):
            self.status_var.set("Password copied to the clipboard.")

    def copy_selected(self) -> None:
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showinfo(
                "Select a password",
                "Select a password from the session history first.",
                parent=self.root,
            )
            return
        if self._copy(str(self.history_list.get(selection[0]))):
            self.status_var.set("Selected history password copied to the clipboard.")

    def _copy(self, password: str, automatic: bool = False) -> bool:
        try:
            copy_password(password)
            return True
        except ClipboardUnavailable as error:
            self.status_var.set(str(error))
            if not automatic or not self.clipboard_warning_shown:
                messagebox.showwarning("Clipboard unavailable", str(error), parent=self.root)
                self.clipboard_warning_shown = True
            return False

    def _show_strength(self, strength: StrengthResult) -> None:
        self.strength_var.set(
            f"Strength: {strength.label}  •  approximately {strength.entropy_bits:.0f} bits"
        )
        self.strength_label.configure(fg=strength.color)
        self.strength_bar.configure(
            value=min(strength.entropy_bits, 120),
            style=f"{strength.label}.Horizontal.TProgressbar",
        )

    def _refresh_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for password in self.history.entries:
            self.history_list.insert(tk.END, password)

    def clear_result(self) -> None:
        self.password_var.set("")
        self.strength_var.set("Strength: generate a password to check")
        self.strength_label.configure(fg="#4B5563")
        self.strength_bar.configure(value=0, style="Weak.Horizontal.TProgressbar")
        self.copy_button.state(["disabled"])
        self.status_var.set("Generated result cleared. Session history is unchanged.")

    def clear_history(self) -> None:
        self.history.clear()
        self._refresh_history()
        self.status_var.set("Session history cleared.")
