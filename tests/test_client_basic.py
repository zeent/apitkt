from __future__ import annotations

from apitkt.client import APIClient


def test_client_builds_url_without_double_slash():
    client = APIClient("https://example.com/")
    # This should not raise
    response = client._build_url("/test")
    assert response == "/test"


def test_client_does_not_mutate_base_url():
    client = APIClient("https://example.com/")
    assert client.base_url == "https://example.com"