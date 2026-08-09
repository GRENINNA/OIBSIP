"""Shared chat application errors."""


class ChatAppError(RuntimeError):
    """Base error whose message is safe to show to a user."""


class ValidationError(ChatAppError):
    """Input did not meet an application rule."""


class AlreadyExistsError(ChatAppError):
    """A unique username or room name is already taken."""


class NotFoundError(ChatAppError):
    """A requested room or record does not exist."""


class ProtocolError(ChatAppError):
    """A network packet was malformed or too large."""
