"""Launcher for the Tkinter chat client."""

from __future__ import annotations

import argparse
import tkinter as tk

from chat_app.client_ui import ChatGUI


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the graphical chat client.")
    parser.add_argument("--host", default="127.0.0.1", help="Chat server host")
    parser.add_argument("--port", type=int, default=5050, help="Chat server port")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Could not start the graphical interface: {error}") from error
    ChatGUI(root, arguments.host, arguments.port)
    root.mainloop()


if __name__ == "__main__":
    main()
