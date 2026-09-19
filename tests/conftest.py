import socket

import pytest


@pytest.fixture(autouse=True)
def _offline_suite(monkeypatch):
    """The whole suite must be offline: any socket use is a test bug,
    not an environment quirk (IMPLICIT_SPEC invariant 17)."""

    def _blocked(*_args, **_kwargs):
        raise AssertionError("network access attempted during the offline suite")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)
