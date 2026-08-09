"""Threaded TCP chat server with authentication and room broadcasts."""

from __future__ import annotations

import socket
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .database import ChatDatabase, DEFAULT_DATABASE_PATH
from .emoji import replace_shortcodes
from .errors import ChatAppError, ProtocolError, ValidationError
from .models import Room, User
from .protocol import receive_packet, send_packet


@dataclass(eq=False)
class ClientSession:
    sock: socket.socket
    address: tuple[str, int]
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    user: User | None = None
    room_id: int | None = None
    closed: bool = False

    def send(self, packet: dict[str, Any]) -> bool:
        if self.closed:
            return False
        try:
            with self.send_lock:
                send_packet(self.sock, packet)
            return True
        except (OSError, ProtocolError):
            return False


class ChatServer:
    """Accept clients and coordinate authenticated multi-room chat."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5050,
        database_path: Path = DEFAULT_DATABASE_PATH,
    ) -> None:
        self.host = host
        self.port = port
        self.database = ChatDatabase(database_path)
        self._listener: socket.socket | None = None
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._state_lock = threading.RLock()
        self._clients: set[ClientSession] = set()
        self._room_members: dict[int, set[ClientSession]] = defaultdict(set)
        self.startup_error: Exception | None = None

    def serve_forever(self) -> None:
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.host, self.port))
            listener.listen()
            listener.settimeout(1.0)
            self._listener = listener
            self.port = int(listener.getsockname()[1])
            print(f"Chat server listening on {self.host}:{self.port}")
        except Exception as error:
            self.startup_error = error
            self._ready_event.set()
            raise

        self._ready_event.set()
        try:
            while not self._stop_event.is_set():
                try:
                    client_socket, address = listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise
                session = ClientSession(client_socket, (str(address[0]), int(address[1])))
                with self._state_lock:
                    self._clients.add(session)
                threading.Thread(
                    target=self._handle_client,
                    args=(session,),
                    daemon=True,
                ).start()
        finally:
            self.shutdown()

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        return self._ready_event.wait(timeout) and self.startup_error is None

    def shutdown(self) -> None:
        if self._stop_event.is_set() and self._listener is None:
            return
        self._stop_event.set()
        listener, self._listener = self._listener, None
        if listener is not None:
            try:
                listener.close()
            except OSError:
                pass
        with self._state_lock:
            clients = list(self._clients)
        for session in clients:
            session.send(
                {
                    "type": "server_shutdown",
                    "message": "The chat server is shutting down.",
                }
            )
            self._disconnect_session(session)

    def _handle_client(self, session: ClientSession) -> None:
        try:
            while not self._stop_event.is_set():
                packet = receive_packet(session.sock)
                if packet is None:
                    break
                if not self._dispatch(session, packet):
                    break
        except ProtocolError as error:
            session.send({"type": "error", "message": str(error)})
        except OSError:
            pass
        finally:
            self._disconnect_session(session)

    def _dispatch(self, session: ClientSession, packet: dict[str, Any]) -> bool:
        packet_type = str(packet.get("type", ""))
        try:
            if packet_type == "register":
                self._register(session, packet)
            elif packet_type == "login":
                self._login(session, packet)
            elif packet_type == "disconnect":
                return False
            elif session.user is None:
                raise ValidationError("Log in before using chat rooms.")
            elif packet_type == "list_rooms":
                self._send_rooms(session)
            elif packet_type == "create_room":
                self._create_room(session, packet)
            elif packet_type == "join_room":
                self._join_room(session, self._packet_int(packet, "room_id"))
            elif packet_type == "message":
                self._handle_message(session, packet)
            else:
                raise ValidationError("Unknown client request.")
        except ChatAppError as error:
            session.send({"type": "error", "message": str(error)})
        except (TypeError, ValueError):
            session.send({"type": "error", "message": "A request contained invalid data."})
        return True

    def _register(self, session: ClientSession, packet: dict[str, Any]) -> None:
        if session.user is not None:
            raise ValidationError("This connection is already authenticated.")
        user = self.database.register_user(
            str(packet.get("username", "")),
            str(packet.get("password", "")),
        )
        self._finish_authentication(session, user, "Registration successful.")

    def _login(self, session: ClientSession, packet: dict[str, Any]) -> None:
        if session.user is not None:
            raise ValidationError("This connection is already authenticated.")
        user = self.database.authenticate(
            str(packet.get("username", "")),
            str(packet.get("password", "")),
        )
        if user is None:
            session.send(
                {
                    "type": "auth_result",
                    "ok": False,
                    "message": "Incorrect username or password.",
                }
            )
            return
        self._finish_authentication(session, user, "Login successful.")

    def _finish_authentication(
        self, session: ClientSession, user: User, message: str
    ) -> None:
        session.user = user
        session.send(
            {
                "type": "auth_result",
                "ok": True,
                "message": message,
                "username": user.username,
            }
        )
        rooms = self._send_rooms(session)
        lobby = next((room for room in rooms if room.name.casefold() == "lobby"), None)
        if lobby is not None:
            self._join_room(session, lobby.id)

    def _send_rooms(self, session: ClientSession) -> list[Room]:
        rooms = self.database.list_rooms()
        session.send(
            {
                "type": "rooms",
                "rooms": [
                    {
                        "id": room.id,
                        "name": room.name,
                        "message_count": room.message_count,
                    }
                    for room in rooms
                ],
            }
        )
        return rooms

    def _broadcast_room_list(self) -> None:
        with self._state_lock:
            clients = [client for client in self._clients if client.user is not None]
        for client in clients:
            self._send_rooms(client)

    def _create_room(self, session: ClientSession, packet: dict[str, Any]) -> None:
        assert session.user is not None
        room = self.database.create_room(str(packet.get("name", "")), session.user.id)
        self._broadcast_room_list()
        self._join_room(session, room.id)

    def _join_room(self, session: ClientSession, room_id: int) -> None:
        assert session.user is not None
        room = self.database.get_room(room_id)
        old_room_id = session.room_id
        if old_room_id is not None and old_room_id != room_id:
            with self._state_lock:
                self._room_members[old_room_id].discard(session)
            self._broadcast_system(
                old_room_id,
                f"{session.user.username} left the room.",
                exclude=session,
            )

        session.room_id = room.id
        with self._state_lock:
            self._room_members[room.id].add(session)
        history = self.database.get_history(room.id)
        session.send(
            {
                "type": "join_result",
                "ok": True,
                "room": {"id": room.id, "name": room.name},
                "history": [message.as_packet() for message in history],
            }
        )
        if old_room_id != room.id:
            self._broadcast_system(
                room.id,
                f"{session.user.username} joined the room.",
                exclude=session,
            )

    def _handle_message(self, session: ClientSession, packet: dict[str, Any]) -> None:
        assert session.user is not None
        room_id = self._packet_int(packet, "room_id")
        if session.room_id is None or room_id != session.room_id:
            raise ValidationError("Join that room before sending a message.")
        text = replace_shortcodes(str(packet.get("text", "")))
        message = self.database.save_message(room_id, session.user, text)
        self._broadcast(room_id, message.as_packet())
        self._broadcast_room_list()

    def _broadcast_system(
        self,
        room_id: int,
        text: str,
        exclude: ClientSession | None = None,
    ) -> None:
        self._broadcast(
            room_id,
            {
                "type": "system",
                "room_id": room_id,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            exclude=exclude,
        )

    def _broadcast(
        self,
        room_id: int,
        packet: dict[str, Any],
        exclude: ClientSession | None = None,
    ) -> None:
        with self._state_lock:
            recipients = list(self._room_members.get(room_id, set()))
        failed: list[ClientSession] = []
        for recipient in recipients:
            if recipient is exclude:
                continue
            if not recipient.send(packet):
                failed.append(recipient)
        for recipient in failed:
            self._disconnect_session(recipient)

    def _disconnect_session(self, session: ClientSession) -> None:
        with self._state_lock:
            if session.closed:
                return
            session.closed = True
            self._clients.discard(session)
            old_room_id = session.room_id
            if old_room_id is not None:
                self._room_members[old_room_id].discard(session)
            session.room_id = None
        try:
            session.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            session.sock.close()
        except OSError:
            pass
        if (
            old_room_id is not None
            and session.user is not None
            and not self._stop_event.is_set()
        ):
            self._broadcast_system(
                old_room_id,
                f"{session.user.username} disconnected.",
            )

    @staticmethod
    def _packet_int(packet: dict[str, Any], key: str) -> int:
        value = packet.get(key)
        if isinstance(value, bool):
            raise ValueError(key)
        return int(value)
