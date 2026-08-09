"""Entry point for the modular Weather App."""

import tkinter as tk

from weather_app.ui import WeatherApp


def main() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Could not start the graphical interface: {error}") from error

    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
