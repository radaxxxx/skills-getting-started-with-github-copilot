import copy
import pytest
from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore participant lists after each test to prevent cross-test pollution."""
    original = {name: copy.deepcopy(details) for name, details in activities.items()}
    yield
    activities.clear()
    activities.update(original)


# --- GET / ---

def test_root_redirects_to_index():
    # Arrange - client is module-level, no extra setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"].endswith("/static/index.html")


# --- GET /activities ---

def test_get_activities_returns_all():
    # Arrange - 9 activities pre-loaded in app state

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 9


def test_get_activities_have_expected_fields():
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    for activity in response.json().values():
        assert expected_fields.issubset(activity.keys())


# --- POST /activities/{activity_name}/signup ---

def test_signup_success():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_signup_adds_participant_to_list():
    # Arrange
    activity_name = "Math Olympiad"
    email = "newmath@mergington.edu"
    count_before = len(activities[activity_name]["participants"])

    # Act
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert len(activities[activity_name]["participants"]) == count_before + 1
    assert email in activities[activity_name]["participants"]


def test_signup_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_existing_participant_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # pre-seeded participant

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()
