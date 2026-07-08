"""Secure password generation for pgman-created database owners."""

import secrets
import string

# Character set: uppercase + lowercase letters and digits (no symbols, per spec).
_ALPHABET = string.ascii_letters + string.digits

# Inclusive length bounds for generated passwords.
_MIN_LENGTH = 13
_MAX_LENGTH = 17


def generate_password() -> str:
    """Return a cryptographically secure random password.

    The password is between 13 and 17 characters (inclusive), composed of
    upper- and lower-case ASCII letters and digits.
    """
    length = secrets.choice(range(_MIN_LENGTH, _MAX_LENGTH + 1))
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
