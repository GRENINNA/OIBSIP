"""Server-side conversion of common emoji shortcodes."""

import re


EMOJI_SHORTCODES = {
    ":smile:": "😄",
    ":laugh:": "😂",
    ":heart:": "❤️",
    ":thumbs_up:": "👍",
    ":wave:": "👋",
    ":fire:": "🔥",
    ":cry:": "😢",
    ":angry:": "😠",
    ":party:": "🎉",
    ":rocket:": "🚀",
    ":check:": "✅",
    ":coffee:": "☕",
}

SHORTCODE_PATTERN = re.compile(r":[a-z0-9_+-]+:")


def replace_shortcodes(text: str) -> str:
    return SHORTCODE_PATTERN.sub(
        lambda match: EMOJI_SHORTCODES.get(match.group(0), match.group(0)),
        text,
    )
