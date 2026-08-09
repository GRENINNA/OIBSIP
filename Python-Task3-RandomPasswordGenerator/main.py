"""Entry point for the Secure Password Generator."""

import tkinter as tk

from password_app.ui import PasswordGeneratorApp


def main() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Could not start the graphical interface: {error}") from error

    PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
