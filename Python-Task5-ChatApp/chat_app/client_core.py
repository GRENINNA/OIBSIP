"""Background TCP client that exposes received packets through a queue."""

from __future__ import annotations

import queue
import socket
import threading
from typing import Any

from .errors import ProtocolError
from .protocol import receive_packet, send_packet


class ChatClient:
    """Thread-safe client transport designed for a Tkinter event loop."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5050) -> None:
        self.host = host
        self.port = port
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._socket: socket.socket | None = None
        self._send_lock = threading.Lock()
        self._closed = threading.Event()

    @property
    def connected(self) -> bool:
        return self._socket is not None and not self._closed.is_set()

    def connect(self, timeout: float = 5.0) -> None:
        if self.connected:
            return
        self._closed.clear()
        try:
            sock = socket.create_connection((self.host, self.port), timeout=timeout)
            sock.settimeout(None)
        except OSError as error:
            raise ConnectionError(
                f"Could not connect to {self.host}:{self.port}. Start server.py first."
            ) from error
        self._socket = sock
        threading.Thread(target=self._receive_loop, daemon=True).start()
        self.events.put(
            {
                "type": "connected",
                "message": f"Connected to {self.host}:{self.port}.",
            }
        )

    def send(self, packet: dict[str, Any]) -> None:
        sock = self._socket
        if sock is None or self._closed.is_set():
            raise ConnectionError("The chat client is not connected to the server.")
        try:
            with self._send_lock:
                send_packet(sock, packet)
        except (OSError, ProtocolError) as error:
            self._notify_disconnected("The connection was lost while sending data.")
            raise ConnectionError("The connection was lost.") from error

    def close(self, notify_server: bool = True) -> None:
        sock, self._socket = self._socket, None
        if sock is None:
            self._closed.set()
            return
        if notify_server and not self._closed.is_set():
            try:
                with self._send_lock:
                    send_packet(sock, {"type": "disconnect"})
            except (OSError, ProtocolError):
                pass
        self._closed.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass

    def _receive_loop(self) -> None:
        sock = self._socket
        if sock is None:
            return
        message = "Disconnected from the server."
        try:
            while not self._closed.is_set():
                packet = receive_packet(sock)
                if packet is None:
                    break
                self.events.put(packet)
        except ProtocolError as error:
            message = f"Protocol error: {error}"
        except OSError:
            if not self._closed.is_set():
                message = "The server connection was interrupted."
        finally:
            if not self._closed.is_set():
                self._notify_disconnected(message)

    def _notify_disconnected(self, message: str) -> None:
        if self._closed.is_set():
            return
        self._closed.set()
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        self.events.put({"type": "disconnected", "message": message})
