import asyncio
from unittest.mock import AsyncMock

from app.config import settings
from app.services.web_socket_manager import ConnectionManager


def test_public_demo_rejects_unauthenticated_writes(client, monkeypatch):
    monkeypatch.setattr(settings, "sensor_api_key", "test-only-key")
    response = client.post("/observations", json={})
    assert response.status_code == 401
    assert client.get("/tracks").status_code == 200


def test_production_ingestion_fails_closed_without_key(client, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "sensor_api_key", "")
    assert client.post("/observations", json={}).status_code == 503


def test_authorized_ingestion_persists_and_broadcasts(client, monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(settings, "sensor_api_key", "test-only-key")
    with client.websocket_connect("/ws/tracks") as ws:
        response = client.post("/observations", headers={"X-Sensor-Key": "test-only-key"}, json={
            "sensor_id": "DEMO", "source_track_id": "DEMO-1",
            "latitude": 34.92, "longitude": -80.91, "altitude": 12000,
            "heading": 90, "speed": 180, "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        assert response.status_code == 200
        event = ws.receive_json()
        assert event["event"] == "track_updated"
        assert event["track_id"] == response.json()["track_id"]
        assert client.get(f'/observations/{event["track_id"]}/latest').json()["id"] == response.json()["id"]


def test_disconnected_viewer_does_not_break_ingestion_or_other_viewers():
    manager = ConnectionManager()
    gone = AsyncMock()
    gone.send_json.side_effect = RuntimeError("socket closed")
    active = AsyncMock()
    manager.active_connections = [gone, active]
    asyncio.run(manager.broadcast({"event": "track_updated"}))
    assert manager.active_connections == [active]
    active.send_json.assert_awaited_once()
    manager.disconnect(gone)
