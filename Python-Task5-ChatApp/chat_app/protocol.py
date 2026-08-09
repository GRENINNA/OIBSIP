"""Length-prefixed UTF-8 JSON protocol used by client and server."""

from __future__ import annotations

import json
import socket
import struct
from typing import Any

from .errors import ProtocolError


HEADER_SIZE = 4
MAX_PACKET_SIZE = 1_048_576


def _receive_exact(sock: socket.socket, byte_count: int) -> bytes | None:
    data = bytearray()
    while len(data) < byte_count:
        chunk = sock.recv(byte_count - len(data))
        if not chunk:
            if not data:
                return None
            raise ProtocolError("The connection closed during a network packet.")
        data.extend(chunk)
    return bytes(data)


def send_packet(sock: socket.socket, payload: dict[str, Any]) -> None:
    """Serialize and send one complete packet."""
    try:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ProtocolError("A packet contained data that could not be encoded.") from error
    if len(body) > MAX_PACKET_SIZE:
        raise ProtocolError("The network packet was too large.")
    sock.sendall(struct.pack("!I", len(body)) + body)


def receive_packet(sock: socket.socket) -> dict[str, Any] | None:
    """Receive one packet, returning None after a clean disconnect."""
    header = _receive_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    if length < 2 or length > MAX_PACKET_SIZE:
        raise ProtocolError("Received an invalid network packet length.")
    body = _receive_exact(sock, length)
    if body is None:
        raise ProtocolError("The connection closed before a packet was complete.")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("Received a malformed JSON packet.") from error
    if not isinstance(payload, dict):
        raise ProtocolError("Every network packet must be a JSON object.")
    return payload
