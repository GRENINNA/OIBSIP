"""Command-line launcher for the chat server."""

from __future__ import annotations

import argparse
from pathlib import Path

from chat_app.database import DEFAULT_DATABASE_PATH
from chat_app.server_core import ChatServer


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-room chat server.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind")
    parser.add_argument("--port", type=int, default=5050, help="TCP port")
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLite database path",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    server = ChatServer(arguments.host, arguments.port, arguments.database)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping chat server…")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
