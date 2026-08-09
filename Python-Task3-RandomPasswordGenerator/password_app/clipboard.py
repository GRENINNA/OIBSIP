"""Clipboard integration isolated from the password generator."""


class ClipboardUnavailable(RuntimeError):
    """Raised when pyperclip cannot access a working clipboard."""


def copy_password(text: str) -> None:
    """Copy a password using pyperclip and normalize clipboard errors."""
    if not text:
        raise ClipboardUnavailable("There is no password to copy.")

    try:
        import pyperclip
    except ImportError as error:
        raise ClipboardUnavailable(
            "Pyperclip is not installed. Run: python -m pip install -r requirements.txt"
        ) from error

    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as error:
        raise ClipboardUnavailable(f"The system clipboard is unavailable: {error}") from error
