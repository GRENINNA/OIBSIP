"""Salted password hashing and constant-time verification."""

from __future__ import annotations

import hashlib
import hmac
import os

from .errors import ValidationError


PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
HASH_BYTES = 32


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters.")
    if len(password) > 128:
        raise ValidationError("Password must contain at most 128 characters.")


def hash_password(password: str) -> tuple[bytes, bytes, int]:
    validate_password(password)
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES,
    )
    return salt, digest, PBKDF2_ITERATIONS


def verify_password(
    password: str,
    salt: bytes,
    expected_digest: bytes,
    iterations: int,
) -> bool:
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_digest),
    )
    return hmac.compare_digest(candidate, expected_digest)
