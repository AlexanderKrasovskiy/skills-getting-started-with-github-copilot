"""
Tests for the Mergington High School activities API.
Uses AAA (Arrange-Act-Assert) testing pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture: Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Fixture: Reset activities to known state before each test."""
    # Store original state with deep copy to prevent state leakage
    from src import app as app_module
    original_activities = copy.deepcopy(app_module.activities)
    
    yield client
    
    # Restore original state after test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_activities))


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, reset_activities):
        """Test that GET /activities returns all available activities."""
        # Arrange
        client = reset_activities
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_includes_participants(self, reset_activities):
        """Test that activity data includes participants list."""
        # Arrange
        client = reset_activities
        
        # Act
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

    def test_get_activities_includes_activity_details(self, reset_activities):
        """Test that activities include all required fields."""
        # Arrange
        client = reset_activities
        
        # Act
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert chess_club["max_participants"] == 12


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, reset_activities):
        """Test that a new participant can successfully sign up."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Signed up" in result["message"]
        assert email in result["message"]

    def test_signup_adds_participant_to_activity(self, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        participants = activities[activity_name]["participants"]
        assert email in participants

    def test_signup_duplicate_email_fails(self, reset_activities):
        """Test that signing up with same email twice returns error."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity_fails(self, reset_activities):
        """Test that signing up for non-existent activity returns 404."""
        # Arrange
        client = reset_activities
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_multiple_different_emails(self, reset_activities):
        """Test that multiple different emails can sign up for same activity."""
        # Arrange
        client = reset_activities
        activity_name = "Basketball Team"  # Has 0 participants initially
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in the activity
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, reset_activities):
        """Test that an existing participant can successfully unregister."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        assert email in result["message"]

    def test_unregister_removes_participant_from_activity(self, reset_activities):
        """Test that unregister actually removes the participant."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/unregister", params={"email": email})
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        participants = activities[activity_name]["participants"]
        assert email not in participants

    def test_unregister_not_signed_up_fails(self, reset_activities):
        """Test that unregistering email not signed up returns 400."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "notsignedupstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]

    def test_unregister_nonexistent_activity_fails(self, reset_activities):
        """Test that unregistering from non-existent activity returns 404."""
        # Arrange
        client = reset_activities
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_then_signup_again(self, reset_activities):
        """Test that after unregister, same email can sign up again."""
        # Arrange
        client = reset_activities
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - First unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act - Then sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        
        # Verify email is back in participants
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email in participants


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
