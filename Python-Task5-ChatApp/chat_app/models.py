"""Small immutable data models shared by server modules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    username: str


@dataclass(frozen=True)
class Room:
    id: int
    name: str
    message_count: int = 0


@dataclass(frozen=True)
class Message:
    id: int
    room_id: int
    username: str
    text: str
    timestamp: str

    def as_packet(self) -> dict[str, object]:
        return {
            "type": "message",
            "id": self.id,
            "room_id": self.room_id,
            "username": self.username,
            "text": self.text,
            "timestamp": self.timestamp,
        }
