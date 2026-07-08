"""Tests for pgman.passwords."""

import re

from pgman.passwords import generate_password


def test_length_within_bounds():
    for _ in range(200):
        pw = generate_password()
        assert 13 <= len(pw) <= 17


def test_only_alphanumeric():
    pattern = re.compile(r"^[A-Za-z0-9]+$")
    for _ in range(200):
        pw = generate_password()
        assert pattern.match(pw), pw


def test_reasonably_unique():
    passwords = {generate_password() for _ in range(100)}
    # Collisions are astronomically unlikely; expect all distinct.
    assert len(passwords) == 100


def test_uses_secrets_module(monkeypatch):
    import pgman.passwords as passwords_mod

    calls = {"choice": 0}
    real_choice = passwords_mod.secrets.choice

    def counting_choice(seq):
        calls["choice"] += 1
        return real_choice(seq)

    monkeypatch.setattr(passwords_mod.secrets, "choice", counting_choice)
    pw = generate_password()
    # One choice for the length + one per character.
    assert calls["choice"] == len(pw) + 1
