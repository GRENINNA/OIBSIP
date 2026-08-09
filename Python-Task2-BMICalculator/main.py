"""Entry point for the BMI Calculator."""

import tkinter as tk

from bmi_app.ui import BMIApp


def main() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Could not start the graphical interface: {error}") from error

    BMIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
