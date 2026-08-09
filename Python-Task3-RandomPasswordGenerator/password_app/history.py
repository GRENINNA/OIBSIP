"""Non-persistent session history for generated passwords."""

from collections import deque


HISTORY_LIMIT = 5


class SessionHistory:
    """Keep a fixed number of passwords in memory, newest first."""

    def __init__(self, limit: int = HISTORY_LIMIT) -> None:
        if limit < 1:
            raise ValueError("History limit must be at least 1.")
        self._entries: deque[str] = deque(maxlen=limit)

    def add(self, password: str) -> None:
        self._entries.appendleft(password)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def entries(self) -> tuple[str, ...]:
        return tuple(self._entries)
