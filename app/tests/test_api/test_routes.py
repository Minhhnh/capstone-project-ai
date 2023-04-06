"""Unittest for api"""
from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

with open("app/tests/example_data/img2img.json", 'r', encoding='utf-8') as f:
    img2img_request: dict[str, Any] = json.load(f)
with open("app/tests/example_data/clip.json", 'r', encoding='utf-8') as f:
    clip_request: dict[str, Any] = json.load(f)


def test_img2img():
    """
    It sends a POST request to the `/api/img2img` endpoint with the `img2img_request` object as the body
    of the request

    Authored by minhhnh
    """
    response = client.post("/api/img2img", json=img2img_request)
    assert response.status_code == 200


def test_clip():
    """
    It sends a POST request to the `/api/clip` endpoint with the `clip_request` data, and asserts that
    the response status code is 200

    Authored by minhhnh
    """
    response = client.post("/api/clip", json=clip_request)
    assert response.status_code == 200
