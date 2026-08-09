"""Secure password generation, validation, and strength estimation."""

from __future__ import annotations

import math
import secrets
import string
from typing import Iterable, NamedTuple


MIN_LENGTH = 8
MAX_LENGTH = 128

CHARACTER_SETS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": string.punctuation,
}

AMBIGUOUS_CHARACTERS = frozenset("0O1lI")


class StrengthResult(NamedTuple):
    label: str
    entropy_bits: float
    color: str


def build_character_pools(
    selected_types: Iterable[str], exclude_ambiguous: bool = False
) -> dict[str, str]:
    """Build validated character pools for the selected type names."""
    unique_types = list(dict.fromkeys(selected_types))
    unknown_types = [name for name in unique_types if name not in CHARACTER_SETS]
    if unknown_types:
        raise ValueError(f"Unknown character type: {unknown_types[0]}.")
    if len(unique_types) < 2:
        raise ValueError("Select at least two character types.")

    pools: dict[str, str] = {}
    for name in unique_types:
        pool = CHARACTER_SETS[name]
        if exclude_ambiguous:
            pool = "".join(
                character for character in pool if character not in AMBIGUOUS_CHARACTERS
            )
        if not pool:
            raise ValueError(f"No characters remain in the {name} character type.")
        pools[name] = pool
    return pools


def secure_shuffle(characters: list[str]) -> None:
    """Shuffle a list in place using cryptographically secure randomness."""
    for index in range(len(characters) - 1, 0, -1):
        swap_index = secrets.randbelow(index + 1)
        characters[index], characters[swap_index] = characters[swap_index], characters[index]


def generate_password(
    length: int,
    selected_types: Iterable[str],
    exclude_ambiguous: bool = False,
) -> str:
    """Generate a secure password containing every selected character type."""
    if isinstance(length, bool) or not isinstance(length, int):
        raise ValueError("Password length must be a whole number.")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH} characters."
        )

    pools = build_character_pools(selected_types, exclude_ambiguous)
    if length < len(pools):
        raise ValueError("Password length is too short for the selected character types.")

    characters = [secrets.choice(pool) for pool in pools.values()]
    combined_pool = "".join(pools.values())
    characters.extend(
        secrets.choice(combined_pool) for _ in range(length - len(characters))
    )
    secure_shuffle(characters)
    return "".join(characters)


def estimate_strength(length: int, pools: dict[str, str]) -> StrengthResult:
    """Estimate strength from length and available character diversity."""
    pool_size = sum(len(pool) for pool in pools.values())
    entropy_bits = length * math.log2(pool_size)
    if entropy_bits < 60:
        return StrengthResult("Weak", entropy_bits, "#B91C1C")
    if entropy_bits < 90:
        return StrengthResult("Medium", entropy_bits, "#B45309")
    return StrengthResult("Strong", entropy_bits, "#15803D")
