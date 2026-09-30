import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps({"vehicles": [], "next_vehicle_id": 1, "next_service_id": 1}))
    application = create_app(data_file=str(data_file))
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_dashboard_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_api_vehicles_empty(client):
    resp = client.get("/api/vehicles")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_and_view_vehicle(client):
    resp = client.post(
        "/vehicles/add",
        data={
            "make": "Toyota",
            "model": "Corolla",
            "year": "2020",
            "license_plate": "MH12AB1234",
            "owner_name": "Rucha",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Corolla" in resp.data

    api_resp = client.get("/api/vehicles")
    vehicles = api_resp.get_json()
    assert len(vehicles) == 1
    assert vehicles[0]["make"] == "Toyota"


def test_add_service_and_upcoming(client):
    client.post(
        "/vehicles/add",
        data={"make": "Honda", "model": "City", "year": "2019",
              "license_plate": "MH14CD5678", "owner_name": "Rucha"},
    )
    vehicles = client.get("/api/vehicles").get_json()
    vehicle_id = vehicles[0]["id"]

    resp = client.post(
        f"/vehicles/{vehicle_id}/services/add",
        data={
            "service_type": "Oil Change",
            "date": "2026-01-01",
            "cost": "1500",
            "notes": "Routine",
            "next_due_date": "2026-01-15",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Oil Change" in resp.data


def test_delete_vehicle(client):
    client.post(
        "/vehicles/add",
        data={"make": "Ford", "model": "EcoSport", "year": "2018",
              "license_plate": "MH01ZZ0001", "owner_name": "Test"},
    )
    vehicles = client.get("/api/vehicles").get_json()
    vehicle_id = vehicles[0]["id"]

    resp = client.post(f"/vehicles/{vehicle_id}/delete", follow_redirects=True)
    assert resp.status_code == 200

    vehicles_after = client.get("/api/vehicles").get_json()
    assert len(vehicles_after) == 0


def test_vehicle_not_found(client):
    resp = client.get("/vehicles/999")
    assert resp.status_code == 404
