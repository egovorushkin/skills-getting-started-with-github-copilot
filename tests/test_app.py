from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


TEST_ACTIVITY = "Robotics"
EXISTING_PARTICIPANT = "already-signed-up@example.com"
NEW_PARTICIPANT = "new-student@example.com"


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    activities.clear()
    activities[TEST_ACTIVITY] = {
        "description": "Build and program robots",
        "schedule": "Mondays, 3:30 PM",
        "max_participants": 10,
        "participants": [EXISTING_PARTICIPANT],
    }

    try:
        yield TestClient(app)
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[TEST_ACTIVITY]["participants"] == [EXISTING_PARTICIPANT]


def test_signup_adds_participant(client):
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": NEW_PARTICIPANT},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {NEW_PARTICIPANT} for {TEST_ACTIVITY}"
    }
    assert activities[TEST_ACTIVITY]["participants"] == [
        EXISTING_PARTICIPANT,
        NEW_PARTICIPANT,
    ]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": EXISTING_PARTICIPANT},
    )

    assert response.status_code == 400
    assert activities[TEST_ACTIVITY]["participants"] == [EXISTING_PARTICIPANT]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": NEW_PARTICIPANT},
    )

    assert response.status_code == 404


def test_unregister_removes_participant(client):
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": EXISTING_PARTICIPANT},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_PARTICIPANT} from {TEST_ACTIVITY}"
    }
    assert activities[TEST_ACTIVITY]["participants"] == []


def test_unregister_returns_not_found_for_nonparticipant(client):
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": NEW_PARTICIPANT},
    )

    assert response.status_code == 404
    assert activities[TEST_ACTIVITY]["participants"] == [EXISTING_PARTICIPANT]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": EXISTING_PARTICIPANT},
    )

    assert response.status_code == 404
